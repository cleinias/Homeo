# Desc:     Device definitions for Khepera, a very simple circular robot 
#           with two "eyes" (fiducial sensors).
# Author:   Stefano Franchi
# Date:     06 February 2014

# The fiducial finders used to simulate light sensors
#
# The two sensors are positioned on the edge of the robot with a 60 deg angle
# between them with respect to the bisecant of the robot, i.e. each one is 30 degrees
# right (res.,left) from the line bisecting the robot along the north-south axis
# The sensor are oriented the x axis (they point straight forward).
# Each sensor is 8mm from the robot's top.
# The size of each sensor is 1 cubic mm

define rightEye fiducial
(
    size [ 0.001 0.001 0.001 ]
    pose [ 0.06062 0.035 0.050 0]  # Pose from the center of the robot, height is 8mm from the top (0.058m)
    range_max 10
    range_max_id 10 
    fov 60   # field of view in degrees
#    fov 360
    ignore_zloc 1
    name "rightEye"
    # define the color that ranges are drawn in the gui (now blue)
    color_rgba [ 0.0 0.0 1.0 1.0 ]
)

define leftEye fiducial
(
    size [  0.001 0.001 0.001 ]
    pose [ 0.06062 -0.035 0.050 0 ] # Pose from the center of the robot, height is 8mm from the top (0.058m)
    range_max 10
    range_max_id 10 
    fov 60   # field of view in degrees
#    fov 360
    ignore_zloc 1
    name "leftEye"
    # define the color that ranges are drawn in the gui (now blue)
    color_rgba [ 0.0 0.0 1.0 1.0 ]
)

# A basic Khepera vehicle spatial configuration (its body)
# Appr. size is taken from Khepera 4 specs and rendered as a circle (cylinder)
# Diameter: 140mm Height: 58 mm Clearance 4 mm
# Turn Radius 0 cm Weight 540 gr.

define Khepera position
(
  #Khepera is a cylinder: stage will draw it from the bitmap of a circle
  bitmap "images/circle.png"

  # actual size in meters [xsize ysize zsize]
  size [0.14 0.14 0.058]

  # Khepera is a cylinder, so its center of rotation will fall in its center, as it shoul d
  origin [0 0.0 0 0]

  # draw a nose on the robot so we can see which way it points
  gui_nose 1

  # estimated mass in KG (from Khepera 4 specs)
  mass 0.540

  # Khepera has a differential steering model
  drive "diff"
  
  # Add the two "eyes" (fiducial finders) defined above
  rightEye()
  leftEye()  
) 










