#!/usr/bin/python
from xml.dom import minidom
import urllib.request
import math
import os, re, fileinput, csv
import locale, time
import sys, getopt
import regions
import sqlite3

def fserequest(rqst,tagname):
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
	print("Sending request for sales listing...")
	airplanes = fserequest('query=aircraft&search=forsale','Aircraft')
	print("Recording data...")
	c=getdbcon()
	iter=getmaxiter()
	iter+=1
	now=time.strftime("%Y-%m-%d %H:%M", time.gmtime())
	row=(iter, now)
	c.execute('INSERT INTO queries VALUES (?,?);',row)
	for airplane in airplanes:
		actype = airplane.getElementsByTagName("MakeModel")[0].firstChild.nodeValue
		serial = int(airplane.getElementsByTagName("SerialNumber")[0].firstChild.nodeValue)
		aframetime = airplane.getElementsByTagName("AirframeTime")[0].firstChild.nodeValue
		hours = int(aframetime.split(":")[0])
		price = float(airplane.getElementsByTagName("SalePrice")[0].firstChild.nodeValue)
		loc = airplane.getElementsByTagName("Location")[0].firstChild.nodeValue
		locname = airplane.getElementsByTagName("LocationName")[0].firstChild.nodeValue
		row=(serial, actype, loc, locname, hours, price, iter)
		c.execute('INSERT INTO allac VALUES (?,?,?,?,?,?,?);',row)
	conn.commit()
	conn.close()

def getdbcon(conn):
	c = conn.cursor()
	c.execute("select count(*) from sqlite_master where type = 'table';")
	if c.fetchone() == 0:
		c.execute('''CREATE TABLE allac
			 (serial real, type text, loc text, locname text, hours real, price real, obsiter real)''')
		c.execute('''CREATE TABLE queries
			 (iter real, qtime text)''')
		# Save (commit) the changes
		conn.commit()
	return c
	
def getmaxiter():
	c.execute('SELECT iter FROM queries ORDER BY iter DESC;')
	if c.fetchone() > 0:
		iter=c.fetchone()
	else:
		iter=0
	return iter

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
		if loc!="In Flight":
			near=nearby(loc,75)
			try:
				apts=models[mod]
				apts=apts+"-"+near
			except (KeyError,IndexError) as e:
				apts=near
			models[mod]=apts
	for model,apts in models.items():
		seats=getseats(model)
		jobs=jobsfrom(apts,price,seats)
		print(model+": "+str(seats)+" seats")
		printjobs(jobs,0)
	
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
		seats=48
	elif model=="Saab 340B":
		seats=34
	elif model=="Cessna 208":
		seats=13
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

def cosinedist(lat1,lon1,lat2,lon2):
	phi1 = math.radians(lat1)
	phi2 = math.radians(lat2)
	dellamb = math.radians(lon2-lon1)
	R = 3440.06479 # Nm
	# gives d in Nm
	d = math.acos( math.sin(phi1)*math.sin(phi2) + math.cos(phi1)*math.cos(phi2) * math.cos(dellamb) ) * R
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

def build_xplane_locations(): #keeping this in case FSE csv file fails
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
	if green==2: #Include green jobs
		jobs=paxto(icaoto,minpax,maxpax)
		checked[2]=checked[2]+"-"+icaoto
		pax="pax "
	elif green==1: #Wider (+/-120 deg) search
		jobs=jobsto(icaoto,4000,maxpax) #(loc,arr,amt,typ,pay,exp)
		checked[1]=checked[1]+"-"+icaoto
		pax=""
	else: #Standard (+/-60 deg) search
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

def bigjobs(apts,dir):
	total=0
	for airport in apts:
		if dir==0:
			area=nearby(airport,50)
			jobs=jobsfrom(area,30000,8) 
		else:
			jobs=jobsto(airport,30000,8)
		printjobs(jobs,0)
		total+=len(jobs)
	word="from near" if dir==0 else "to"
	print("Found these "+str(total)+" big jobs "+word+" those airports:")
	
def mapper(points, mincoords, maxcoords): # Put the points on a map, color by division
	if maxcoords[1]-mincoords[1]>180 or maxcoords[0]-mincoords[0]>60: # World with center aligned
		m = Basemap(projection='hammer',lon_0=(maxcoords[1]+mincoords[1])/2)
	else: # Center map on area
		width=maxcoords[1]-mincoords[1]
		height=maxcoords[0]-mincoords[0]
		m = Basemap(projection='lcc', resolution=None, llcrnrlon=mincoords[1]+0.1*width, llcrnrlat=mincoords[0]+0.1*height, urcrnrlon=maxcoords[1]+0.1*width, urcrnrlat=maxcoords[0]+0.1*height)
		# m = Basemap(width=35000000, height=22000000, projection='lcc', resolution=None, lat_0=1.0, lon_0=1.0)
	m.shadedrelief()
	# m.drawlsmask(land_color='#F5F6CE',ocean_color='#CEECF5',lakes=True)
	colors=['b','g','r','c','m','#088A29','#FF8000','#6A0888','#610B0B','#8A4B08','#A9F5A9'] # HTML dark green, orange, purple, dark red, dark orange, light green
	for i in range(len(divs)):
		print("Plotting division "+str(i))
		# x, y = m([k[1] for k in divs[i]], [k[0] for k in divs[i]])
#			print("Plotting coord "+str(divs[i][j][0])+", "+str(divs[i][j][1]))
		x, y = m(points[i][1],points[i][0])
		ptsize=3
		c='b'
		m.plot(x,y,markersize=ptsize,marker='o',markerfacecolor=c)
	plt.title('Locations of aircraft for sale',fontsize=12)
	plt.show()

def gettotals(conn):
	c=getdbcon(conn)
	totals=[]
	iters=getmaxiter()
	for i in range(iters):
		c.execute("SELECT COUNT(*) FROM allac WHERE iter = ?;", i)
		totals.append(c.fetchone())
	return totals

def maplocations(conn):
	c=getdbcon(conn)
	locations=[]
	lat_tot=0
	lon_tot=0
	latmax,lonmax,latmin,lonmin=100,200,100,200 #garbage to signal init
	for row in c.execute("SELECT loc FROM allac WHERE iter = ?;", iters)
		lat,lon=loc_dict[row[0]]
		locations.append((lat,lon))
		lat_tot+=lat
		lon_tot+=lon
		if lat<latmin or abs(latmin)>90:
			latmin=lat
		elif lat>latmax or abs(latmax)>90:
			latmax=lat
		if lon<lonmin or abs(lonmin)>180:
			lonmin=lon
		elif lon>lonmax or abs(lonmax)>180:
			lonmax=lon
	pts=len(locations)
	center=(lat_tot/pts,lon_tot/pts)
	
	mapper(locations, (latmin,lonmin), (latmax,lonmax))

def main(argv):
	file='/mnt/data/XPLANE10/XSDK/mykey.txt'
	with open(file, 'r') as f:
		mykey = f.readline()
	mykey=mykey.strip()
	
	requests=[]
	
	print("Building airport location dictionary from csv...")
	loc_dict=build_csv()
	
	conn = sqlite3.connect('/mnt/data/XPLANE10/XSDK/forsale.db')
	
	acforsale(conn)
	
	# We can also close the connection if we are done with it.
	# Just be sure any changes have been committed or they will be lost.
	conn.close()
	
	syntaxstring='fses.py -hcpsb -f <from ICAOs> -t <to ICAOs> -r <min pay> -m <min pax> -n <max pax> -g <from region> -u <to region>'
	try:
		opts, args = getopt.getopt(argv,"hcpf:t:r:m:n:g:u:",["from=","to=","minrev=","minpax=","maxpax=","fromregion=","toregion="])
	except getopt.GetoptError:
		print syntaxstring
		sys.exit(2)
	for opt, arg in opts:
		if opt=='-h':
			print syntaxstring
			sys.exit()
		elif opt=='-c':
			walk=1
		elif opt=='-p':
			planes=1
		elif opt=='-s':
			sale=1
		elif opt=='-b':
			big=1
		elif opt in ("-r", "--minrev"):
			minrev=int(arg)
		elif opt in ("-m", "--minpax"):
			minpax=int(arg)
		elif opt in ("-n", "--maxpax"):
			maxpax=int(arg)
		elif opt in ("-f", "--from"):
			fromairports=arg
		elif opt in ("-t", "--to"):
			toairports=arg
		elif opt in ("g", "--fromregion"):
			fromregion=regions.getairports(arg)
		elif opt in ("u", "--to region"):
			toregion=regions.getairports(arg)
	if walk==1:
		if fromairports!="" and toairports!="":
			walkthewalk(fromairports,toairports,chain,0,minpax,maxpax)
			printjobs(chain,1)
		else:
			print 'fses.py: need both from and to airports for -c chain option'
			sys.exit(2)
	elif big==1:
		if fromairports!="":
			bigjobs(fromairports,0)
		if toairports!="":
			bigjobs(toairports,1)
		if fromregion!="":
			bigjobs(fromregion,0)
		if toregion!="":
			bigjobs(toregion,1)
	else:
		if fromairports!="":
			jobs=jobsfrom(fromairports,minrev,maxpax)
			printjobs(jobs,0)
		if toairports!="":
			jobs=jobsto(toairports,minrev,maxpax)
			printjobs(jobs,0)
	if sale==1:
		acforsale()
	if planes==1:
		dudewheresmyairplane()
		jobs=jobsforairplanes(minrev)
		printjobs(jobs,0)
	
	
	print("Made "+str(len(requests))+" requests in "+str(requests[len(requests)-1]-requests[0])+" secs.")
	print("Considered "+str(totalto)+" jobs to and "+str(totalfrom)+" jobs from airports.")

if __name__ == "__main__":
   main(sys.argv[1:])
