from dronekit import connect, VehicleMode
import dronekit_sitl
import gps2BC

#gps2BC specific libraries
from time import sleep
from time import localtime
import math
from multiprocessing import Queue
import threading

sitl = dronekit_sitl.start_default()
connection_string = sitl.connection_string()

vehicle = connect(connection_string, wait_ready = True)



#Main Entry Point
nmea_class = gps2BC.nmeaFrame()		#instantiate nmeaFrame class
q = Queue()	#The queue used to communicate between main and auxiliary thread
thread = threading.Thread(target=gps2BC.mainTCPLoop, args=(q, ))
thread.start()

while 1:
	gps2BC.convertFrameNMEA(gps2BC.grabFrameNav(vehicle), nmea_class)	#Gather dronekit GPS data and convert it into the nmeaFrame class
	q.put(nmea_class.generateNMEA())			#Generate final NMEA string from nmeaFrame class and pop onto queue
	sleep(1)
vehicle.close()
sitl.stop()

