from PIL import Image, ImageDraw
import math

TILE_SIDE  = 90
TILE_PITCH = 100
TILE_X_DIM = 16
TILE_Y_DIM = 10
TILE_MARGIN = (TILE_PITCH-TILE_SIDE)

PORT_SIDE = 12

def draw_port(imgdraw, x, y, output_dir, pct):
  img_x = x
  img_y = y+1
  tile_x = (img_x*TILE_PITCH) + TILE_MARGIN
  tile_y = (img_y*TILE_PITCH) + TILE_MARGIN
  
  # calculate fill color
  fill_color = (255, math.floor((100-pct)/100*255), math.floor((100-pct)/100*255))
  
  # calculate shape
  if output_dir == "P":
    xmin = tile_x + (TILE_SIDE/2) - (PORT_SIDE/2)
    ymin = tile_y + (TILE_SIDE/2) - (PORT_SIDE/2)
  elif output_dir == "W":
    xmin = tile_x
    ymin = tile_y + (TILE_SIDE/2) - (PORT_SIDE/2)
  elif output_dir == "E":
    xmin = tile_x + (TILE_SIDE) - (PORT_SIDE)
    ymin = tile_y + (TILE_SIDE/2) - (PORT_SIDE/2)
  elif output_dir == "N":
    xmin = tile_x + (TILE_SIDE/2) - (PORT_SIDE/2)
    ymin = tile_y
  elif output_dir == "S":
    xmin = tile_x + (TILE_SIDE/2) - (PORT_SIDE/2)
    ymin = tile_y + TILE_SIDE - PORT_SIDE
  elif output_dir == "RW":
    xmin = tile_x
    ymin = tile_y
  elif output_dir == "RE":
    xmin = tile_x + (TILE_SIDE) - (PORT_SIDE)
    ymin = tile_y

  xmax = xmin + PORT_SIDE
  ymax = ymin + PORT_SIDE
  shape = [(xmin,ymin),(xmax,ymax)]

  imgdraw.rectangle(shape, fill=fill_color, outline="black")
  
def visualize_router_traffic(diff_df, stat, image_name):
  img = Image.new("RGB", (TILE_PITCH*TILE_X_DIM,TILE_PITCH*TILE_Y_DIM), (0,0,0))
  
  imgdraw = ImageDraw.Draw(img)
  
  # draw tile outline
  for y in range(TILE_Y_DIM):
    for x in range(TILE_X_DIM):
      xmin = (x*TILE_PITCH) + TILE_MARGIN
      ymin = (y*TILE_PITCH) + TILE_MARGIN
      xmax = xmin + TILE_SIDE
      ymax = ymin + TILE_SIDE
      shape = [(xmin,ymin),(xmax,ymax)]
      imgdraw.rectangle(shape, fill="#aaaaaa", outline="black")


  # draw tile ports
  for idx, row in diff_df.iterrows():
    x = row["x"]
    y = row["y"]
    output_dir = row["output_dir"]
    pct = row[stat]
    draw_port(imgdraw, x, y, output_dir, pct)

  # show image
  #img.show()

  # save image
  img.save(image_name)
