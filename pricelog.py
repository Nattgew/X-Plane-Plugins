#!/usr/bin/python
from xml.dom import minidom
import urllib.request
import math
import os, re, fileinput, csv, sqlite3
import locale, time
import sys, getopt
import dicts
from datetime import timedelta, date, datetime
from mpl_toolkits.basemap import Basemap
from matplotlib.dates import DateFormatter, date2num
import matplotlib.pyplot as plt

def getkey():
	file='/mnt/data/XPLANE10/XSDK/mykey.txt'
	with open(file, 'r') as f:
		mykey = f.readline()
	mykey=mykey.strip()
	return mykey

def getname():
	file='/mnt/data/XPLANE10/XSDK/mykey.txt'
	with open(file, 'r') as f:
		nothing = f.readline()
		myname = f.readline()
	myname=myname.strip()
	return myname

def fserequest(ra,rqst,tagname):
	if ra==1:
		rakey="&readaccesskey="+getkey()
	else:
		rakey=""
	print("Will make request: http://server.fseconomy.net/data?userkey="+getkey()+rakey+'&format=xml&'+rqst)
	data = urllib.request.urlopen('http://server.fseconomy.net/data?userkey='+getkey()+rakey+'&format=xml&'+rqst)
	print("Parsing data...")
	xmldoc = minidom.parse(data)
	error = xmldoc.getElementsByTagName('Error')
	if error!=[]:
		print("Received error: "+error[0].firstChild.nodeValue)
		tags=[]
	else:
		tags = xmldoc.getElementsByTagName(tagname)
	return tags

def acforsale(conn): #Log aircraft currently for sale
	print("Sending request for sales listing...")
	airplanes = fserequest(0,'query=aircraft&search=forsale','Aircraft')
	print("Recording data...")
	c=getdbcon(conn)
	count=getmaxiter(conn)
	count+=1
	now=time.strftime("%Y-%m-%d %H:%M", time.gmtime())
	row=(count, now)
	c.execute('INSERT INTO queries VALUES (?,?);',row) #Record date/time of this query
	for airplane in airplanes: #Record aircraft for sale
		actype = airplane.getElementsByTagName("MakeModel")[0].firstChild.nodeValue
		serial = int(airplane.getElementsByTagName("SerialNumber")[0].firstChild.nodeValue)
		aframetime = airplane.getElementsByTagName("AirframeTime")[0].firstChild.nodeValue
		hours = int(aframetime.split(":")[0])
		price = float(airplane.getElementsByTagName("SalePrice")[0].firstChild.nodeValue)
		loc = airplane.getElementsByTagName("Location")[0].firstChild.nodeValue
		locname = airplane.getElementsByTagName("LocationName")[0].firstChild.nodeValue
		row=(serial, actype, loc, locname, hours, price, count)
		c.execute('INSERT INTO allac VALUES (?,?,?,?,?,?,?);',row)
	conn.commit()
	
def logpaymonth(conn,year,month): #Log a month of payments
	print("Sending request for payment listing...")
	payments = fserequest(1,'query=payments&search=monthyear&month='+month+'&year='+year,'Payment')
	c=getpaydbcon(conn)
	print("Recording data...")
	for payment in payments:
		pdate = payment.getElementsByTagName("Date")[0].firstChild.nodeValue
		to = payment.getElementsByTagName("To")[0].firstChild.nodeValue
		fr = payment.getElementsByTagName("From")[0].firstChild.nodeValue
		amt = float(payment.getElementsByTagName("Amount")[0].firstChild.nodeValue)
		rsn = payment.getElementsByTagName("Reason")[0].firstChild.nodeValue
		loc = payment.getElementsByTagName("Location")[0].firstChild.nodeValue
		pid = int(payment.getElementsByTagName("Id")[0].firstChild.nodeValue)
		#print("pdate="+pdate+"  to="+to+"  from="+fr+"  amount="+str(amt)+"  reason="+rsn+"  loc="+loc)
		if rsn in ("Monthly Interest", "Fuel Delivered", "Sale of wholesale JetA", "Sale of wholesale 100LL", "Sale of supplies", "Sale of building materials", "Transfer of supplies", "Transfer of building materials", "Group payment", "FBO sale", "Transfer of JetA", "Transfer of 100LL"): #Broken XML
			ac = "null"
		else:
			ac = payment.getElementsByTagName("Aircraft")[0].firstChild.nodeValue
		com = payment.getElementsByTagName("Comment")[0].firstChild.nodeValue
		if com=="null":
			com=""
		pdate=pdate.replace('/','-')
		row=(pdate, to, fr, amt, rsn, loc, ac, pid, com)
		c.execute('INSERT INTO payments VALUES (?,?,?,?,?,?,?,?,?);',row)
	conn.commit()

def logpaymonthcom(conn,year,month): #Add comments to a month of payments
	print("Sending request for payment listing...")
	payments = fserequest(1,'query=payments&search=monthyear&month='+month+'&year='+year,'Payment')
	c=getpaydbcon(conn)
	print("Recording data...")
	for payment in payments:
		pid = int(payment.getElementsByTagName("Id")[0].firstChild.nodeValue)
		com = payment.getElementsByTagName("Comment")[0].firstChild.nodeValue
		if com=="null":
			com=""
		c.execute('SELECT * FROM payments WHERE pid = ?',(pid,))
		row=c.fetchone()
		c.execute('UPDATE payments SET comment = ? WHERE pid = ?',(com, pid))
	conn.commit()

def loglogmonth(conn,year,month):
	print("Sending request for logs...")
	logs = fserequest(1,'query=flightlogs&search=monthyear&month='+month+'&year='+year,'Commodity')
	c=getlogdbcon(conn)
	print("Recording data...")
	for log in logs:
		id = int(payment.getElementsByTagName("Id")[0].firstChild.nodeValue)
		typ = payment.getElementsByTagName("Type")[0].firstChild.nodeValue
		tim = payment.getElementsByTagName("Time")[0].firstChild.nodeValue
		dis = int(payment.getElementsByTagName("Distance")[0].firstChild.nodeValue)
		#pilot
		sn = int(payment.getElementsByTagName("SerialNumber")[0].firstChild.nodeValue)
		ac = payment.getElementsByTagName("Aircraft")[0].firstChild.nodeValue
		mo = payment.getElementsByTagName("MakeModel")[0].firstChild.nodeValue
		if typ=="flight":
			fr = payment.getElementsByTagName("From")[0].firstChild.nodeValue
			to = payment.getElementsByTagName("To")[0].firstChild.nodeValue
		else: #More borked XML
			fr=""
			to=""
		#total eng time
		ft = payment.getElementsByTagName("FlightTime")[0].firstChild.nodeValue
		#group name (broken)
		inc = float(payment.getElementsByTagName("Income")[0].firstChild.nodeValue)
		pf = float(payment.getElementsByTagName("PilotFee")[0].firstChild.nodeValue)
		crw = float(payment.getElementsByTagName("CrewCost")[0].firstChild.nodeValue)
		bf = float(payment.getElementsByTagName("BookingFee")[0].firstChild.nodeValue)
		bo = float(payment.getElementsByTagName("Bonus")[0].firstChild.nodeValue)
		fl = float(payment.getElementsByTagName("FuelCost")[0].firstChild.nodeValue)
		gc = float(payment.getElementsByTagName("GCF")[0].firstChild.nodeValue)
		rat = float(payment.getElementsByTagName("RentalPrice")[0].firstChild.nodeValue)
		rtp = payment.getElementsByTagName("RentalType")[0].firstChild.nodeValue
		rtt = payment.getElementsByTagName("RentalUnits")[0].firstChild.nodeValue
		rtc = float(payment.getElementsByTagName("RentalCost")[0].firstChild.nodeValue)
		tim=tim.replace('/','-')
		row = (id, typ, tim, dis, sn, ac, mo, fr, to, ft, inc, pf, crw, bf, bo, fl, gc, rat, rtp, rtt, rtc)
		c.execute('INSERT INTO logs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);',row)
	conn.commit()

def getdbcon(conn): #Get cursor for aircraft sale database
	print("Initializing database cursor...")
	c = conn.cursor()
	c.execute("select count(*) from sqlite_master where type = 'table';")
	exist=c.fetchone()
	#print("Found " + str(exist[0]) + " tables...")
	if exist[0]==0: #Table does not exist, create table
		print("Creating tables...")
		c.execute('''CREATE TABLE allac
			 (serial real, type text, loc text, locname text, hours real, price real, iter real)''')
		c.execute('''CREATE TABLE queries
			 (obsiter real, qtime text)''')
		c.execute('''CREATE INDEX idx1 ON allac(iter)''') #FIX ME
		c.execute('''CREATE INDEX idx2 ON queries(obsiter)''')
		c.execute('''CREATE INDEX idx3 ON queries(qtime)''')
		c.execute('''CREATE INDEX idx4 ON allac(type)''')
		conn.commit()
	return c
	
def getpaydbcon(conn): #Get cursor for payment database
	print("Initializing payment database cursor...")
	c = conn.cursor()
	c.execute("select count(*) from sqlite_master where type = 'table';")
	exist=c.fetchone()
	if exist[0]==0: #Table does not exist, create table
		print("Creating tables...")
		c.execute('''CREATE TABLE payments
			 (date text, payto text, payfrom text, amount real, reason text, location text, aircraft text, pid real, comment text)''')
		c.execute('''CREATE INDEX idx1 ON payments(date)''')
		conn.commit()
	com=0 #Check if comments column exists, should only need this once
	for col in c.execute('''PRAGMA table_info(payments)'''):
		if col[0]=="comment":
			com=1
			break
	if com==0:
		c.execute('''ALTER TABLE payments ADD COLUMN comment text''')
		conn.commit()
	return c

def getlogdbcon(conn): #Get cursor for log database
	print("Initializing log database cursor...")
	c = conn.cursor()
	c.execute("select count(*) from sqlite_master where type = 'table';")
	exist=c.fetchone()
	if exist[0]==0: #Table does not exist, create table
		print("Creating tables...")
		c.execute('''CREATE TABLE logs
			 (fid real, type text, time text, dist real, sn real, ac text, model text, dep text, arr text, fltime text, income real, pfee real, crew real, bkfee real, bonus real, fuel real, gndfee real, rprice real, rtype text, runits text, rcost real)''')
		c.execute('''CREATE INDEX idx1 ON logs(date)''')
		c.execute('''CREATE INDEX idx2 ON logs(type)''')
		c.execute('''CREATE INDEX idx3 ON logs(dist)''')
		c.execute('''CREATE INDEX idx4 ON logs(model)''')
		c.execute('''CREATE INDEX idx5 ON logs(ac)''')
		conn.commit()
	return c

def getmaxiter(conn): #Return the number of latest query, which is the number of queries
	c = conn.cursor()
	c.execute('SELECT iter FROM queries ORDER BY iter DESC;')
	count=c.fetchone()
	#print("Found "+str(count)+" previous queries")
	if count is not None:
		current=int(count[0])
	else:
		current=0
	return current

def dudewheresmyairplane(): #Print list of owned planes
	#planes={}
	print("Sending request for aircraft list...")
	airplanes = fserequest(1,'query=aircraft&search=key','Aircraft')
	for plane in airplanes:
		loc = plane.getElementsByTagName("Location")[0].firstChild.nodeValue
		reg = plane.getElementsByTagName("Registration")[0].firstChild.nodeValue
		eng = plane.getElementsByTagName("EngineTime")[0].firstChild.nodeValue
		chk = plane.getElementsByTagName("TimeLast100hr")[0].firstChild.nodeValue
		#planes[reg]=(loc,eng,chk)
		print(reg+" at "+loc+"  tot: "+eng+"  last: "+chk)
	
def jobsfrom(apts,price,pax): #High paying jobs from airports
	jobs=[]
	print("Sending request for jobs from "+apts+"...")
	assignments = fserequest(0,'query=icao&search=jobsfrom&icaos='+apts,'Assignment')
	for assignment in assignments:
		jobs=jobstest(assignment,jobs,price,pax)
		global totalfrom
		totalfrom+=1
	return jobs

def jobsto(apts,price,pax): #High paying jobs to airports
	jobs=[]
	print("Sending request for jobs to "+apts+"...")
	assignments = fserequest(0,'query=icao&search=jobsto&icaos='+apts,'Assignment')
	for assignment in assignments:
		jobs=jobstest(assignment,jobs,price,pax)
		global totalto
		totalto+=1
	return jobs

def jobstest(assignment,jobs,price,pax): #Only add job to array if meeting minumum pax and pay values
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

def paxto(apts,minpax,maxpax): #Pax jobs to airports (incl green jobs)
	print("Sending request incl pax jobs to "+apts+"...")
	assignments = fserequest(0,'query=icao&search=jobsto&icaos='+apts,'Assignment')
	jobs=paxtest(assignments,minpax,maxpax,"to")
	return jobs

def paxfrom(apts,minpax,maxpax): #Pax jobs from airports (incl green jobs)
	print("Sending request incl pax jobs from "+apts+"...")
	assignments = fserequest(0,'query=icao&search=jobsfrom&icaos='+apts,'Assignment')
	jobs=paxtest(assignments,minpax,maxpax,"from")
	return jobs

def paxtest(assignments,minpax,maxpax,tofrom): #Return assignments meeting min and max pax requirements
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

def printjobs(jobs,rev): #Print the list of jobs
	if rev==1:
		list=jobs
	else:
		list=reversed(jobs)
	for job in jobs:
		print(job[2]+" "+job[3]+" "+job[0]+"-"+job[1]+" $"+str(int(job[4]))+" "+str(distbwt(job[0],job[1]))+" "+job[5])
	
def cosinedist(lat1,lon1,lat2,lon2): #Use cosine to find distance between coordinates
	phi1 = math.radians(lat1)
	phi2 = math.radians(lat2)
	dellamb = math.radians(lon2-lon1)
	R = 3440.06479 # Nmi
	# gives d in Nmi
	d = math.acos( math.sin(phi1)*math.sin(phi2) + math.cos(phi1)*math.cos(phi2) * math.cos(dellamb) ) * R
	return int(round(d))

def inithdg(lat1,lon1,lat2,lon2): #Find heading between coordinates
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

def dirbwt(icaofrom,icaoto): #Find bearing from one airport to another
	lat1,lon1=loc_dict[icaofrom]
	lat2,lon2=loc_dict[icaoto]
	hdg=inithdg(lat1,lon1,lat2,lon2)
	return hdg

def distbwt(icaofrom,icaoto): #Find distance from one airport to another
	lat1,lon1=loc_dict[icaofrom]
	lat2,lon2=loc_dict[icaoto]
	dist=cosinedist(lat1,lon1,lat2,lon2)
	return dist

def build_latlon_csv(): #return dictionary of airport coordinates, using FSE csv file
	loc_dict = {}
	file='/mnt/data/XPLANE10/XSDK/icaodata.csv'
	with open(file, 'r') as f:
		has_header = csv.Sniffer().has_header(f.read(1024))
		f.seek(0)  # rewind
		reader = csv.reader(f)
		if has_header:
			next(reader)  # skip header row
		for row in reader:
			loc_dict[row[0]]=(float(row[1]),float(row[2])) #Code = lat, lon
	return loc_dict

def build_ctry_csv(): #return dictionary of airport countries, using FSE csv file
	loc_dict = {}
	file='/mnt/data/XPLANE10/XSDK/icaodata.csv'
	with open(file, 'r') as f:
		has_header = csv.Sniffer().has_header(f.read(1024))
		f.seek(0)  # rewind
		reader = csv.reader(f)
		if has_header:
			next(reader)  # skip header row
		for row in reader:
			loc_dict[row[0]]=row[8] #Code = Country
	return loc_dict

def chgdir(hdg,delt): #Add delta to heading and fix if passing 0 or 360
	hdg+=delt
	if hdg>360:
		hdg-=360
	elif hdg<=0:
		hdg+=360
	return hdg

def nearby(icao,rad): #Find other airports within radius of given airport
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

def bigjobs(apts,dir): #Find high paying jobs to/from airports
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
		
def mapper(what, points, mincoords, maxcoords, title): # Put the points on a map
	print("Mapping points...")
	if maxcoords[1]-mincoords[1]>180 or maxcoords[0]-mincoords[0]>60: # World with center aligned
		m = Basemap(projection='hammer', resolution='c', lon_0=(maxcoords[1]+mincoords[1])/2)
	else: # Center map on area
		width=maxcoords[1]-mincoords[1]
		height=maxcoords[0]-mincoords[0]
		m = Basemap(projection='cyl', resolution='c', llcrnrlon=mincoords[1]-0.1*width, llcrnrlat=mincoords[0]-0.1*height, urcrnrlon=maxcoords[1]+0.1*width, urcrnrlat=maxcoords[0]+0.1*height)
	if what=="ac":
		if len(points) < 30: #Use awesome airplane symbol
			verts = list(zip([0.,1.,1.,10.,10.,9.,6.,1.,1.,4.,1.,0.,-1.,-4.,-1.,-1.,-5.,-9.,-10.,-10.,-1.,-1.,0.],[9.,8.,3.,-1.,-2.,-2.,0.,0.,-5.,-8.,-8.,-9.,-8.,-8.,-5.,0.,0.,-2.,-2.,-1.,3.,8.,9.])) #Supposed to be an airplane
			mk=(verts,0)
			ptsize=50
		else: #Use boring but more compact dots
			mk='o'
			ptsize=2
		m.shadedrelief()
		x, y = m([i[1] for i in points], [i[0] for i in points])
		c='b'
		m.scatter(x,y,s=ptsize,marker=mk,c=c)
	elif what=="fuel":
		max=0
		for loc in points:
			thous=int(round(loc[2])) #Size of point will be based on fuel amount
			if thous>max:
				max=thous
			loc[2]=thous
		pts=[] #rows=thous, columns=colors, contents=list of points
		for i in range(max+1):
			pts.append([[],[],[]]) #Add a new empty row
			for loc in points:
				if loc[2]==i+1:
					pts[i][loc[3]].append((loc[0],loc[1]))
		for i in range(max+1): #Set size/color of points
			sz=(i+1)*2 #Size based on amount
			if pts[i]!=[[],[],[]]: #Check if any list has points
				for j in range(3):
					if pts[i][j]!=[]: #Check if this list has any points
						x, y = m([k[1] for k in pts[i][j]], [k[0] for k in pts[i][j]]) #Populate points
						if j==0: #Set color
							c='#cc9900'
						elif j==1:
							c='b'
						else:
							c='k'
						m.scatter(x,y,s=sz,marker='o',c=c) #Plot the points with these properties
	plt.title(title,fontsize=12)
	plt.show()
	
def gettotals(conn,actype,fr,to): #Return list of total aircraft for sale at each query time
	c=getdbcon(conn)
	d=getdbcon(conn)
	totals=[]
	print("Finding total aircraft for sale from "+fr+" to "+to+"...")
	for query in c.execute('SELECT * FROM queries WHERE qtime BETWEEN ? AND ?', (fr,to)):
		print("Reading query "+str(query[0])+" from "+query[1])
		if actype=="None":
			d.execute('SELECT COUNT(*) FROM allac WHERE obsiter = ?', (query[0],))
		else:
			d.execute('SELECT COUNT(*) FROM allac WHERE obsiter = ? AND type = ?', (query[0],actype))	
		total=int(d.fetchone()[0])
		totals.append((getdtime(query[1]),total))
	return totals

def getaverages(conn,actype,fr,to): #Return list of average prices for aircraft in each query time
	c=getdbcon(conn)
	d=getdbcon(conn)
	averages=[]
	fr=fr+" 00:01" #Add times to match the values in table
	to=to+" 23:59"
	print("Finding averages for: "+actype+" from "+fr+" to "+to+"...")
	for query in c.execute('SELECT * FROM queries WHERE qtime BETWEEN ? AND ?', (fr,to)): #Find the queries in this time range
		numforsale=0
		totalprice=0
		prices=[]
		for sale in d.execute('SELECT price FROM allac WHERE obsiter = ? AND type = ?', (query[0],actype)):
			totalprice+=int(sale[0])
			prices.append(sale[0])
			numforsale+=1
		if numforsale>0:
			avg=totalprice/numforsale
			ssprice=0
			for price in prices:
				ssprice+=math.pow(price-avg,2)
			stdev=math.sqrt(ssprice/numforsale)
			averages.append((getdtime(query[1]),avg,stdev))
	return averages

def getdtime(strin): #Return datetime for the Y-M-D H:M input
	adate,atime=strin.split()
	year=int(adate.split('-', 2)[0])
	month=int(adate.split('-', 2)[1])
	day=int(adate.split('-', 2)[2])
	hour=int(atime.split(':')[0])
	mnt=int(atime.split(':')[1])
	return datetime(year,month,day,hour,mnt)

def getlows(conn,actype,fr,to): #Return list of lowest price for aircraft in each query
	c=getdbcon(conn)
	d=getdbcon(conn)
	lows=[]
	print("Finding low low prices for: "+actype+"...")
	for query in c.execute('SELECT * FROM queries WHERE qtime BETWEEN ? AND ?', (fr,to)):
		d.execute('SELECT price FROM allac WHERE obsiter = ? AND type = ? ORDER BY price', (query[0],actype))
		price=d.fetchone()
		if price is not None:
			lows.append((getdtime(query[1]),price))
	return lows

def plotfuelprices(conn): #Plot fuel prices over time
	c=getdbcon(conn)
	print("Getting flight logs...") #Thinking about a raw plot per payment, and average per day
	#(date text, payto text, payfrom text, amount real, reason text, location text, aircraft text, pid real, comment text)
	for log in c.execute('SELECT amount, comment FROM payments WHERE reason = "Refuelling with JetA"'):
		#User ID: xxxxx Amount (gals): 428.9, $ per Gal: $3.75
		gals=log[1].float(split(':',2)[1].split(',')) #Maybe do this when creating db?

def getapstats(conn,actype): #Return something about airplane flight logs
	#(fid real, type text, time text, dist real, sn real, ac text, model text, dep text, arr text, fltime text, income real, pfee real, crew real, bkfee real, bonus real, fuel real, gndfee real, rprice real, rtype text, runits text, rcost real)
	#typ - flight, refuel
	c=getdbcon(conn)
	#Let's try total average gph, speed
	gals=0
	ftime=0
	dist=0
	#Ooh let's graph gph/speed vs distance too
	tgals=[0,0,0,0,0,0,0,0] #dist <50 <100 <150 <200 <250 <300 <350 >400
	tftime=[0,0,0,0,0,0,0,0]
	tdist=[0,0,0,0,0,0,0,0]
	tflts=[0,0,0,0,0,0,0,0] #and number of flights too
	aspeed=[[],[],[],[],[],[],[],[]] #for standard deviation calc
	agph=[[],[],[],[],[],[],[],[]]
	print("Getting flight logs...")
	for log in c.execute('SELECT dist, fltime, fuel FROM logs WHERE model = ? AND type = "flight" AND fuel > 0.0', (actype,)):
		gal=log[2]/3.5
		gals+=gal #For overall averages
		dist+=log[0]
		secs=logs[1].split(':')*3600+logs[1].split(':')[1]*60
		ftime+=secs
		bucket=floor(log[0]/50) #For averages per distance bucket
		if bucket>7:
			bucket=7
		tgals[bucket]+=gal
		tftime[bucket]+=secs
		tdist[bucket]+=log[0]
		tflts[bucket]+=1
		hrs=secs/3600 #Store actual values for computing standard deviation
		gph=gal/hrs
		speed=log[0]/hrs
		agph[bucket].append(gph)
		aspeed[bucket].append(speed)
	hrs=ftime/3600 #Print out the overall averages
	speed=dist/hrs
	gph=gals/hrs
	print("Stats for "+actype)
	print("-----------------------------------------")
	print("Avg speed: "+speed+" kt")
	print("Avg gph: "+gph+" gph")
	dspeed=[]
	dgph=[]
	xax=[]
	stdgph=[]
	stdspd=[]
	for i in range(8):
		hrs=tftime[i]/3600 #Compute values for the different buckets
		speed=tdist[i]/hrs
		gph=tgals[i]/hrs
		dspeed.append(speed)
		dgph.append(gph)
		idx=(i+1)*50 #Generate stuff for x axis
		val=idx-25
		if idx<7:
			lbl="<"+idx
		else:
			lbl=">"+idx
		xax.append((val,lbl))
		ssgph=0
		ssspd=0
		for j in range(tflts[i]): #Compute standard deviation
			ssgph+=math.pow(aspeed[i][j]-speed,2)
			ssspd+=math.pow(agph[i][j]-gph,2)
		stdgph.append(sqrt(ssgph/tflts[i]))
		stdspd.append(sqrt(ssspd/tflts[i]))
	print("Plotting figure for "+actype+" stats...")
	fig, ax = plt.subplots()
	# ax.plot([i[0] for i in xax], [i[0] for i in dspeed], 'o-')
	# ax.plot([i[0] for i in xax], [i[0] for i in dgph], 'o-')
	ax.errorbar([i[0] for i in xax], [i[0] for i in dspeed], yerr=stdspd, fmt='--o')
	ax.errorbar([i[0] for i in xax], [i[0] for i in dgph], yerr=stdgph, fmt='--o', c='#cc9900', ecolor='cc9900')
	ax.set_xticklabels((i[1] for i in xax))
	plt.title("Speed and gph for sector length",fontsize=12)
	plt.xlabel("Length")
	plt.ylabel("Speed/gph")
	plt.show()
	print("Plotting figure for "+actype+" distances...")
	fig, ax = plt.subplots()
	ind=([i[0]-25 for i in xax])
	width=0.35
	rects1 = ax.bar(ind, tflts, width, color='r')
	ax.set_ylabel('Flights')
	ax.set_title('Flights by sector length')
	ax.set_xticks(ind+width)
	ax.set_xticklabels( (i[1] for i in xax) )
	ax.legend( (i[1] for i in xax) )
	plt.show()

def mapcommo(type):
	if type=="fuel":
		t1="JetA Fuel"
		t2="100LL Fuel"
	elif type=="mtrl":
		t1="Supplies"
		t2="Building materials"
	else:
		print("Commodity type "+type+" not recognized!")
	if t1 is not None:
		print("Sending request for commodities...")
		commo = fserequest(1,'query=commodities&search=key','Commodity')
		print("Sorting results...")
		stuff = []
		for item in commo: #Parse commodity info
			typ = airplane.getElementsByTagName("Type")[0].firstChild.nodeValue
			if typ==t1 or typ==t2:
				loc = airplane.getElementsByTagName("Location")[0].firstChild.nodeValue
				amt = airplane.getElementsByTagName("Amount")[0].firstChild.nodeValue
				stuff.append((loc,typ,amt))
		if stuff!=[]: #Add up quantity per location
			qty=[] #List to hold quantities
			for item in stuff:
				match=-1
				i=-1
				for prev in qty:
					i+=1
					if item[0]==qty[0]: #Test if the location has already been added
						match=1
						break
				if match==-1: #If not added, then add new location/quantity
					if item[1]==t1:
						idx=0
					else: #t2
						idx=1
					qty.append([item[0],item[2].split(),idx])
				else: #If added, then sum with other quantity
					qty[i][1]+=item[2].split()
					qty[i][2]=2 #Indicates a mix of t1 and t2
			coords=getcoords(qty[:][0])
			if len(coords)==len(qty): #If not, there was some key error I guess
				locations=[]
				for i in range(len(coords)):
					locations.append([locations[i][0],locations[i][1],qty[i][1],qty[i][2]])
				mapper(type, locations, (latmin,lonmin), (latmax,lonmax), title)
		else:
			print("No "+type+" found!")

def getlistings(conn,actype,lo,hi): #Return list of time for aircraft to sell
	c=getdbcon(conn)
	d=getdbcon(conn)
	cdict=build_ctry_csv()
	rdict=dicts.getregiondict()
	listings=[]
	print("Finding sell times for: "+actype+", "+str(lo)+" to "+str(hi)+"...")
	for query in c.execute('SELECT obsiter FROM queries'):
	#serial real, type text, loc text, locname text, hours real, price real, obsiter real
		for sale in d.execute('SELECT * FROM allac WHERE obsiter = ? AND type = ? AND price BETWEEN ? AND ?', (query[0],actype,lo,hi)):
			country=cdict[sale[2]]
			region=rdict(country)
			match=0
			for i in range(len(listings)):
				if sale[0]==listings[i][0]:
					if region==listings[i][1] and sale[5]==listings[i][2]:
						listings[i][4]=query[0] #Update "to" date in current list
						match=1
					else:
						listings.remove(listings[i]) #Price/region changed, remove old listing and will append a new one
					break
			if match==0:
				listings.append([sale[0],region,int(sale[5]),query[0],query[0]]) #SN, region, price, first iter, last iter
				
	return listings

def mapaclocations(conn, actype): #Map locations of aircraft type for sale
	c=getdbcon(conn)
	iters=getmaxiter(conn)
	q1="SELECT loc FROM allac WHERE obsiter = "+str(iters) #To allow adding to query
	if actype=="":
		title="Locations of all aircraft for sale"
	else:
		q1+=" AND type = '"+actype+"'"
		title="Locations of "+actype+" for sale"
	locations=getcoords(c.execute(q1))
	mapper(what, locations, (latmin,lonmin), (latmax,lonmax), title)
	
def getcoords(data): #Get coordinates for a list of airports
	print("Building airport location dictionary from csv...")
	loc_dict=build_latlon_csv()
	print("Creating locations list...")
	locations=[]
	lat_tot=0
	lon_tot=0
	latmax,lonmax,latmin,lonmin=100,200,100,200 #garbage to signal init
#	print("Running query: "+q1)
	for row in data:
		try:
			lat,lon=loc_dict[row[0]]
		except KeyError: #Probably "Airborne"
			continue
		locations.append([lat,lon])
		lat_tot+=lat
		lon_tot+=lon
		if lat<latmin or abs(latmin)>90:
			latmin=lat
		if lat>latmax or abs(latmax)>90:
			latmax=lat
		if lon<lonmin or abs(lonmin)>180:
			lonmin=lon
		if lon>lonmax or abs(lonmax)>180:
			lonmax=lon
	pts=len(locations)
	if pts==0:
		print("No locations found!")
	#else:
		#center=(lat_tot/pts,lon_tot/pts)
	return locations
	
def plotdates(dlist,title,ylbl,sym): #Plot a list of data vs. dates
	print("Plotting figure for: "+title)
	fig, ax = plt.subplots()
	formatter=DateFormatter('%Y-%m-%d %H:%M')
	ax.xaxis.set_major_formatter(formatter)
	for data in dlist:
		if len(data)==2:
			ax.plot([date2num(i[0]) for i in data], [i[1] for i in data], sym)
		else:
			ax.errorbar([date2num(i[0]) for i in data], [i[1] for i in data], yerr=[i[2] for i in data], fmt=sym)
	formatter=DateFormatter('%Y-%m-%d')
	ax.xaxis.set_major_formatter(formatter)
	fig.autofmt_xdate()
	plt.xlim([min(date2num(i[0]) for i in dlist[0]),max(date2num(i[0]) for i in dlist[0])])
	plt.title(title,fontsize=12)
	plt.xlabel("Date")
	plt.ylabel(ylbl)
	plt.show()
	
def plotpayments(conn,fromdate,todate): #Plot payment totals per category
	c=getpaydbcon(conn)
	user=getname()
	delta=timedelta(days=1)
	fyear=int(fromdate.split('-', 2)[0])
	fmonth=int(fromdate.split('-', 2)[1])
	fday=int(fromdate.split('-', 2)[2])
	tyear=int(todate.split('-', 2)[0])
	tmonth=int(todate.split('-', 2)[1])
	tday=int(todate.split('-', 2)[2])
	fdate=date(fyear,fmonth,fday)
	tdate=date(tyear,tmonth,tday)
	rentexp, rentinc, assnmtexp, assnmtinc, pltfee, addcrewfee, gndcrewfee, bkgfee, ref100, refjet, mxexp, eqinstl, acsold, acbought, fboref100, fborefjet, fbogndcrew, fborepinc, fborepexp, fboeqpexp, fboeqpinc, ptrentinc, ptrentexp, fbosell, fbobuy, wsbuy100, wssell100, wsbuyjet, wsselljet, wsbuybld, wssellbld, wsbuysupp, wssellsupp, grpay=([[fdate,0]] for i in range(34))
	allthat=[rentexp, rentinc, assnmtexp, assnmtinc, pltfee, addcrewfee, gndcrewfee, bkgfee, ref100, refjet, mxexp, eqinstl, acsold, acbought, fboref100, fborefjet, fbogndcrew, fborepinc, fborepexp, fboeqpexp, fboeqpinc, ptrentinc, ptrentexp, fbosell, fbobuy, wsbuy100, wssell100, wsbuyjet, wsselljet, wsbuybld, wssellbld, wsbuysupp, wssellsupp, grpay]
	i=0
	print("Tallying daily payments from "+str(fdate.year)+"-"+str(fdate.month)+" to "+str(tdate.year)+"-"+str(tdate.month)+"...")
	#(date text, to text, from text, amount real, reason text, location real, aircraft real)
	while fdate <= tdate:
		fdateq=fdate.isoformat()+" 00:00:01"
		tdateq=fdate.isoformat()+" 23:59:59"
		if i>0:
			dstring=fdate
			for var in allthat:
				var.append([dstring,var[i-1][1]])
		for payment in c.execute('SELECT * FROM payments WHERE date BETWEEN ? AND ?',(fdateq,tdateq)):
			if payment[4]=="Rental of aircraft":
				if payment[2]!=user:
					rentinc[i][1]+=payment[3]
				else:
					rentexp[i][1]+=payment[3]
			elif payment[4]=="Pay for assignment":
				if payment[2]!=user:
					assnmtinc[i][1]+=payment[3]
				else:
					assnmtexp[i][1]+=payment[3]
			elif payment[4]=="Crew fee":
				addcrewfee[i][1]+=payment[3]
			elif payment[4]=="FBO ground crew fee":
				if payment[2]!=user:
					fbogndcrew[i][1]+=payment[3]
				else:
					gndcrewfee[i][1]+=payment[3]
			elif payment[4]=="Booking Fee":
				bkgfee[i][1]+=payment[3]
			elif payment[4]=="Refuelling with JetA":
				if payment[2]!=user:
					fborefjet[i][1]+=payment[3]
				else:
					refjet[i][1]+=payment[3]
			elif payment[4]=="Refuelling with 100LL":
				if payment[2]!=user:
					fboref100[i][1]+=payment[3]
				else:
					ref100[i][1]+=payment[3]
			elif payment[4]=="Aircraft maintenance":
				if payment[2]!=user:
					fborepinc[i][1]+=payment[3]
				else:
					mxexp[i][1]+=payment[3]
			elif payment[4]=="Aircraft sale":
				if payment[2]!=user:
					acsold[i][1]+=payment[3]
				else:
					acbought[i][1]+=payment[3]
			elif payment[4]=="Sale of wholesale JetA":
				if payment[2]!=user:
					wsselljet[i][1]+=payment[3]
				else:
					wsbuyjet[i][1]+=payment[3]
			elif payment[4]=="Sale of wholesale 100LL":
				if payment[2]!=user:
					wssell100[i][1]+=payment[3]
				else:
					wsbuy100[i][1]+=payment[3]
			elif payment[4]=="Sale of supplies":
				if payment[2]!=user:
					wssellsupp[i][1]+=payment[3]
				else:
					wsbuysupp[i][1]+=payment[3]
			elif payment[4]=="Sale of building materials":
				if payment[2]!=user:
					wssellbld[i][1]+=payment[3]
				else:
					wsbuybld[i][1]+=payment[3]
			elif payment[4]=="Group payment":
				if payment[2]!=user:
					grpay[i][1]+=payment[3]
				else:
					grpay[i][1]-=payment[3]
			elif payment[4]=="Pilot fee":
				if payment[2]!=user:
					pltfee[i][1]+=payment[3]
				else:
					pltfee[i][1]-=payment[3]
			elif payment[4]=="Installation of equipment in aircraft":
				if payment[2]!=user:
					fboeqpinc[i][1]+=payment[3]
				else:
					eqinstl[i][1]+=payment[3]
			else:
				print("No category found for "+payment[4])
		fdate += delta
		i += 1
	
	plotdates([refjet, addcrewfee, gndcrewfee],"Money","Money",'-')
	
def sumpayments(conn,fdate,tdate): #Plot portion of income/expense per category
	c=getpaydbcon(conn)
	#Income
	rentinc=[0,"Rental income"]
	assnmtinc=[0,"Assignment income"]
	acsold=[0,"Aircraft sold"]
	fboref100=[0,"100LL pumped"]
	fborefjet=[0,"JetA pumped"]
	fbogndcrew=[0,"Ground crew income"]
	fborepinc=[0,"Repair income"]
	fboeqpinc=[0,"Eqp instl income"]
	ptrentinc=[0,"PT rent income"]
	fbosell=[0,"FBO sold"]
	wssell100=[0,"100LL sold"]
	wsselljet=[0,"JetA sold"]
	wssellbld=[0,"Building materials sold"]
	wssellsupp=[0,"Supplies sold"]
	grpay=[0,"Group payment"]
	
	#Expenses
	rentexp=[0,"Rental expense"]
	assnmtexp=[0,"Assignment expense"]
	pltfee=[0,"Pilot fees"]
	addcrewfee=[0,"Additional crew fee"]
	gndcrewfee=[0,"Ground crew fee"]
	bkgfee=[0,"Booking fee"]
	ref100=[0,"100LL pumped"]
	refjet=[0,"JetA pumped"]
	mxexp=[0,"Maintenance"]
	eqinstl=[0,"Equipment installed"]
	acbought=[0,"Aircraft bought"]
	fborepexp=[0,"FBO repair cost"]
	fboeqpexp=[0,"FBO eqp instl"]
	fbobuy=[0,"FBO bought"]
	wsbuy100=[0,"100LL bought"]
	wsbuyjet=[0,"JetA bought"]
	wsbuybld=[0,"Building materials"]
	wsbuysupp=[0,"Supplies"]

	user=getname()
	fromdate=fdate+" 00:01"
	todate=tdate+" 23:59"
	print("Tallying payments from"+str(fdate[0])+"-"+str(fdate[1])+" to "+str(tdate[0])+"-"+str(tdate[1])+"...")
	#(date text, to text, from text, amount real, reason text, location real, aircraft real)
	for payment in c.execute('SELECT * FROM payments WHERE date BETWEEN ? AND ?',(fromdate,todate)):
		if payment[4]=="Rental of aircraft":
			if payment[2]!=user:
				rentinc[0]+=payment[3]
			else:
				rentexp[0]+=payment[3]
		elif payment[4]=="Pay for assignment":
			if payment[2]!=user:
				assnmtinc[0]+=payment[3]
			else:
				assnmtexp[0]+=payment[3]
		elif payment[4]=="Crew fee":
			addcrewfee[0]+=payment[3]
		elif payment[4]=="FBO ground crew fee":
			if payment[2]!=user:
				fbogndcrew[0]+=payment[3]
			else:
				gndcrewfee[0]+=payment[3]
		elif payment[4]=="Booking Fee":
			bkgfee[0]+=payment[3]
		elif payment[4]=="Refuelling with JetA":
			if payment[2]!=user:
				fborefjet[0]+=payment[3]
			else:
				refjet[0]+=payment[3]
		elif payment[4]=="Refuelling with 100LL":
			if payment[2]!=user:
				fboref100[0]+=payment[3]
			else:
				ref100[0]+=payment[3]
		elif payment[4]=="Aircraft maintenance":
			if payment[2]!=user:
				fborepinc[0]+=payment[3]
			else:
				mxexp[0]+=payment[3]
		elif payment[4]=="Aircraft sale":
			if payment[2]!=user:
				acsold[0]+=payment[3]
			else:
				acbought[0]+=payment[3]
		elif payment[4]=="Sale of wholesale JetA":
			if payment[2]!=user:
				wsselljet[0]+=payment[3]
			else:
				wsbuyjet[0]+=payment[3]
		elif payment[4]=="Sale of wholesale 100LL":
			if payment[2]!=user:
				wssell100[0]+=payment[3]
			else:
				wsbuy100[0]+=payment[3]
		elif payment[4]=="Sale of supplies":
			if payment[2]!=user:
				wssellsupp[0]+=payment[3]
			else:
				wsbuysupp[0]+=payment[3]
		elif payment[4]=="Sale of building materials":
			if payment[2]!=user:
				wssellbld[0]+=payment[3]
			else:
				wsbuybld[0]+=payment[3]
		elif payment[4]=="Group payment":
			if payment[2]!=user:
				grpay[0]+=payment[3]
			else:
				grpay[0]-=payment[3]
		elif payment[4]=="Pilot fee":
			if payment[2]!=user:
				pltfee[0]+=payment[3]
			else:
				pltfee[0]-=payment[3]
		elif payment[4]=="Installation of equipment in aircraft":
			if payment[2]!=user:
				fboeqpinc[0]+=payment[3]
			else:
				eqinstl[0]+=payment[3]
		else:
			print("No category found for "+payment[4])

	#Income nets per category
	rent=[rentinc[0]-rentexp[0],"Rental"]
	assnmt=[assnmtinc[0]-assnmtexp[0],"Assignments"]
	ac=[acsold[0]-acbought[0],"Aircraft"]
	ws100=[fboref100[0]+wssell100[0]-wsbuy100[0],"WS 100LL"]
	wsjet=[fborefjet[0]+wsselljet[0]-wsbuyjet[0],"WS JetA"]
	fborep=[fborepinc[0]-fborepexp[0],"FBO Repairs"]
	fboeqp=[fboeqpinc[0]-fboeqpexp[0],"FBO Eqp Instl"]
	ptrent=[ptrentinc[0],"PT Rent"]
	fbo=[fbosell[0]-fbobuy[0],"FBO"]
	sup=[wssellsupp[0]-wsbuysupp[0],"Supplies"]
	bld=[wssellbld[0]-wsbuybld[0],"Building Mtrls"]
	incnets=[rent, assnmt, ac, ws100, wsjet, fborep, fboeqp, ptrent, fbo, sup, bld]
	
	incnet=[]
	expnet=[ref100, refjet, bkgfee, gndcrewfee, addcrewfee, pltfee, mxexp] #Always negative
	netinc=0
	netexp=ref100[0]+refjet[0]+bkgfee[0]+gndcrewfee[0]+addcrewfee[0]+pltfee[0]+mxexp[0]
	for net in incnets: #Test if category represents an expense or income
		if net[0]>0:
			incnet.append(net)
			netinc+=net[0]
		else:
			expnet.append(net)
			netexp+=net[0]
	pieplot(incnet,netinc,5,"Income sources")
	pieplot(expnet,netexp,5,"Expense sources")

	#Totals income/expenses
	revs=[rentinc, assnmtinc, acsold, fboref100, fborefjet, fbogndcrew, fborepinc, fboeqpinc, ptrentinc, fbosell, wssell100, wsselljet, wssellbld, wssellsupp]
	exps=[rentexp, assnmtexp, pltfee, addcrewfee, gndcrewfee, bkgfee, ref100, refjet, mxexp, eqinstl, acbought, fborepexp, fboeqpexp, fbobuy, wsbuy100, wsbuyjet, wsbuybld, wsbuysupp]
	pieplot(revs,None,5,"Revenues")
	pieplot(exps,None,5,"Expenses")
	
def sumacpayments(conn,fdate,tdate): #Plot revenue portion by aircraft
	c=getpaydbcon(conn)
	d=getpaydbcon(conn)
	#Income
	rent=[[],"Rental income"]
	assnmtinc=[[],"Assignment income"]
		
	#Expenses
	pltfee=[[],"Pilot fees"]
	addcrewfee=[[],"Additional crew fee"]
	gndcrewfee=[[],"Ground crew fee"]
	bkgfee=[[],"Booking fee"]
	ref100=[[],"100LL pumped"]
	refjet=[[],"JetA pumped"]
	mxexp=[[],"Maintenance"]
	eqinstl=[[],"Equipment installed"]
	acbuy=[[],"Aircraft bought"]

	items=[rent,assnmtinc,pltfee,addcrewfee,gndcrewfee,bkgfee,ref100,refjet,mxexp,eqinstl,acbuy]
	
	user=getname()
	fromdate=fdate+" 00:01"
	todate=tdate+" 23:59"
	ac=[]
	i=-1
	print("Tallying payments from"+str(fdate[0])+"-"+str(fdate[1])+" to "+str(tdate[0])+"-"+str(tdate[1])+"...")
	#(date text, payto text, payfrom text, amount real, reason text, location text, aircraft text)
	for dac in c.execute('SELECT DISTINCT aircraft FROM payments WHERE date BETWEEN ? AND ? AND payto = ? AND reason = "Pay for assignment"',(fromdate,todate,user)):
		ac.append([0,dac[0]])
		for var in items:
			var[0].append(0)
		i+=1
		for payment in d.execute('SELECT * FROM payments WHERE date BETWEEN ? AND ? AND aircraft = ?',(fromdate,todate,dac[0])):
			if payment[4]=="Rental of aircraft":
				if payment[2]!=user:
					rent[0][i]+=payment[3]
				else:
					rent[0][i]-=payment[3]
			elif payment[4]=="Pay for assignment":
				if payment[2]!=user:
					assnmtinc[0][i]+=payment[3]
			elif payment[4]=="Crew fee":
				addcrewfee[0][i]-=payment[3]
			elif payment[4]=="FBO ground crew fee":
				if payment[2]==user:
					gndcrewfee[0][i]-=payment[3]
			elif payment[4]=="Booking Fee":
				bkgfee[0][i]-=payment[3]
			elif payment[4]=="Refuelling with JetA":
				if payment[2]==user:
					refjet[0][i]-=payment[3]
			elif payment[4]=="Refuelling with 100LL":
				if payment[2]==user:
					ref100[0][i]-=payment[3]
			elif payment[4]=="Aircraft maintenance":
				if payment[2]==user:
					mxexp[0][i]-=payment[3]
			elif payment[4]=="Aircraft sale":
				if payment[2]!=user:
					acbuy[0][i]+=payment[3]
				else:
					acbuy[0][i]-=payment[3]
			elif payment[4]=="Pilot fee":
				if payment[2]!=user:
					pltfee[0][i]+=payment[3]
				else:
					pltfee[0]-=payment[3]
			elif payment[4]=="Installation of equipment in aircraft":
				if payment[2]==user:
					eqinstl[0][i]-=payment[3]
			else:
				print("No category (for aircraft) found for "+payment[4])

	for i in range(len(ac)): #Sum up all categories for each aircraft
		for var in items:
			ac[i][0]+=var[0][i]
		i+=1
	pieplot(ac,None,5,"Aircraft Income")
	
def pieplot(data, total, min, stitle): #Create a pie plot
	labels=[]
	sizes=[]
	other=0
	if total is None:
		total=0
		for cat in data:
			total+=cat[0]
	for cat in data: #Convert values to a percentage of total, separate smaller categories
		cat[0]=cat[0]/total*100
		if cat[0]>min:
			labels.append(cat[1])
			sizes.append(cat[0])
		else:
			other+=cat[0]
	if other>0.1:
		sizes.append(other)
		labels.append("Other")
	# The slices will be ordered and plotted counter-clockwise.
	colors = ['yellowgreen', 'gold', 'lightskyblue', 'lightcoral']
	#explode = (0, 0.1, 0, 0) # only "explode" the 2nd slice # But I don't wanna explode...
	plt.pie(sizes, labels=labels, #colors=colors,
			autopct='%1.1f%%', shadow=True, startangle=90)
	plt.axis('equal') # Set aspect ratio to be equal so that pie is drawn as a circle.
	plt.title(stitle)
	plt.show()
	
def gettype(icao): #Return name of aircraft type or error if not found
	icaodict=dicts.getactypedict()
	try:
		if icao!="":
			actype=icaodict[icao]
		else:
			actype=""
		success=1
	except (KeyError,IndexError) as e:
		print("Name for code "+icao+" not found!")
		actype=""
		success=0
	return actype, success

def main(argv): #This is where the magic happens
	
	syntaxstring='pricelog.py -un -dmac <aircraft icao> -ft <YYYY-MM-DD> -lh <price>'
	try:
		opts, args = getopt.getopt(argv,"hund:m:a:c:f:t:l:i:pqsg:ve:x:j",["duration=","map=","average=","cheapest=","from=","to=","low=","high=","total=","commodity=","typestats="])
	except getopt.GetoptError:
		print(syntaxstring)
		sys.exit(2)
	print("Opening database...")
	conn=sqlite3.connect('/mnt/data/XPLANE10/XSDK/forsale.db')
	tot=0
	avg=0
	low=0
	dur=0
	pay=0
	ppay=0
	spay=0
	stot=0
	stat=0
	logs=0
	lowprice=0
	highprice=99999999
	fromdate="2014-01-01"
	todate="2100-12-31"
	for opt, arg in opts:
		if opt=='-h':
			print(syntaxstring)
			sys.exit()
		elif opt=='-u':
			acforsale(conn)
		elif opt=='-n':
			totals=gettotals(conn,"None",fromdate,todate)
			plotdates([totals],"Aircraft for sale","Aircraft",'o-')
		elif opt in ("-d", "--duration"):
			durtype,dur=gettype(arg)
		elif opt in ("-m", "--map"):
			maptype,domap=gettype(arg)
			mapaclocations(conn,maptype)
		elif opt in ("-f", "--from"):
			fromdate=arg
		elif opt in ("-t", "--to"):
			todate=arg
		elif opt in ("-a", "--average"):
			avgtype,avg=gettype(arg)
		elif opt in ("-c", "--cheapest"):
			lowtype,low=gettype(arg)
		elif opt in ("-l", "--low"):
			lowprice=arg
		elif opt in ("-i", "--high"):
			highprice=arg
		elif opt in ("-p", "--payments"):
			pay=1
		elif opt in ("-q", "--plotpayments"):
			ppay=1
		elif opt in ("-s", "--sumpayments"):
			spay=1
		elif opt in ("-g", "--total"):
			tottype,tot=gettype(arg)
		elif opt=="-v":
			stot=1
		elif opt in ("-e", "--commodity"):
			mapcommo(arg)
		elif opt in ("-x", "--typestats"):
			stattype,stat=gettype(arg)
		elif opt=="-j":
			logs=1

	if pay+ppay+spay+stot>0:
		conn2=sqlite3.connect('/mnt/data/XPLANE10/XSDK/payments.db')
	
	if logs+stat>0:
		conn3=sqlite3.connect('/mnt/data/XPLANE10/XSDK/flightlogs.db')

	if tot==1:
		totals=gettotals(conn,tottype,fromdate,todate)
		plotdates([totals],"Number of "+tottype+" for sale","Aircraft",'o-')
	
	if avg==1:
		averages=getaverages(conn,avgtype,fromdate,todate)
		plotdates([averages],"Average price for "+avgtype,"Price",'o-')
	
	if low==1:
		lows=getlows(conn,lowtype,fromdate,todate)
		plotdates([lows],"Lowest price for "+lowtype,"Price",'o-')
	
	if dur==1:
		listings=getlistings(conn,durtype,lowprice,highprice)
		durations=[]
		for listing in listings:
			duration=listings[4]-listings[3]
			durations.append((listings[2],duration))
			print(str(listings[2])+": "+str(duration))
		plotdates([durations],"Time to sell for "+durtype,"Days",'o-')
	
	if pay==1:
		year=fromdate.split('-', 2)[0]
		month=fromdate.split('-', 2)[1]
		logpaymonth(conn2,year,month)
		conn2.close()
	
	if ppay==1:
		plotpayments(conn2,fromdate,todate)

	if spay==1:
		sumpayments(conn2,fromdate,todate)
	
	if stot==1:
		sumacpayments(conn2,fromdate,todate)
	
	if stat==1:
		getapstats(conn3,stattype)
		
	if logs==1:
		year=fromdate.split('-', 2)[0]
		month=fromdate.split('-', 2)[1]
		loglogmonth(conn3,year,month)
		conn3.close()

	# We can also close the connection if we are done with it.
	# Just be sure any changes have been committed or they will be lost. FOREVER
	print("Finished, closing database...")
	conn.close()
	
if __name__ == "__main__":
   main(sys.argv[1:])
