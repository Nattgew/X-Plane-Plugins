from xlm.dom import minidom
import urllib
import math

def acforsale():
	# Aircraft name, ICAO code, max price, max hours
	goodones=(("Pilatus PC-12","PC12",800000,100),
			("Beechcraft 1900D","BE19",1150000,100),
			("Bombardier Challenger 300","CL30",850000,100),
			("Ilyushin Il-14","IL14",1410000,100),
			("Alenia C-27J Spartan","C27J",3500000,100),
			("Alenia C-27J Spartan (IRIS)","C27J",3500000,100),
			("Lockheed C-130 (Generic)","C130",4500000,500),
			("Lockheed C-130 (Capt Sim)","C130",4500000,500),
			("Bombardier Dash-8 Q400","DH8D",8000000,500),
			("Dassault Falcon 7X","FA7X",4000000,10000),
			("Fairchild C123","C123",5000000,10000),
			("Douglas C117D","C117",5000000,10000),
			("Cessna Citation X","C750",1000000,10000))
	mykey = "CHANGEME"
	data = urllib.urlopen('http://server.fseconomy.net/data?userkey='+mykey+'&format=xml&query=aircraft&search=forsale').read()
	xmldoc = minidom.parse(data)
	airplanes = xmldom.getElementsByTagName("Aircraft")
	for airplane in airplanes:
		type = airplane.getElementsByTagName("MakeModel")[0]
		aframetime = airplane.getElementsByTagName("AirframeTime")[0]
		hours = int(aframetime.split(":")[0])
		price = float(airplane.getElementsByTagName("SalePrice")[0])
		for option in goodones:
			if type==option[0] and hours<option[3] and price<option[2]:
				loc = airplane.getElementsByTagName("Location")[0]
				locname = airplane.getElementsByTagName("LocationName")[0]
				print(option[1]+" | "+aframetime+" | "+str(int(price))+" | "+loc+" | "+locname)
def jobsfrom():
	#Airports to watch
	apts="SPIM-SPJJ-SEGU-SEQU-SPZO-SPQU-SPJN-SPGM-SPOL-SETA-SPEO-SKBO-SKGB-SKCL-MPTO-MPHO"
	#High paying jobs from airports
	data = urllib.urlopen('http://server.fseconomy.net/data?userkey='+mykey+'&format=xml&query=icao&search=jobsfrom&icaos='+apts).read()
	xmldoc = minidom.parse(data)
	jobs = xmldom.getElementsByTagName("Assignment")
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

def jobsto():
	#High paying jobs to airports
	data = urllib.urlopen('http://server.fseconomy.net/data?userkey='+mykey+'&format=xml&query=icao&search=jobsto&icaos='+apts).read()
	xmldoc = minidom.parse(data)
	jobs = xmldom.getElementsByTagName("Assignment")
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
				

apts="KSEA"
dir=90
data = urllib.urlopen('http://server.fseconomy.net/data?userkey='+mykey+'&format=xml&query=icao&search=jobsfrom&icaos='+apts).read()
xmldoc = minidom.parse(data)
jobs = xmldom.getElementsByTagName("Assignment")
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
			
def haverdist(lat1, lat2):
	#http://www.movable-type.co.uk/scripts/latlong.html
	R = 6371000; # metres
	phi1 = math.radians(lat1)
	phi2 = math.radians(lat2)
	delphi = math.radians(lat2-lat1)
	dellamb = math.radians(lon2-lon1)
	a = math.sin(delphi/2) * math.sin(delphi/2) + math.cos(phi1) * math.cos(phi2) * math.sin(dellamb/2) * math.sin(dellamb/2)
	c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
	d = R * c
	return d

def cosinedist(lat1, lat2):
	phi1 = math.radians(lat1)
	phi2 = math.radians(lat2)
	dellamb = math.radians(lon2-lon1)
	R = 6371000
	# gives d in metres
	d = math.acos( math.sin(phi1)*math.sin(phi2) + math.cos(phi1)*math.cos(phi2) * math.cos(dellamb) ) * R
	return d

def inithdg(lat1, lat2):
	y = math.sin(lamb2-lamb1) * math.cos(phi2)
	x = math.cos(phi1)*math.sin(phi2) - math.sin(phi1)*math.cos(phi2)*math.cos(lamb2-lamb1)
	brng = math.degrees(math.atan2(y, x))
	return brng
