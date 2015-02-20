# Desc: Device definitions for Braiten, a very simple robot as described in Braitenberg's Vehicles.
# Author: Stefano Franchi
# Date: 09 December 2009


# The Braiten sonar array (two sensors in front)
define BraitenSonar sensor
(
# define the size of each transducer [xsize ysize zsize] in meters
  size [0.01 0.05 0.1]
  # define the range [range_min range_max]
  range [0 10.0]
  # and field of view  [degrees]
  fov 30
  # define the number of samples spread over the fov
  samples 1
  # define the color that ranges are drawn in the gui (now green)
  color_rgba [ 0 1 0 0.2 ] 
)

define Braiten_sonars ranger
# the two front sensors
(
 # define the type and pose of each transducer [xpos ypos zpos heading]
  BraitenSonar ( pose [ 0.73 -0.13 0.10 -5 ])
  BraitenSonar ( pose [ 0.73  0.13 0.10 5 ])
)

#Define the fiducial finders used to simulate light sensors
#
# TO DO
#

# A basic Braitenberg vehicle spatial configuration (its body)
define Braiten position
(
  # actual size in meters [xsize ysize zsize]
  size [1 0.604 0.250]

  # Braiten's center of rotation is horizontally offset from the geometrical center of its shape
  # to make it fall exactly between the wheels
  origin [0.23 0.0 0 0]

  # draw a nose on the robot so we can see which way it points
  gui_nose 1

  # estimated mass in KG
  mass 10

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
  # use the sonar array defined above
  Braiten_sonars()  
  
  # use my picture instead of polygons
  # bitmap "images/Braiten.png"
) 










