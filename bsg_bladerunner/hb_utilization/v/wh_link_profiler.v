`include "bsg_defines.v"
`include "bsg_manycore_defines.vh"

module wh_link_profiler
  import bsg_noc_pkg::*;
  import bsg_manycore_pkg::*;
  #(parameter `BSG_INV_PARAM(num_pods_y_p)
    , `BSG_INV_PARAM(num_pods_x_p)
    ,`BSG_INV_PARAM(num_vcache_rows_p)
    , `BSG_INV_PARAM(wh_ruche_factor_p)
    , `BSG_INV_PARAM(wh_flit_width_p)
    , `BSG_INV_PARAM(data_width_p)
    , localparam wh_link_sif_width_lp =
      `bsg_ready_and_link_sif_width(wh_flit_width_p)

  )
  (
    input clk_i
    
    , input [num_pods_y_p-1:0][num_pods_x_p-1:0] reset_lo
    , input [E:W][num_pods_y_p-1:0][S:N][num_vcache_rows_p-1:0][wh_ruche_factor_p-1:0][wh_link_sif_width_lp-1:0] wh_link_sif_i
    , input [E:W][num_pods_y_p-1:0][S:N][num_vcache_rows_p-1:0][wh_ruche_factor_p-1:0][wh_link_sif_width_lp-1:0] wh_link_sif_o

    , input [31:0] global_ctr_i
    , input print_stat_v_i
    , input [data_width_p-1:0] print_stat_tag_i
  );


  `declare_bsg_ready_and_link_sif_s(wh_flit_width_p, wh_link_sif_s);
  wh_link_sif_s [E:W][num_pods_y_p-1:0][S:N][wh_ruche_factor_p-1:0] wh_link_sif_in, wh_link_sif_out;
  always_comb begin
    for (integer i = W; i <= E; i++) begin
      for (integer y = 0; y < num_pods_y_p; y++) begin
        for (integer j = N; j <= S; j++) begin
          for (integer rf = 0; rf < wh_ruche_factor_p; rf++) begin
            if (rf == 0) begin
              wh_link_sif_in[i][y][j][rf] = wh_link_sif_i[i][y][j][0][rf];
              wh_link_sif_out[i][y][j][rf] = wh_link_sif_o[i][y][j][0][rf];
            end
            else begin
              wh_link_sif_in[i][y][j][rf] = ~wh_link_sif_i[i][y][j][0][rf];
              wh_link_sif_out[i][y][j][rf] = ~wh_link_sif_o[i][y][j][0][rf];
            end
          end
        end
      end
    end
  end

  wire reset = |reset_lo;
  


  typedef struct packed {
    integer stall;
    integer idle;
  } wh_stat_s;


  wh_stat_s [E:W][num_pods_y_p-1:0][S:N][wh_ruche_factor_p-1:0] input_stat_r, output_stat_r;

  always_ff @ (posedge clk_i) begin
    if (reset) begin
      input_stat_r <= '0;   
      output_stat_r <= '0;
    end
    else begin

      for (integer i = W; i <= E; i++) begin
        for (integer y = 0; y < num_pods_y_p; y++) begin
          for (integer j = N; j <= S; j++) begin
            for (integer rf = 0; rf < wh_ruche_factor_p; rf++) begin
              // input
              if (wh_link_sif_in[i][y][j][rf].v == 1'b0) begin
                // idle
                input_stat_r[i][y][j][rf].idle++;
              end                 
              else begin
                if (wh_link_sif_out[i][y][j][rf].ready_and_rev == 1'b0) begin
                  // stall
                  input_stat_r[i][y][j][rf].stall++;
                end
              end
        
              // output
              if (wh_link_sif_out[i][y][j][rf].v == 1'b0) begin
                // idle
                output_stat_r[i][y][j][rf].idle++;
              end                 
              else begin
                if (wh_link_sif_in[i][y][j][rf].ready_and_rev == 1'b0) begin
                  // stall
                  output_stat_r[i][y][j][rf].stall++;
                end
              end

              
            end
          end
        end
      end

    end
  end

  // Stat Printing
  // format: global_ctr,tag,{E|W},{pod_y},{S|N},{rf},{in|out},stall,idle
  integer fd;
  initial begin
    fd = $fopen("wh_link_stat.csv", "w");
    $fwrite(fd, "global_ctr,tag,EW,pod_y,SN,rf,inout,stall,idle\n");
    $fflush(fd);
  end

  always_ff @ (posedge clk_i) begin
    if (print_stat_v_i) begin
 
     for (integer i = W; i <= E; i++) begin
        for (integer y = 0; y < num_pods_y_p; y++) begin
          for (integer j = N; j <= S; j++) begin
            for (integer rf = 0; rf < wh_ruche_factor_p; rf++) begin
              $fwrite(fd, "%0d,%0d,%0d,%0d,%0d,%0d,in,%0d,%0d\n",
                global_ctr_i, print_stat_tag_i,
                i, y, j, rf,
                input_stat_r[i][y][j][rf].stall,
                input_stat_r[i][y][j][rf].idle
              );

              $fwrite(fd, "%0d,%0d,%0d,%0d,%0d,%0d,out,%0d,%0d\n",
                global_ctr_i, print_stat_tag_i,
                i, y, j, rf,
                output_stat_r[i][y][j][rf].stall,
                output_stat_r[i][y][j][rf].idle
              );
            end
          end
        end
      end

    end
  end

  final begin
    $fclose(fd);
  end

endmodule

`BSG_ABSTRACT_MODULE(wh_link_profiler)


  bind bsg_manycore_pod_ruche_array wh_link_profiler  #(
    .num_pods_y_p(num_pods_y_p)
    ,.num_pods_x_p(num_pods_x_p)
    ,.num_vcache_rows_p(num_vcache_rows_p)
    ,.wh_ruche_factor_p(wh_ruche_factor_p)
    ,.wh_flit_width_p(wh_flit_width_p)
    ,.data_width_p(data_width_p)
  ) wh0 (
    .*
    ,.global_ctr_i($root.`HOST_MODULE_PATH.global_ctr)
    ,.print_stat_v_i($root.`HOST_MODULE_PATH.print_stat_v)
    ,.print_stat_tag_i($root.`HOST_MODULE_PATH.print_stat_tag)
  );

