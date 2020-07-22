import time
from time import localtime
from time import sleep
from time import time
import socket, sys
import math

#Lat/Long defaults for simulation
time = " "
long = 3811.366
long_heading = 'N'
lat = "08325.56"
lat_heading = 'W'

class nmeaFrame:
	def __init__(self):
		self.header = "GPGGA"
		self.time = ''
		self.latitude = ''
		self.latHemi = "N"
		self.longitude = ''
		self.longHemi = "W"
		self.fix = 0
		self.sats = 0
		self.hdop = 0
		self.altitude = 0
		self.geoid = -32.00
		self.distanceUnits = 'M'
		self.ageRTK = '01'
		self.correctionID = '0000'
	def generateNMEA(self):
		#Generate timestamp for current frame
		self.timestruct = localtime()
		self.time = (str(self.timestruct.tm_hour).zfill(2) + str(self.timestruct.tm_min).zfill(2) + str(self.timestruct.tm_sec).zfill(2) + ".3")		
		
		#Generate NMEA string		
		self.gga_string = (self.header + "," + str(self.time) + "," + self.latitude + "," + self.latHemi + "," + self.longitude + "," + self.longHemi + "," + str(self.fix) + "," + str(self.sats) + "," + "0.9" + "," + str(self.altitude) + "," + self.distanceUnits + "," + "-32.00" + "," + self.distanceUnits + "," + self.ageRTK + "," + self.correctionID)

		#Calculate and append checksum
		self.checksum = 0
		for x in self.gga_string:
			self.checksum = self.checksum ^ ord(x)
		self.gga_string = ("$" + self.gga_string + "*" + str(format(self.checksum, 'X')))
		#print(self.gga_string)
		return(self.gga_string)

def simulateNMEA():
	time_struct = localtime()	#Populate time struct
	global long
	global lat
	long += 0.1
	time_string = (str(time_struct.tm_hour) + str(time_struct.tm_min) + str(time_struct.tm_sec) + ".3") 
	gga_string = ("GPGGA," + str(time_string) + "," + str(long) + "," + long_heading + "," + lat + "," + lat_heading + ",1,4,3.3,2.0,M,,,,")
	checksum = 0
	for x in gga_string:
		checksum = checksum ^ ord(x)

	gga_string = ("$" + gga_string + "*" + str(format(checksum, 'X')))
	return gga_string

def printSimNMEA(rate):
	while(True):
		simulateNMEA()
		sleep(1)

#example string
# $GPGGA,101623.3,13828.13,E,3510.78,S,1,4,3.3,2.0,M,,,,*2A

#print(gps2BC.generateNMEA())

TCP_IP = '0.0.0.0'		#Uses default system interface IP
TCP_PORT = 10110		#This is default port for BC's
BUFFER_SIZE = 1024

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
s.listen(1)


def connMan():
	print("Waiting on connection...")
	addr = None	
	while not addr:
		conn, addr = s.accept()
	print('Connection address:', addr)
	return conn

def sendData(data, conn):
	print("Sending: " + data)
	conn.send(bytes((data + "\x0d\x0a"), encoding='utf8'))	#BC expects \r\n to terminate string

#################################################################################
#	Main TCP loop (executed in separate program thread). Operates at 1Hz	#
#################################################################################
def mainTCPLoop(nmea_string):
	while 1:
		conn = connMan()	#Wait until we're connected
		try:
			while 1:
				#data = conn.recv(BUFFER_SIZE)
		    		#if data:
				#	print "received data:", data	    	
				#data = conn.recv(BUFFER_SIZE)
				sendData(nmea_string.get(), conn)
				sleep(1)
		except KeyboardInterrupt:
			conn.close()
			exit()    		
		except Exception as e: print(e)
			
	conn.close()

#################################################################################################
#	Converts the values provided by dronekit to ones usable by the NMEA string generator	#					
#################################################################################################
def convertFrameNMEA(navFrame, nmea_class):
	nmea_class.time = localtime()
	
	#Format Latitude (convert from deg.decimal to degmin.decimal)
	latRaw = 0
	if navFrame['latitude'] > 0:
		nmea_class.latHemi = 'N'
		latRaw = (navFrame['latitude'])
	else:
		nmea_class.latHemi = 'S'
		latRaw = (navFrame['latitude']) * -1
	latDec, latDeg = math.modf(latRaw)	#Split degrees and decimal
	latSec, latMin  = math.modf(latDec*60)	#Split Mins and Sec
	latSec = round(latSec, 7)
	
	
	#Format lat string
	latStr = ""
	latStr += (str(int(latDeg)).zfill(2)) #Add degrees. Add padding if number is <10
	latStr += (str(int(latMin)).zfill(2))	#add minutes. Add padding if <10
	latStr += "."
	latStr += str(int(round(latSec, 7) * 10000000)).zfill(7)
	#print ("Latitude: ", latStr)
	nmea_class.latitude = latStr
	
	#Format Longitude  (convert from deg.decimal to degmin.decimal)	
	longRaw = 0
	if navFrame['longitude'] > 0:
		nmea_class.longHemi = 'E'
		longRaw = (navFrame['longitude'])
	else:
		nmea_class.longHemi = 'W' 	
		longRaw = (navFrame['longitude']) * -1
	longDec, longDeg  = math.modf(longRaw)		#Split degrees and decimal
	longSec, longMin  = math.modf(longDec*60)	#Split Mins and Sec
	longSec = round(longSec, 7)
	
	#Format long string	
	longStr = ""
	longStr += (str(int(longDeg)).zfill(3)) #Add degrees. Add padding if number is <10
	longStr += (str(int(longMin)).zfill(2))	#add minutes. Add padding if <10
	longStr += "."
	longStr += str(int(round(longSec, 7) * 10000000)).zfill(7)
	#print ("Longitude: ", longStr)
	nmea_class.longitude = longStr


	nmea_class.fix = navFrame['gps_fix']
	nmea_class.altitude = navFrame['altitude']
	nmea_class.sats = navFrame['gps_sats']
	#print("NMEA Frame: ", nmeaFrame)
	#print("---------------------------------")

#########################################
#	Collect dronekit GPS data 	#
#########################################
def grabFrameNav(vehicle):
	navFrame = {
		'latitude' : vehicle.location.global_frame.lat,
		'longitude' : vehicle.location.global_frame.lon,
		'gps_fix' : vehicle.gps_0.fix_type,
		'gps_sats' : vehicle.gps_0.satellites_visible,
		'gps_hdop' : vehicle.gps_0.eph,
		'gps_vdop' : vehicle.gps_0.epv,
		'altitude' : vehicle.location.global_frame.alt
	}
	
	#DroneKit will populate feilds with 'None' to start.
	#NMEA strings don't like 'None' for a feild. Set to 0 until populated	
	for key, value in navFrame.items():
		if value is None:
			navFrame[key] = 0
	return navFrame


