from xml.dom import minidom
import urllib.request
import math
import os
import re
import fileinput

def acforsale():
	# Aircraft name, ICAO code, max price, max hours
	print("Finding aircraft for sale...")
	goodones=(("Pilatus PC-12","PC12",800000,50),
			("Beechcraft 1900D","BE19",1150000,50),
			("Bombardier Challenger 300","CL30",850000,50),
			("Ilyushin Il-14","IL14",1410000,50),
			("Alenia C-27J Spartan","C27J",3500000,200),
			("Alenia C-27J Spartan (IRIS)","C27J",3500000,200),
			("Lockheed C-130 (Generic)","C130",4500000,500),
			("Lockheed C-130 (Capt Sim)","C130",4500000,500),
			("Bombardier Dash-8 Q400","DH8D",8000000,500),
			("Dassault Falcon 7X","FA7X",1500000,10000),
			("Fairchild C123","C123",5000000,10000),
			("Douglas C117D","C117",5000000,10000),
			("Cessna Citation X","C750",1200000,10000))
	mykey = "CHANGEME"
	print("Sending request...")
	data = urllib.request.urlopen('http://server.fseconomy.net/data?userkey='+mykey+'&format=xml&query=aircraft&search=forsale')
	print("Got data")
	xmldoc = minidom.parse(data)
	airplanes = xmldoc.getElementsByTagName("Aircraft")
	for airplane in airplanes:
		actype = airplane.getElementsByTagName("MakeModel")[0].firstChild.nodeValue

		aframetime = airplane.getElementsByTagName("AirframeTime")[0].firstChild.nodeValue
		hours = int(aframetime.split(":")[0])
		price = float(airplane.getElementsByTagName("SalePrice")[0].firstChild.nodeValue)
		for option in goodones:
			if actype==option[0] and hours<option[3] and price<option[2]:
				loc = airplane.getElementsByTagName("Location")[0].firstChild.nodeValue
				locname = airplane.getElementsByTagName("LocationName")[0].firstChild.nodeValue
				print(option[1]+" | "+aframetime+" | $"+locale.format("%d", price, grouping=True)+" | "+loc+" | "+locname)
	print("Finished looking for planes")

def jobsfrom(apts):
	#Airports to watch
	#apts="SPIM-SPJJ-SEGU-SEQU-SPZO-SPQU-SPJN-SPGM-SPOL-SETA-SPEO-SKBO-SKGB-SKCL-MPTO-MPHO"
	#High paying jobs from airports
	data = urllib.request.urlopen('http://server.fseconomy.net/data?userkey='+mykey+'&format=xml&query=icao&search=jobsfrom&icaos='+apts).read()
	xmldoc = minidom.parse(data)
	jobs = getElementsByTagName("Assignment")
	for assignment in assignments:
		pay = float(assignment.getElementsByTagName("Pay")[0])
		if pay>5000:
			dep = assignment.getElementsByTagName("FromIcao")[0]
			arr = assignment.getElementsByTagName("ToIcao")[0]
			loc = assignment.getElementsByTagName("Location")[0]
			amt = assignment.getElementsByTagName("Amount")[0]
			typ = assignment.getElementsByTagName("UnitType")[0]
			exp = assignment.getElementsByTagName("Expires")[0]
			if dep==loc:
				print (amt+" "+typ+" "+dep+"-"+arr+" $"+str(int(pay))+" "+exp)
			else:
				print (amt+" "+typ+" @"+dep+"-"+arr+" $"+str(int(pay))+" "+exp)

def jobsto(apts):
	#High paying jobs to airports
	data = urllib.request.urlopen('http://server.fseconomy.net/data?userkey='+mykey+'&format=xml&query=icao&search=jobsto&icaos='+apts).read()
	xmldoc = minidom.parse(data)
	jobs = getElementsByTagName("Assignment")
	for assignment in assignments:
		pay = float(assignment.getElementsByTagName("Pay")[0])
		if pay>10000:
			dep = assignment.getElementsByTagName("FromIcao")[0]
			arr = assignment.getElementsByTagName("ToIcao")[0]
			loc = assignment.getElementsByTagName("Location")[0]
			amt = assignment.getElementsByTagName("Amount")[0]
			typ = assignment.getElementsByTagName("UnitType")[0]
			exp = assignment.getElementsByTagName("Expires")[0]
			if not(int(amt)<33 and typ=="passengers"):
				if dep==loc:
					print (amt+" "+typ+" "+dep+"-"+arr+" $"+str(int(pay))+" "+exp)
				else:
					print (amt+" "+typ+" @"+dep+"-"+arr+" $"+str(int(pay))+" "+exp)


def findjobs(apt):
	apts="KSEA"
	dir=90
	data = urllib.request.urlopen('http://server.fseconomy.net/data?userkey='+mykey+'&format=xml&query=icao&search=jobsfrom&icaos='+apts).read()
	xmldoc = minidom.parse(data)
	jobs = getElementsByTagName("Assignment")
	for assignment in assignments:
		pay = float(assignment.getElementsByTagName("Pay")[0])
		if pay>5000:
			dep = assignment.getElementsByTagName("FromIcao")[0]
			arr = assignment.getElementsByTagName("ToIcao")[0]
			loc = assignment.getElementsByTagName("Location")[0]
			amt = assignment.getElementsByTagName("Amount")[0]
			typ = assignment.getElementsByTagName("UnitType")[0]
			exp = assignment.getElementsByTagName("Expires")[0]
			if dep==loc:
				print (amt+" "+typ+" "+dep+"-"+arr+" $"+str(int(pay))+" "+exp)
			else:
				print (amt+" "+typ+" @"+dep+"-"+arr+" $"+str(int(pay))+" "+exp)
			
def haverdist(lat1, lon1, lat2, lon2):
	#http://www.movable-type.co.uk/scripts/latlong.html
	R = 6371000; # metres
	phi1 = math.radians(lat1)
	phi2 = math.radians(lat2)
	delphi = math.radians(lat2-lat1)
	dellamb = math.radians(lon2-lon1)
	a = math.sin(delphi/2) * math.sin(delphi/2) + math.cos(phi1) * math.cos(phi2) * math.sin(dellamb/2) * math.sin(dellamb/2)
	c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
	d = R * c * 3.2808399 / 6076 # m to ft to Nm
	return d

def cosinedist(lat1, lon1, lat2, lon2):
	phi1 = math.radians(lat1)
	phi2 = math.radians(lat2)
	dellamb = math.radians(lon2-lon1)
	R = 6371000
	# gives d in metres
	d = math.acos( math.sin(phi1)*math.sin(phi2) + math.cos(phi1)*math.cos(phi2) * math.cos(dellamb) ) * R * 3.2808399 / 6076 # m to ft to Nm
	return d

def inithdg(lat1, lon1, lat2, lon2):
	phi1 = math.radians(lat1)
	phi2 = math.radians(lat2)
	lamb1 = math.radians(lon1)
	lamb2 = math.radians(lon2)
	y = math.sin(lamb2-lamb1) * math.cos(phi2)
	x = math.cos(phi1)*math.sin(phi2) - math.sin(phi1)*math.cos(phi2)*math.cos(lamb2-lamb1)
	brng = math.degrees(math.atan2(y, x))
	if brng<0:
		brng+=360
	return brng

def get_dest_info(icao): #Get info about destination
	found=0
	# r'\b[01] [01] '+dest+r'\b'
	# r'^1(6?|7?)\s+\d{1,5}\s+[01]\s+[01]\s+'+dest+r'\b'
	regex=re.compile(r'^1(6?|7?)\s.*?'+icao+r'\b').search
	dir1='/mnt/data/XPLANE10/X-Plane10/Resources/default scenery/default apt dat/Earth nav data/apt.dat'
	dir2='/mnt/data/XPLANE10/X-Plane10/Custom Scenery/zzzz_FSE_Airports/Earth nav data/apt.dat'
	for line in fileinput.input([dir1,dir2]): # I am forever indebted to Padraic Cunningham for this code
		if found==1:
			params=line.split()
			if int(params[0])==100:
				lat=float(params[9])
				lon=float(params[10])
				break
		if regex(line):
			found=1
	else:
		print(icao+" not found, giving up")
		lat=0
		lon=0
	fileinput.close()
	return (lat, lon)

print("Running main")
pos=get_dest_info("KORD")
print("KORD returns "+str(pos[0])+" "+str(pos[1]))
lat=pos[0]
lon=pos[1]
pos=get_dest_info("KSEA")
print("KSEA returns "+str(pos[0])+" "+str(pos[1]))
lat2=pos[0]
lon2=pos[1]
hdist=haverdist(lat,lon,lat2,lon2)
cdist=cosinedist(lat,lon,lat2,lon2)
hdg=inithdg(lat,lon,lat2,lon2)
print("Haverdist: "+str(int(round(hdist)))+"  Cdist: "+str(int(round(cdist)))+"  Hdg: "+str(int(round(hdg))))
