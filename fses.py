from xml.dom import minidom
import urllib.request
import math
import os
import re
import fileinput
import csv

def acforsale():
	# Aircraft name, ICAO code, max price, max hours
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
	print("Sending request for sales listing...")
	data = urllib.request.urlopen('http://server.fseconomy.net/data?userkey='+mykey+'&format=xml&query=aircraft&search=forsale')
	print("Parsing data...")
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
				dist=distbwt("SPJJ",loc,loc_dict)
				print(option[1]+" | "+aframetime+" | $"+locale.format("%d", price, grouping=True)+" | "+loc+" | "+str(dist)+" | "+locname)

def jobsfrom(apts,price,pax):
	#High paying jobs from airports
	jobs=[]
	print("Sending request for jobs from "+apts+"...")
	data = urllib.request.urlopen('http://server.fseconomy.net/data?userkey='+mykey+'&format=xml&query=icao&search=jobsfrom&icaos='+apts).read()
	print("Parsing response...")
	xmldoc = minidom.parse(data)
	assignments = xmldoc.getElementsByTagName("Assignment")
	for assignment in assignments:
		pay = float(assignment.getElementsByTagName("Pay")[0].firstChild.nodeValue)
		if pay>price:
			dep = assignment.getElementsByTagName("FromIcao")[0].firstChild.nodeValue
			arr = assignment.getElementsByTagName("ToIcao")[0].firstChild.nodeValue
			loc = assignment.getElementsByTagName("Location")[0].firstChild.nodeValue
			amt = assignment.getElementsByTagName("Amount")[0].firstChild.nodeValue
			typ = assignment.getElementsByTagName("UnitType")[0].firstChild.nodeValue
			exp = assignment.getElementsByTagName("Expires")[0].firstChild.nodeValue
			if not(int(amt)<pax+1 and typ=="passengers"):
				jobs.append((loc,arr,amt,typ,pay))
				# if dep==loc:
					# print(amt+" "+typ+" "+dep+"-"+arr+" $"+str(int(pay))+" "+exp)
				# else:
					# print(amt+" "+typ+" @"+dep+"-"+arr+" $"+str(int(pay))+" "+exp)
	return jobs

def jobsto(apts,price,pax):
	#High paying jobs to airports
	jobs=[]
	print("Sending request for jobs to "+apts+"...")
	data = urllib.request.urlopen('http://server.fseconomy.net/data?userkey='+mykey+'&format=xml&query=icao&search=jobsto&icaos='+apts).read()
	print("Parsing response...")
	xmldoc = minidom.parse(data)
	assignments = xmldoc.getElementsByTagName("Assignment")
	for assignment in assignments:
		pay = float(assignment.getElementsByTagName("Pay")[0].firstChild.nodeValue)
		if pay>price:
			dep = assignment.getElementsByTagName("FromIcao")[0].firstChild.nodeValue
			arr = assignment.getElementsByTagName("ToIcao")[0].firstChild.nodeValue
			loc = assignment.getElementsByTagName("Location")[0].firstChild.nodeValue
			amt = assignment.getElementsByTagName("Amount")[0].firstChild.nodeValue
			typ = assignment.getElementsByTagName("UnitType")[0].firstChild.nodeValue
			exp = assignment.getElementsByTagName("Expires")[0].firstChild.nodeValue
			if not(int(amt)<pax+1 and typ=="passengers"):
				jobs.append((loc,arr,amt,typ,pay,exp))
				#if dep==loc:
				#	print (amt+" "+typ+" "+dep+"-"+arr+" $"+str(int(pay))+" "+exp)
				#else:
				#	print (amt+" "+typ+" @"+loc+"-"+arr+" $"+str(int(pay))+" "+exp)
	return jobs

def printjobs(jobs):
	for job in jobs:
		print(job[2]+" "+job[3]+" "+job[0]+"-"+job[1]+" $"+str(int(job[4]))+" "+job[5])

def haverdist(lat1,lon1,lat2,lon2):
	#http://www.movable-type.co.uk/scripts/latlong.html
	R = 6371000; # metres
	phi1 = math.radians(lat1)
	phi2 = math.radians(lat2)
	delphi = math.radians(lat2-lat1)
	dellamb = math.radians(lon2-lon1)
	a = math.sin(delphi/2) * math.sin(delphi/2) + math.cos(phi1) * math.cos(phi2) * math.sin(dellamb/2) * math.sin(dellamb/2)
	c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
	d = R * c * 3.2808399 / 6076 # m to ft to Nm
	return int(round(d))

def cosinedist(lat1,lon1,lat2,lon2):
	phi1 = math.radians(lat1)
	phi2 = math.radians(lat2)
	dellamb = math.radians(lon2-lon1)
	R = 6371000
	# gives d in metres
	d = math.acos( math.sin(phi1)*math.sin(phi2) + math.cos(phi1)*math.cos(phi2) * math.cos(dellamb) ) * R * 3.2808399 / 6076 # m to ft to Nm
	return int(round(d))

def inithdg(lat1,lon1,lat2,lon2):
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

def dirbwt(icaofrom,icaoto):
	lat1,lon1=loc_dict['icaofrom']
	lat2,lon2=loc_dict['icaoto']
	hdg=inithdg(lat1,lon1,lat2,lon2)
	return hdg

def distbwt(icaofrom,icaoto):
	lat1,lon1=loc_dict['icaofrom']
	lat2,lon2=loc_dict['icaoto']
	dist=cosinedist(lat1,lon1,lat2,lon2)
	return dist

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

def build_locations(): #return dictionary of airport locations
	loc_dict = {}
	in_ap=0
	dir1='/mnt/data/XPLANE10/X-Plane10/Custom Scenery/zzzz_FSE_Airports/Earth nav data/apt.dat'
	dir2='/mnt/data/XPLANE10/X-Plane10/Resources/default scenery/default apt dat/Earth nav data/apt.dat'
	for line in fileinput.input([dir1,dir2]): # I am forever indebted to Padraic Cunningham for this code
		params=line.split()
		header=int(params[0])
		if in_ap==1:
			if header==100:
				lat=float(params[9])
				lon=float(params[10])
				loc_dict[icao]=(lat,lon)
			in_ap=0
		if header==1 or header==16 or header==17:
			icao=params[4]
			in_ap=1
	return loc_dict

def build_csv(): #return dictionary of airport locations, using FSE csv file
	loc_dict = {}
	file='/mnt/data/XPLANE10/XSDK/icaodata.csv'
	with open(file, 'r') as f:
		reader = csv.reader(f)
		for row in reader:
			loc_dict[row[0]]=(row[1],row[2])
	return loc_dict

def walkthewalk(icaofrom,icaoto,chain):
	dir=dirbwt(icaoto,icaofrom)
	min_dir=chgdir(dir,-60)
	max_dir=chgdir(dir,60)
	jobs=jobsto(icaoto,5000,8) #(loc,amt,typ,pay)
	print("Searching jobs from "+icaofrom+" to "+icaoto+"...")
	for job in jobs:
		if job[0]==icaofrom:
			chain.append(job)
			return chain
		else:
			dir=dirbwt(icaoto,job[0])
			if (dir<max_dir and (dir>min_dir or min_dir>max_dir) or dir>min_dir and (dir<max_dir or min_dir>max_dir)):
				chain.append(job)
				return walkthewalk(icaofrom,job[0],chain)
	return chain

def chgdir(dir,delt):
	dir+=delt
	if dir>360:
		dir-=360
	elif dir<0:
		dir+=360
	return dir

def nearby(icao,rad):
	for apt, coords in loc_dict.items():
		dist=cosinedist(loc_dict[apt][0],loc_dict[apt][1],coords[0],coords[1])
		if dist<rad:
			print(apt+" "+str(dist))

def dudewheresmyairplane():
	planes={}
	print("Sending request for aircraft list...")
	data = urllib.request.urlopen('http://server.fseconomy.net/data?userkey='+mykey+'&format=xml&query=aircraft&search=key&readaccesskey='+mykey).read()
	print("Parsing response...")
	xmldoc = minidom.parse(data)
	airplanes = xmldoc.getElementsByTagName("Aircraft")
	for plane in airplanes:
		loc = assignment.getElementsByTagName("Location")[0].firstChild.nodeValue
		reg = assignment.getElementsByTagName("Registration")[0].firstChild.nodeValue
		planes[reg]=loc
	return planes

mykey = "CHANGEME"
file='/mnt/data/XPLANE10/XSDK/mykey.txt'
with open(file, 'r') as f:
	mykey = f.readline()
print("Building coordinate dictionary...")
loc_dict=build_locations()
print("Building alternate dictionary from csv...")
loc_dict2=build_csv()
print("Looking up the old way...")
latt,lonn=get_dest_info("KORD")
print("Looking up the new way...")
lat,lon=loc_dict['KORD']
print("KORD returns "+str(latt)+" "+str(lonn))
print("KORD returns "+str(lat)+" "+str(lon))
print("Looking up the old way...")
latt,lonn=get_dest_info("KSEA")
print("Looking up the new way...")
lat2,lon2=loc_dict['KSEA']
print("KSEA returns "+str(latt)+" "+str(lonn))
print("KSEA returns "+str(lat2)+" "+str(lon2))

#hdist=haverdist("KORD","KSEA")
#cdist=cosinedist("KORD","KSEA")
#hdg=inithdg("KORD","KSEA")
#print("Haverdist: "+str(int(round(hdist)))+"  Cdist: "+str(int(round(cdist)))+"  Hdg: "+str(int(round(hdg))))

chain=[]
walkthewalk("KAIA","SEGU",chain)

nearby("KSEA",30)

#Airports to watch
apts="SPIM-SPJJ-SEGU-SEQU-SPZO-SPQU-SPJN-SPGM-SPOL-SETA-SPEO-SKBO-SKGB-SKCL-MPTO-MPHO"
jobs=jobsfrom(apts,10000,32)
printjobs(jobs)

locations=dudewheresmyairplane()
for plane,icao in locations.items():
	print(plane)
	nearby(icao,250)
