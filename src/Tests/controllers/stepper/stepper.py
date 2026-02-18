"Test controller for exploring stepping capabilities in Webots"


from controller import *

class Robbie(DifferentialWheels):
    def run(self):
        while True:
            curTime = self.getTime()
            print "Time is: ", curTime
            self.step(3200)
            

robbie = Robbie()            
robbie.run()
