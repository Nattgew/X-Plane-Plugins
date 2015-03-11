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
checked=["","",""]
requests=[]
totalto=0
totalfrom=0

def fserequest(rqst,tagname):
	global requests
	now=int(time.time())
	total=len(requests)
	if total>10:
		sinceten=now-requests[total-11]
		if sinceten<60:
			towait=66-sinceten
			print("Reached 10 requests/min limit, sleeping "+str(towait)+" secs.")
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
	goodones=[]
	file='/mnt/data/XPLANE10/XSDK/criteria.csv'
	with open(file, 'r') as f:
		has_header = csv.Sniffer().has_header(f.read(1024))
		f.seek(0)  # rewind
		reader = csv.reader(f)
		if has_header:
			next(reader)  # skip header row
		for row in reader:
			goodones.append(row[0],row[1],int(row[2]),int(row[3]))
	# goodones=(("Pilatus PC-12","PC12",750000,100),
			# ("Beechcraft 1900D","BE19",1150000,50),
			# ("Bombardier Challenger 300","CL30",875000,100),
			# ("Ilyushin Il-14","IL14",1450000,50),
			# ("Alenia C-27J Spartan","C27J",3600000,200),
			# ("Alenia C-27J Spartan (IRIS)","C27J",3600000,200),
			# ("Lockheed C-130 (Generic)","C130",4500000,500),
			# ("Lockheed C-130 (Capt Sim)","C130",4500000,500),
			# ("Bombardier Dash-8 Q400","DH8D",8000000,500),
			# ("Dassault Falcon 7X","FA7X",1800000,10000),
			# ("Fairchild C123","C123",5000000,10000),
			# ("Douglas C117D","C117",5000000,10000),
			# ("Cessna Citation X","C750",1200000,10000))
	print("Sending request for sales listing...")
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
				break

def dudewheresmyairplane():
	#planes={}
	print("Sending request for aircraft list...")
	airplanes = fserequest('query=aircraft&search=key&readaccesskey='+mykey,'Aircraft')
	for plane in airplanes:
		loc = plane.getElementsByTagName("Location")[0].firstChild.nodeValue
		reg = plane.getElementsByTagName("Registration")[0].firstChild.nodeValue
		eng = plane.getElementsByTagName("EngineTime")[0].firstChild.nodeValue
		chk = plane.getElementsByTagName("TimeLast100hr")[0].firstChild.nodeValue
		#planes[reg]=(loc,eng,chk)
		print(reg+" at "+loc+"  tot: "+eng+"  last: "+chk)

def jobsforairplanes(price):
	models={}
	jobs=[]
	print("Sending request for aircraft list...")
	airplanes = fserequest('query=aircraft&search=key&readaccesskey='+mykey,'Aircraft')
	for plane in airplanes:
		loc = plane.getElementsByTagName("Location")[0].firstChild.nodeValue
		mod = plane.getElementsByTagName("MakeModel")[0].firstChild.nodeValue
		try:
			apts=models[mod]
			apts=apts+"-"+loc
		except (KeyError,IndexError) as e:
			apts=loc
		models[mod]=apts
	for model,apts in models.items():
		seats=getseats(model)
		jobs.extend(jobsto(apts,price,seats))
	return jobs
	
def getseats(model):
	if model=="Pilatus PC-12":
		seats=10
	elif model=="Bombardier Challenger 300":
		seats=8
	elif model=="Ilyushin Il-14":
		seats=32
	elif model=="Beechcraft 1900D":
		seats=19
	elif model=="Alenia C-27J Spartan (IRIS)" or model=="Alenia C-27J Spartan":
		seats=45
	else:
		seats=0
	return seats

def jobsfrom(apts,price,pax):
	#High paying jobs from airports
	jobs=[]
	print("Sending request for jobs from "+apts+"...")
	assignments = fserequest('query=icao&search=jobsfrom&icaos='+apts,'Assignment')
	for assignment in assignments:
		jobs=jobstest(assignment,jobs,price,pax)
		global totalfrom
		totalfrom+=1
	return jobs

def jobsto(apts,price,pax):
	#High paying jobs to airports
	jobs=[]
	print("Sending request for jobs to "+apts+"...")
	assignments = fserequest('query=icao&search=jobsto&icaos='+apts,'Assignment')
	for assignment in assignments:
		jobs=jobstest(assignment,jobs,price,pax)
		global totalto
		totalto+=1
	return jobs

def jobstest(assignment,jobs,price,pax):
	pay = float(assignment.getElementsByTagName("Pay")[0].firstChild.nodeValue)
	if pay>price:
		amt = assignment.getElementsByTagName("Amount")[0].firstChild.nodeValue
		typ = assignment.getElementsByTagName("UnitType")[0].firstChild.nodeValue
		if not(int(amt)>pax and typ=="passengers"):
			#dep = assignment.getElementsByTagName("FromIcao")[0].firstChild.nodeValue
			arr = assignment.getElementsByTagName("ToIcao")[0].firstChild.nodeValue
			loc = assignment.getElementsByTagName("Location")[0].firstChild.nodeValue
			exp = assignment.getElementsByTagName("Expires")[0].firstChild.nodeValue
			jobs.append((loc,arr,amt,typ,pay,exp))
			#if dep==loc:
			#	print (amt+" "+typ+" "+dep+"-"+arr+" $"+str(int(pay))+" "+exp)
			#else:
			#	print (amt+" "+typ+" @"+loc+"-"+arr+" $"+str(int(pay))+" "+exp)
	return jobs

def paxto(apts,minpax,maxpax):
	#Pax jobs to airports (incl green jobs)
	print("Sending request incl pax jobs to "+apts+"...")
	assignments = fserequest('query=icao&search=jobsto&icaos='+apts,'Assignment')
	jobs=paxtest(assignments,minpax,maxpax,"to")
	return jobs

def paxfrom(apts,minpax,maxpax):
	#Pax jobs from airports (incl green jobs)
	print("Sending request incl pax jobs from "+apts+"...")
	assignments = fserequest('query=icao&search=jobsfrom&icaos='+apts,'Assignment')
	jobs=paxtest(assignments,minpax,maxpax,"from")
	return jobs

def paxtest(assignments,minpax,maxpax,tofrom):
	candidates=[]
	apts={}
	jobs=[]
	for assignment in assignments:
		loc = assignment.getElementsByTagName("Location")[0].firstChild.nodeValue
		arr = assignment.getElementsByTagName("ToIcao")[0].firstChild.nodeValue
		amt = assignment.getElementsByTagName("Amount")[0].firstChild.nodeValue
		typ = assignment.getElementsByTagName("UnitType")[0].firstChild.nodeValue
		if tofrom=="to":
			global totalto
			totalto+=1
			key=loc
		else:
			global totalfrom
			totalfrom+=1
			key=arr
		if not(int(amt)>maxpax and typ=="passengers") and typ=="passengers":
			amt=int(amt)
			pay = float(assignment.getElementsByTagName("Pay")[0].firstChild.nodeValue)
			#dep = assignment.getElementsByTagName("FromIcao")[0].firstChild.nodeValue
			exp = assignment.getElementsByTagName("Expires")[0].firstChild.nodeValue
			candidates.append((loc,arr,amt,typ,pay,exp))
			try:
				tot=apts[key]
				tot+=amt
			except (KeyError,IndexError) as e:
				tot=amt
			apts[key]=tot
	for option in candidates:
		tot=apts[option[0]]
		if tot>minpax:
			jobs.append(option)
	return jobs

def printjobs(jobs,rev):
	if rev==1:
		list=jobs
	else:
		list=reversed(jobs)
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

def walkthewalk(icaofrom,icaoto,chain,green,minpax,maxpax):
	print("Walking from "+icaofrom+" to "+icaoto)
	global checked
	print("Basic direction from "+icaoto[0:4]+" to "+icaofrom)
	hdg=dirbwt(icaoto[0:4],icaofrom)
	if green>0:
		min=-120
		max=120
	else:
		min=-60
		max=60
	min_hdg=chgdir(hdg,min)
	max_hdg=chgdir(hdg,max)
	if green==2:
		jobs=paxto(icaoto,minpax,maxpax)
		checked[2]=checked[2]+"-"+icaoto
		pax="pax "
	elif green==1:
		jobs=jobsto(icaoto,4000,maxpax) #(loc,arr,amt,typ,pay,exp)
		checked[1]=checked[1]+"-"+icaoto
		pax=""
	else:
		jobs=jobsto(icaoto,4000,maxpax) #(loc,arr,amt,typ,pay,exp)
		checked[0]=checked[0]+"-"+icaoto
		pax=""
	print("Searching "+pax+"job chain from "+icaofrom+" to "+icaoto+", hdg "+str(int(round(min_hdg)))+"-"+str(int(round(max_hdg)))+"...")
	iter=0
	for job in jobs:
		iter+=1
		if job[0]==icaofrom:
			print("You win")
			chain.append(job)
			return chain
		else:
			hdg=dirbwt(job[1],job[0])
			#print("JOB:"+job[2]+" "+job[3]+" "+job[0]+"-"+job[1]+" "+str(hdg)+" $"+str(int(job[4]))+" "+str(distbwt(job[0],job[1]))+"Nm "+job[5])
			if (hdg<max_hdg and (hdg>min_hdg or min_hdg>max_hdg) or hdg>min_hdg and (hdg<max_hdg or min_hdg>max_hdg)):
				print("Adding job "+job[0]+" to "+job[1]+" "+job[2]+" "+job[3]+" $"+str(job[4])+" "+job[5])
				chain.append(job)
				return walkthewalk(icaofrom,job[0],chain,0,minpax,maxpax)
	if len(icaoto)>4:
		print("Failed to find jobs nearby")
		if green<2:
			return walkthewalk(icaofrom,icaoto,chain,green+1,minpax,maxpax)
		else:
			return chain
	else:
		near=nearby(icaoto,50)+"-"+icaoto
		if len(near)>0:
			if not near in checked[0]:
				return walkthewalk(icaofrom,near,chain,0,minpax,maxpax)
			elif not near in checked[1]:
				print("Failed to find jobs at arpts nearby")
				return walkthewalk(icaofrom,near,chain,1,minpax,maxpax)
			elif not near in checked[2]:
				print("Failed to find expanded direction jobs at arpts nearby")
				return walkthewalk(icaofrom,near,chain,2,minpax,maxpax)
			else:
				print("Dead end")
				return chain
		else:
				print("Dead end, no airports near"+icaoto)
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
		printjobs(jobs,0)
		total+=len(jobs)
	print("Found "+str(total)+" big jobs at those airports:")


print("Building airport location dictionary from csv...")
loc_dict=build_csv()

acforsale()

#walkthewalk("MRCH","SEGU",chain,0,4,8)
#printjobs(chain,1)

bigjobs(("SPIM-SPJJ-SEGU-SEQU-SPZO-SPQU-SPJN-SPGM-SPOL-SETA-SPEO-SKBO-SKGB-SKCL-MPTO-MPHO"))

jobs=jobsforairplanes(10000)

#Airports to watch
#apts="SPIM-SPJJ-SEGU-SEQU-SPZO-SPQU-SPJN-SPGM-SPOL-SETA-SPEO-SKBO-SKGB-SKCL-MPTO-MPHO"
#jobs=jobsfrom(apts,30000,32)
#printjobs(jobs,0)

#dudewheresmyairplane()

print("Made "+str(len(requests))+" requests in "+str(requests[len(requests)-1]-requests[0])+" secs.")
print("Considered "+str(totalto)+" jobs to and "+str(totalfrom)+" jobs from airports.")
