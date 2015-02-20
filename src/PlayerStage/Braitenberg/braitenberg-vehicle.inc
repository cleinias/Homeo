# Desc: Device definitions for Braiten, a very simple robot as described in Braitenberg's Vehicles.
#       With two fiducial finders to simulate "eyes"
# Author: Stefano Franchi
# Date: 26 January 2011



#Define the fiducial finders used to simulate light sensors
#
# IN PROGRESS
#
define BraitenRightEye  fiducial
(
    size [ 0.01 0.05 0.1 ] # x-size y-size z-size
    pose [ 0.73 -0.13 0.10 -5 ] # xpos ypos zpos angle
    range_max 10
    range_max_id 10 
    fov 2 #in radians
    ignore_zloc 1
    name "rightEye"
    # define the color that ranges are drawn in the gui (now  blue)
    color_rgba [ 0 0 1.0 1.0 ]
)
  
define BraitenLeftEye  fiducial
(
    size [ 0.01 0.05 0.1 ]
    pose [ 0.73  0.13 0.10 5 ]
    range_max 10
    range_max_id 10 
    fov 360 #in radians
    ignore_zloc 1
    name "leftEye"
    # define the color that ranges are drawn in the gui (now blue)
    color_rgba [ 0.0 0.0 1.0 1.0 ]
  )



# A basic Braitenberg vehicle spatial configuration (its body)
define Braiten position
(
  # actual size in meters [xsize ysize zsize]
#  size [1 0.604 0.250]
  size [0.1 0.0604 0.0250]  # a tenth (1/10)
  # Braiten's center of rotation is horizontally offset from the geometrical center of its shape
  # to make it fall exactly between the wheels
#  origin [0.23 0 0 0]
  origin [0.023 0 0 0]
  # draw a nose on the robot so we can see which way it points
  gui_nose 1

  # estimated mass in KG
#  mass 10
   mass 1
  # differential steering model
  drive "diff"

#   these 5 rectangles approximate the shape of a Braitenberg vehicle, 
#   instead of letting stage draw the shape from the bitmap file
#   Need to declare points anti-clockwise!
#   Need also to position blocks vertically in the model with z [height_from height_to]

#   # main body (rectangular)
block
(
  points 4
  point[0] [  0  15 ]
  point[1] [  0  230 ]
  point[2] [ 355 230]
  point[3] [ 355  15 ]
  z [ 0 0.25]
)

   
#   # right wheel (rectangular)
block
(
  points 4
  point[0] [60 0]
  point[1] [160 0]
  point[2] [160 15]
  point[3] [60 15]
  z [ 0 0.15]
)

#   
#   # left wheel (rectangular)
block
(
  points 4
  point[0] [60 230]
  point[1] [160 230]
  point[2] [160 245]
  point[3] [60 245]
  z [ 0 0.15]
)

#   
#   #right sensor (rectangular)
block
(
  points 4
  point[0] [355 160]
  point[1] [405 160]
  point[2] [405 190]
  point[3] [355 190]
  z [ .15 0.25]
)

#   
#   #left sensor (rectangular)
block
(
  points 4
  point[0] [355 55]
  point[1] [405 55]
  point[2] [405 85]
  point[3] [355 85]
  z [ .15 0.25]
)                      

# use the fiducial finders defined above
 BraitenRightEye()
 BraitenLeftEye()

# use my picture instead of polygons
 #  bitmap "images/Braiten.png"
#) 


# unclear what these three last instructions do
#   fiducial_return 1
#   localization "gps"
#   localization_origin [ 0 0 0 ]
 )







