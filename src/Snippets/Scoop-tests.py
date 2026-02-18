from __future__ import print_function
from scoop import futures
from datetime import datetime
from time import sleep

def helloWorld(value):
    sleep(0.01)
    return "Hello World from Future #{0}".format(value)

if __name__ == "__main__":
    startTime = datetime.now()
    returnValues = list(futures.map(helloWorld, range(16)))
#     returnValues = list(map(helloWorld, range(16000)))
    print("\n".join(returnValues))
    print("Elapsed time = ",datetime.now() - startTime)