# Vector_Add 通過但 PageRank 失敗的原因分析

## 觀察到的現象

### Vector_Add: ✅ PASS
- 簡單的浮點加法操作
- 測試通過，結果正確

### PageRank: ❌ FAIL
- 使用內聯彙編的浮點指令 (fmadd.s, fadd.s, fdiv.s)
- **關鍵線索：HammerBlade 的結果約為 CPU 結果的 2 倍**
  ```
  [3902] contrib_new: hb=0.014752, cpu=0.007378  (0.014752 ≈ 2× 0.007378)
  [3925] contrib_new: hb=0.013113, cpu=0.006558  (0.013113 ≈ 2× 0.006558)
  [4036] contrib_new: hb=0.006242, cpu=0.003121  (0.006242 ≈ 2× 0.003121)
  ```
- SSE 測試：`sse0=0.000448` (閾值), `sse1=0.003260` (實際) → FAIL

---

## 根本原因：FP Pipeline 在單發射模式下被錯誤執行

### 問題 1: FP Pipeline 的條件判斷不完整

**位置**: `vanilla_core.sv` line ~1980

```systemverilog
if (flush | stall_id | ~id_r.decode1.is_fp_op) begin
  // 清除 FP pipeline
  fp_exe_ctrl_n.fp_decode.is_fpu_float_op = 1'b0;
  fp_exe_ctrl_n.fp_decode.is_fpu_int_op   = 1'b0;
  ...
end else begin
  fp_exe_ctrl_en = 1'b1;  // ⚠️ FP pipeline 被執行！
  fp_exe_data_en = 1'b1;
end
```

**問題**: 
- 檢查了 `~id_r.decode1.is_fp_op`（slot 1 不是 FP 指令）- **但沒有檢查是否真正進行了雙發射！**- 即使在單發射模式下，slot 1 都有可能包含有效的 FP 指令資訊（從 PC+1 解碼而來但不應執行）

### 問題 2: ID Stage 的指令分流邏輯

**位置**: `vanilla_core.sv` line 260-351

單發射模式下的分流邏輯：
```systemverilog
else begin  // 單發射模式
  if (decode0.is_fp_op) begin
    fp_instr_n = instr0;          // FP 指令放入 FP pipeline
    fp_decode_general_n = decode0;
  end else begin
    int_instr_n = instr0;         // INT 指令放入 INT pipeline
    int_decode_n = decode0;
    // fp_instr_n 保持為 '0 (初始化值)
  end
}
```

**然後在 line 1504-1511**，這些值被填充到 `id_n` 結構體：
```systemverilog
id_n = '{
  instruction: int_instr_n,       // Slot 0 (INT pipeline)
  decode: int_decode_n,
  
  instruction1: fp_instr_n,       // Slot 1 (FP pipeline) ⚠️
  decode1: fp_decode_general_n,   // ⚠️
  fp_decode1: fp_fp_decode_n,     // ⚠️
  ...
};
```

### 問題 3: 缺少雙發射狀態的記錄

當前 `safe_dual_issue` 只在 PC 更新時使用，但沒有被記錄到 pipeline register 中。FP pipeline 無法知道上一個週期是否真正進行了雙發射。

---

## 為什麼 Vector_Add 通過但 PageRank 失敗？

### 假說：指令序列和緩存命中的時序差異

1. **Vector_Add**: 
   - 連續的浮點加法指令
   - 可能因為 icache miss 或其他 stall 條件，大部分時間不滿足 `safe_dual_issue` 的條件
   - FP pipeline 較少被意外觸發

2. **PageRank**:
   - 大量內聯彙編浮點指令（fmadd, fadd）
   - 更高的指令密度和更穩定的執行流
   - 更頻繁地滿足 `safe_dual_issue` 中除了 `can_issue_dual` 之外的條件
   - **導致 FP pipeline 頻繁被執行，即使實際上是單發射**

---

## 修復方案

### 方案 1: 在 FP Pipeline 入口檢查真實的雙發射狀態 ⭐ 推薦

修改 `vanilla_core.sv` line ~1975-1991：

```systemverilog
// 需要一個 register 記錄上一個週期的雙發射狀態
logic dual_issue_id_r;  // 添加到聲明區

always_ff @(posedge clk_i) begin
  if (reset_i)
    dual_issue_id_r <= 1'b0;
  else if (~stall_all)
    dual_issue_id_r <= can_issue_dual & id_issue & icache_v_i & ~icache_miss ...;
end

// 修改 FP pipeline 的條件
always_comb begin
  ...
  if (flush | stall_id | ~id_r.decode1.is_fp_op | ~dual_issue_id_r) begin  // ⬅️ 添加檢查
    // 清除 FP pipeline
    fp_exe_ctrl_n.fp_decode.is_fpu_float_op = 1'b0;
    ...
  end else begin
    fp_exe_ctrl_en = 1'b1;
    fp_exe_data_en = 1'b1;
  end
end
```

### 方案 2: 在 ID Stage 就清零 decode1

在單發射模式下，強制將 `fp_decode_general_n` 的所有執行標誌位清零：

```systemverilog
else begin  // 單發射模式
  ...
  // 確保 FP pipeline 的 decode 信號完全清零
  fp_decode_general_n = '0;  // 顯式清零
}
```

---

## 驗證步驟

1. 實施修復後，重新運行 pagerank 測試
2. 檢查結果是否不再加倍（hb ≈ cpu，而不是 hb ≈ 2×cpu）
3. 確保 vector_add 和其他測試仍然通過
4. 檢查 debug 輸出確認 FP pipeline 只在真正雙發射時執行

---

## 結論

**核心問題**：FP pipeline 在單發射模式下被錯誤執行，導致浮點運算結果加倍。

**直接證據**：PageRank 的 HammerBlade 結果 ≈ 2× CPU 結果

**修復關鍵**：確保 FP pipeline 只在真正的雙發射週期才執行。
