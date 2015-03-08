from xml.dom import minidom
import urllib.request
import math
import os
import re
import fileinput
import csv
import locale
import time

file='/mnt/data/XPLANE10/XSDK/mykey.txt'
with open(file, 'r') as f:
	mykey = f.readline()
mykey=mykey.strip()
chain=[]
checked=""
requests=[]
totalto=0
totalfrom=0

def fserequest(rqst,tagname):
	now=int(time.time())
	total=len(requests)
	if total>10:
		sinceten=now-requests[total-11]
		if sinceten<60:
			towait=66-sinceten
			print("Last 10 requests too fast, sleeping "+str(towait)+" secs.")
			time.sleep(towait)
	requests.append(now)
	data = urllib.request.urlopen('http://server.fseconomy.net/data?userkey='+mykey+'&format=xml&'+rqst)
	print("Parsing data...")
	xmldoc = minidom.parse(data)
	error = xmldoc.getElementsByTagName('Error')
	if error!=[]:
		print("Received error: "+error[0].firstChild.nodeValue)
		tags=[]
	else:
		tags = xmldoc.getElementsByTagName(tagname)
	return tags

def acforsale():
	# Aircraft name, ICAO code, max price, max hours
	goodones=(("Pilatus PC-12","PC12",750000,100),
			("Beechcraft 1900D","BE19",1150000,50),
			("Bombardier Challenger 300","CL30",875000,100),
			("Ilyushin Il-14","IL14",1450000,50),
			("Alenia C-27J Spartan","C27J",3600000,200),
			("Alenia C-27J Spartan (IRIS)","C27J",3600000,200),
			("Lockheed C-130 (Generic)","C130",4500000,500),
			("Lockheed C-130 (Capt Sim)","C130",4500000,500),
			("Bombardier Dash-8 Q400","DH8D",8000000,500),
			("Dassault Falcon 7X","FA7X",1800000,10000),
			("Fairchild C123","C123",5000000,10000),
			("Douglas C117D","C117",5000000,10000),
			("Cessna Citation X","C750",1200000,10000))
	print("Sending request for sales listing...")
	#data = urllib.request.urlopen('http://server.fseconomy.net/data?userkey='+mykey+'&format=xml&query=aircraft&search=forsale')
	#print("Parsing data...")
	#xmldoc = minidom.parse(data)
	#airplanes = xmldoc.getElementsByTagName("Aircraft")
	airplanes = fserequest('query=aircraft&search=forsale','Aircraft')
	for airplane in airplanes:
		actype = airplane.getElementsByTagName("MakeModel")[0].firstChild.nodeValue
		aframetime = airplane.getElementsByTagName("AirframeTime")[0].firstChild.nodeValue
		hours = int(aframetime.split(":")[0])
		price = float(airplane.getElementsByTagName("SalePrice")[0].firstChild.nodeValue)
		for option in goodones:
			if actype==option[0] and hours<option[3] and price<option[2]:
				loc = airplane.getElementsByTagName("Location")[0].firstChild.nodeValue
				locname = airplane.getElementsByTagName("LocationName")[0].firstChild.nodeValue
				dist=distbwt("SPJJ",loc)
				print(option[1]+" | "+aframetime+" | $"+locale.format("%d", price, grouping=True)+" | "+loc+" | "+str(dist)+" | "+locname)

def dudewheresmyairplane():
	planes={}
	print("Sending request for aircraft list...")
	#data = urllib.request.urlopen('http://server.fseconomy.net/data?userkey='+mykey+'&format=xml&query=aircraft&search=key&readaccesskey='+mykey).read()
	#print("Parsing response...")
	#xmldoc = minidom.parseString(data.decode('utf-8'))
	#airplanes = xmldoc.getElementsByTagName("Aircraft")
	airplanes = fserequest('query=aircraft&search=key&readaccesskey='+mykey,'Aircraft')
	for plane in airplanes:
		loc = plane.getElementsByTagName("Location")[0].firstChild.nodeValue
		reg = plane.getElementsByTagName("Registration")[0].firstChild.nodeValue
		eng = plane.getElementsByTagName("EngineTime")[0].firstChild.nodeValue
		chk = plane.getElementsByTagName("TimeLast100hr")[0].firstChild.nodeValue
		planes[reg]=(loc,eng,chk)
	return planes

def jobsfrom(apts,price,pax):
	#High paying jobs from airports
	jobs=[]
	print("Sending request for jobs from "+apts+"...")
	#data = urllib.request.urlopen('http://server.fseconomy.net/data?userkey='+mykey+'&format=xml&query=icao&search=jobsfrom&icaos='+apts).read()
	#print("Parsing response...")
	#xmldoc = minidom.parseString(data.decode('utf-8'))
	#assignments = xmldoc.getElementsByTagName("Assignment")
	assignments = fserequest('query=icao&search=jobsfrom&icaos='+apts,'Assignment')
	for assignment in assignments:
		pay = float(assignment.getElementsByTagName("Pay")[0].firstChild.nodeValue)
		if pay>price:
			dep = assignment.getElementsByTagName("FromIcao")[0].firstChild.nodeValue
			arr = assignment.getElementsByTagName("ToIcao")[0].firstChild.nodeValue
			loc = assignment.getElementsByTagName("Location")[0].firstChild.nodeValue
			amt = assignment.getElementsByTagName("Amount")[0].firstChild.nodeValue
			typ = assignment.getElementsByTagName("UnitType")[0].firstChild.nodeValue
			exp = assignment.getElementsByTagName("Expires")[0].firstChild.nodeValue
			if not(int(amt)>pax and typ=="passengers"):
				jobs.append((loc,arr,amt,typ,pay,exp))
				# if dep==loc:
					# print(amt+" "+typ+" "+dep+"-"+arr+" $"+str(int(pay))+" "+exp)
				# else:
					# print(amt+" "+typ+" @"+dep+"-"+arr+" $"+str(int(pay))+" "+exp)
		global totalfrom
		totalfrom+=1
	return jobs

def jobsto(apts,price,pax):
	#High paying jobs to airports
	jobs=[]
	print("Sending request for jobs to "+apts+"...")
	#data = urllib.request.urlopen('http://server.fseconomy.net/data?userkey='+mykey+'&format=xml&query=icao&search=jobsto&icaos='+apts).read()
	#print("Parsing response...")
	#xmldoc = minidom.parseString(data.decode('utf-8'))
	#assignments = xmldoc.getElementsByTagName("Assignment")
	assignments = fserequest('query=icao&search=jobsto&icaos='+apts,'Assignment')
	for assignment in assignments:
		pay = float(assignment.getElementsByTagName("Pay")[0].firstChild.nodeValue)
		if pay>price:
			dep = assignment.getElementsByTagName("FromIcao")[0].firstChild.nodeValue
			arr = assignment.getElementsByTagName("ToIcao")[0].firstChild.nodeValue
			loc = assignment.getElementsByTagName("Location")[0].firstChild.nodeValue
			amt = assignment.getElementsByTagName("Amount")[0].firstChild.nodeValue
			typ = assignment.getElementsByTagName("UnitType")[0].firstChild.nodeValue
			exp = assignment.getElementsByTagName("Expires")[0].firstChild.nodeValue
			if not(int(amt)>pax and typ=="passengers"):
				jobs.append((loc,arr,amt,typ,pay,exp))
				#if dep==loc:
				#	print (amt+" "+typ+" "+dep+"-"+arr+" $"+str(int(pay))+" "+exp)
				#else:
				#	print (amt+" "+typ+" @"+loc+"-"+arr+" $"+str(int(pay))+" "+exp)
		global totalto
		totalto+=1
	return jobs

def printjobs(jobs):
	for job in jobs:
		print(job[2]+" "+job[3]+" "+job[0]+"-"+job[1]+" $"+str(int(job[4]))+" "+str(distbwt(job[0],job[1]))+" "+job[5])

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
	lat1,lon1=loc_dict[icaofrom]
	lat2,lon2=loc_dict[icaoto]
	hdg=inithdg(lat1,lon1,lat2,lon2)
	return hdg

def distbwt(icaofrom,icaoto):
	lat1,lon1=loc_dict[icaofrom]
	lat2,lon2=loc_dict[icaoto]
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

def build_xplane_locations(): #return dictionary of airport locations
	loc_dict = {}
	in_ap=0
	dir1='/mnt/data/XPLANE10/X-Plane10/Custom Scenery/zzzz_FSE_Airports/Earth nav data/apt.dat'
	dir2='/mnt/data/XPLANE10/X-Plane10/Resources/default scenery/default apt dat/Earth nav data/apt.dat'
	for line in fileinput.input([dir1,dir2]): # I am forever indebted to Padraic Cunningham for this code
		params=line.split()
		try:
			header=params[0]
			if in_ap=="1":
				if header==100:
					lat=float(params[9])
					lon=float(params[10])
					loc_dict[icao]=(lat,lon)
				in_ap=0
			if header=="1" or header=="16" or header=="17":
				icao=params[4]
				in_ap=1
		except (KeyError,IndexError) as e:
			pass
	return loc_dict

def build_csv(): #return dictionary of airport locations, using FSE csv file
	loc_dict = {}
	file='/mnt/data/XPLANE10/XSDK/icaodata.csv'
	with open(file, 'r') as f:
		has_header = csv.Sniffer().has_header(f.read(1024))
		f.seek(0)  # rewind
		reader = csv.reader(f)
		if has_header:
			next(reader)  # skip header row
		for row in reader:
			loc_dict[row[0]]=(float(row[1]),float(row[2]))
	return loc_dict

def walkthewalk(icaofrom,icaoto,chain):
	global checked
	if not icaoto in checked:
		checked=checked+"-"+icaoto
		#print("Basic direction from "+icaoto[0:4]+" to "+icaofrom)
		hdg=dirbwt(icaoto[0:4],icaofrom)
		min_hdg=chgdir(hdg,-80)
		max_hdg=chgdir(hdg,80)
		jobs=jobsto(icaoto,4000,8) #(loc,arr,amt,typ,pay,exp)
		print("Searching job chain from "+icaofrom+" to "+icaoto+", hdg "+str(int(round(min_hdg)))+"-"+str(int(round(max_hdg)))+"...")
		for job in jobs:
			if job[0]==icaofrom:
				chain.append(job)
				return chain
			else:
				hdg=dirbwt(job[1],job[0])
				#print("JOB:"+job[2]+" "+job[3]+" "+job[0]+"-"+job[1]+" "+str(hdg)+" $"+str(int(job[4]))+" "+str(distbwt(job[0],job[1]))+"Nm "+job[5])
				if (hdg<max_hdg and (hdg>min_hdg or min_hdg>max_hdg) or hdg>min_hdg and (hdg<max_hdg or min_hdg>max_hdg)):
					chain.append(job)
					walkthewalk(icaofrom,job[0],chain)
		if len(icaoto)>4:
			return chain
		else:
			near=nearby(icaoto,50)
			if len(near)>0:
				walkthewalk(icaofrom,near,chain)
			else:
				return chain

def chgdir(hdg,delt):
	hdg+=delt
	if hdg>360:
		hdg-=360
	elif hdg<0:
		hdg+=360
	return hdg

def nearby(icao,rad):
	#print("Looking for airports near "+icao)
	near=""
	clat,clon=loc_dict[icao]
	for apt,coords in loc_dict.items():
		if apt!=icao:
			#print("Dist from "+str(clat)+" "+str(clon)+" to "+str(coords[0])+" "+str(coords[1]))
			dist=cosinedist(clat,clon,coords[0],coords[1])
			if dist<rad:
				if near=="":
					near=apt
				else:					
					near=near+"-"+apt
	#print(near)
	return near

def bigjobs(apts):
	total=0
	for airport in apts:
		area=nearby(airport,50)
		jobs=jobsfrom(area,30000,8)
		printjobs(jobs)
		total+=len(jobs)
	print("Found "+str(total)+" jobs at those airports:")
	

print("Building airport location dictionary from csv...")
loc_dict=build_csv()

acforsale()

#walkthewalk("MMCY","MPTO",chain)
#printjobs(chain)

bigjobs(("KEGI","KPBF","KMLC","TS08","XS44","MMMA","KPWG","KCZT","MMCY"))

#Airports to watch
#apts="SPIM-SPJJ-SEGU-SEQU-SPZO-SPQU-SPJN-SPGM-SPOL-SETA-SPEO-SKBO-SKGB-SKCL-MPTO-MPHO"
#jobs=jobsfrom(apts,30000,32)
#printjobs(jobs)

#locations=dudewheresmyairplane()
#for plane,info in locations.items():
#	print(plane+" at "+info[0]+"  tot: "+info[1]+"  since: "+info[2])

print("Made "+str(len(requests))+" requests in "+str(requests[len(requests)-1]-requests[0])+" secs.")
print("Considered "+str(totalto)+" jobs to and "+str(totalfrom)+" jobs from airports.")
