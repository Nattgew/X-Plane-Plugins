#!/usr/bin/python
from xml.dom import minidom
import xml.etree.ElementTree as etree
import urllib.request, math, sys, getopt
import dicts # My script for custom dictionaries
import os, re, fileinput, csv, sqlite3
import locale, time
from datetime import timedelta, date, datetime
from mpl_toolkits.basemap import Basemap
from matplotlib.dates import DateFormatter, date2num
import matplotlib.pyplot as plt

def getkey(): #Returns API key stored in file
	with open('/mnt/data/XPLANE10/XSDK/mykey.txt', 'r') as f:
		mykey = f.readline()
		mykey=mykey.strip()
		return mykey

def getname(): #Returns username stored in file
	with open('/mnt/data/XPLANE10/XSDK/mykey.txt', 'r') as f:
		nothing = f.readline()
		myname = f.readline()
		myname=myname.strip()
		return myname

def fserequest(ra,rqst,tagname,fmt): #Requests data in format, returns list of requested tag
	if ra==1:
		rakey="&readaccesskey="+getkey()
	else:
		rakey=""
	rq = "http://server.fseconomy.net/data?userkey="+getkey()+rakey+'&format='+fmt+'&'+rqst
	print("Will make request: "+rq)
	data = urllib.request.urlopen(rq)
	if fmt=='xml':
		tags=readxml(data,tagname)
	elif fmt=='csv':
		tags=readcsv(data)
	else:
		print("Format "+fmt+" not recognized!")
		tags=[]
	return tags

def readxml(data,tagname): #Parses XML, returns list of requested tagname
	print("Parsing XML data...")
	xmldoc = minidom.parse(data)
	error = xmldoc.getElementsByTagName('Error')
	if error!=[]:
		print("Received error: "+error[0].firstChild.nodeValue)
		tags=[]
	else:
		tags = xmldoc.getElementsByTagName(tagname)
	return tags

# def readxml(data,tagname,ns): #Parses XML, returns list of requested tagname
	# print("Parsing XML data...")
	# tree = etree.parse(data)
	# root = tree.getroot()
	# error = root.findall('sfn:Error',ns)
	# if error!=[]:
		# print("Received error: "+error[0].text)
		# tags=[]
	# else:
		# tags = root.findall(tagname)
	# return tags

def readcsv(data): #Eats Gary's lunch
	print("Parsing CSV data...")
	has_header = csv.Sniffer().has_header(data.read(1024))
	data.seek(0) # rewind
	reader = csv.reader(data)
	if has_header:
		next(reader) # skip header row
	return reader

def gebtn(field,tag): #Shorter way to get tags
	try:
		tags=field.getElementsByTagName(tag)[0].firstChild.nodeValue
	except: #Borked XML, more common than you may think
		tags=""
	return tags

def getbtns(field,tags): #Shorter way to get list of tags
	vals=[]
	for tag in tags: #Converts value based on second field
		val=gebtn(field,tag[0])  #field.find(tag[0],ns).text
		if tag[1]==1:
			val=int(val)
		elif tag[1]==2:
			val=float(val)
		elif tag[1]==3:
			val=int(float(val))
		vals.append(val)
	return vals

def acforsale(conn): #Log aircraft currently for sale
	print("Sending request for sales listing...")
	airplanes = fserequest(0,'query=aircraft&search=forsale','Aircraft','xml')
	if airplanes!=[]:
		print("Recording data...")
		c=getdbcon(conn)
		count=getmaxiter(conn)+1
		now=time.strftime("%Y-%m-%d %H:%M", time.gmtime())
		row=(count, now)
		c.execute('INSERT INTO queries VALUES (?,?)',row) #Record date/time of this query
		fields=(("SerialNumber", 1), ("MakeModel", 0), ("Location", 0), ("LocationName", 0), ("AirframeTime", 0), ("SalePrice", 2))
		rows=[]
		for airplane in airplanes: #Record aircraft for sale
			row=getbtns(airplane,fields)
			row[4]=int(row[4].split(":")[0])
			row.append(count)
			rows.append(tuple(row))
		c.executemany('INSERT INTO allac VALUES (?,?,?,?,?,?,?)',rows)
		conn.commit()

def salepickens(conn): #Convert log to compact format
	print("Processing data...")
	c=getdbcon(conn)
	d=getdbcon(conn)
	rdict=dicts.getregiondict()
	now=time.strftime("%Y-%m-%d %H:%M", time.gmtime())
	c.execute('''CREATE TABLE listings
			 (serial real, type text, loc text, locname text, hours real, price real, firstiter real, lastiter real)''')
	c.execute('''CREATE INDEX idx1 ON listings(firstiter)''')
	c.execute('''CREATE INDEX idx2 ON listings(type)''')
	c.execute('''CREATE INDEX idx3 ON listings(price)''')
	c.execute('''CREATE INDEX idx4 ON listings(lastiter)''')
	for i in range(getmaxiter(conn)):
			for listing in c.execute('SELECT * FROM allac WHERE obsiter = ?',(i+1,)):
				if i>0:
					d.execute('SELECT loc FROM listings WHERE serial = ? AND price = ? AND lastiter = ?',(listing[0], listing[5], i))
					result=d.fetchone()
					if rdict[result[0]]!=rdict[listing[2]]:
						d.execute('INSERT INTO listings VALUES (?,?,?,?,?,?,?,?)',([value for value in listing],i+1))
					else:
						d.execute('UPDATE listings SET lastiter = ? WHERE serial = ? AND price = ? AND lastiter = ?',(i+1,listing[0], listing[5], i))
				else:
					d.execute('INSERT INTO listings VALUES (?,?,?,?,?,?,?,1.0)',([value for value in listing]))
				conn.commit()

def logpaymonth(conn,fromdate): #Log a month of payments
	year,month,*rest=fromdate.split('-', 2)
	print("Sending request for payment listing...")
	payments = fserequest(1,'query=payments&search=monthyear&month='+month+'&year='+year,'Payment','xml')
	if payments!=[]:
		c=getpaydbcon(conn)
		rows=[]
		fields=(("Date", 0), ("To", 0), ("From", 0), ("Amount", 2), ("Reason", 0), ("Location", 0), ("Id", 1), ("Aircraft", 0), ("Comment", 0))
		print("Recording data...")
		for payment in payments:
			row=getbtns(payment,fields)
			if row[8]=="null":
				row[8]=""
			row[0]=row[0].replace('/','-')
			rows.append(tuple(row))
		c.executemany('INSERT INTO payments VALUES (?,?,?,?,?,?,?,?,?)',rows)
		conn.commit()

def loglogmonth(conn,fromdate): #Log a month of logs
	year,month,*rest=fromdate.split('-', 2)
	print("Sending request for logs...")
	logs = fserequest(1,'query=flightlogs&search=monthyear&month='+month+'&year='+year,'FlightLog','xml')
	if logs!=[]:
		c=getlogdbcon(conn)
		rows=[]
		fields=(("Id", 1), ("Type", 0), ("Time", 0), ("Distance", 1), ("SerialNumber", 1), ("Aircraft", 0), ("MakeModel", 0), ("From", 0), ("To", 0), ("FlightTime", 0), ("Income", 2), ("PilotFee", 2), ("CrewCost", 2), ("BookingFee", 2), ("Bonus", 2), ("FuelCost", 2), ("GCF", 2), ("RentalPrice", 2), ("RentalType", 0), ("RentalUnits", 0), ("RentalCost", 2))
		print("Recording data...")
		for log in logs:
			row=getbtns(log, fields)
			row[2]=row[2].replace('/','-')
			rows.append(tuple(row))
		c.executemany('INSERT INTO logs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',rows)
		conn.commit()

def logconfigs(conn): #Update database of aircraft configs
	print("Sending request for configs...")
	configs = fserequest(1,'query=aircraft&search=configs','AircraftConfig','xml')
	if configs!=[]:
		c=getconfigdbcon(conn)
		d=getconfigdbcon(conn)
		fields=(("MakeModel", 0), ("Crew", 1), ("Seats", 1), ("CruiseSpeed", 1), ("GPH", 1), ("FuelType", 1), ("MTOW", 1), ("EmptyWeight", 1), ("Price", 3), ("Ext1", 1), ("LTip", 1), ("LAux", 1), ("LMain", 1), ("Center1", 1), ("Center2", 1), ("Center3", 1), ("RMain", 1), ("RAux", 1), ("RTip", 1), ("Ext2", 1), ("Engines", 1), ("EnginePrice", 3))
		print("Updating config data...")
		for config in configs:
			row=getbtns(config, fields)
			fcap=0
			for i in range(9,20): #Calc total fuel capacity
				fcap+=row[i]
			row.insert(20,fcap)
			c.execute('SELECT * FROM aircraft WHERE ac = ?',(row[0],)) #Get stored info for current aircraft
			current=c.fetchone()
			if current is not None and len(current)>0:
				cols=[]
				for col in c.execute('''PRAGMA table_info(aircraft)'''): #Get list of column names
					cols.append(col[1])
				for i in range(len(row)):
					if current[i]!=row[i]: #Check if field has changed
						print("Updating "+row[0]+": "+cols[i]+" "+str(current[i])+" -> "+str(row[i]))
						d.execute('UPDATE aircraft SET ? = ? WHERE ac = ?',(cols[i], current[i], row[0]))
			else:
				print("Adding new config: "+row[0])
				c.execute('INSERT INTO aircraft VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',row)
			conn.commit()
		print("Configs up to date")

def getdbcon(conn): #Get cursor for aircraft sale database
	print("Initializing sale database cursor...")
	c = conn.cursor()
	if not getdbcon.has_been_called:
		c.execute("SELECT COUNT(*) FROM sqlite_master WHERE type = 'table'")
		exist=c.fetchone()
		#print("Found " + str(exist[0]) + " tables...")
		if exist[0]==0: #Table does not exist, create table
			print("Creating tables...")
			c.execute('''CREATE TABLE allac
				 (serial real, type text, loc text, locname text, hours real, price real, obsiter real)''')
			c.execute('''CREATE TABLE queries
				 (obsiter real, qtime text)''')
			c.execute('''CREATE INDEX idx1 ON allac(obsiter)''')
			c.execute('''CREATE INDEX idx2 ON allac(type)''')
			c.execute('''CREATE INDEX idx3 ON allac(price)''')
			c.execute('''CREATE INDEX idx4 ON queries(qtime)''')
		else:
			c.execute('SELECT qtime FROM queries ORDER BY iter DESC')
			dtime=c.fetchone()
			print("Sale data last updated: "+dtime[0])
		getdbcon.has_been_called=True
	return c

def getpaydbcon(conn): #Get cursor for payment database
	#print("Initializing payment database cursor...")
	c = conn.cursor()
	if not getpaydbcon.has_been_called:
		c.execute("SELECT COUNT(*) FROM sqlite_master WHERE type = 'table'")
		exist=c.fetchone()
		if exist[0]==0: #Table does not exist, create table
			print("Creating payment tables...")
			c.execute('''CREATE TABLE payments
				 (date text, payto text, payfrom text, amount real, reason text, location text, aircraft text, pid real, comment text)''')
			c.execute('''CREATE INDEX idx1 ON payments(date)''')
		else:
			c.execute('SELECT date FROM payments ORDER BY date DESC')
			dtime=c.fetchone()
			print("Last payment data recorded: "+dtime[0])
		getpaydbcon.has_been_called=True
	return c

def getlogdbcon(conn): #Get cursor for log database
	#print("Initializing log database cursor...")
	c = conn.cursor()
	if not getlogdbcon.has_been_called:
		c.execute("SELECT COUNT(*) FROM sqlite_master WHERE type = 'table'")
		exist=c.fetchone()
		if exist[0]==0: #Table does not exist, create table
			print("Creating log database tables...")
			c.execute('''CREATE TABLE logs
				 (fid real, type text, date text, dist real, sn real, ac text, model text, dep text, arr text, fltime text, income real, pfee real, crew real, bkfee real, bonus real, fuel real, gndfee real, rprice real, rtype text, runits text, rcost real)''')
			c.execute('''CREATE INDEX idx1 ON logs(date)''')
			c.execute('''CREATE INDEX idx2 ON logs(type)''')
			c.execute('''CREATE INDEX idx3 ON logs(dist)''')
			c.execute('''CREATE INDEX idx4 ON logs(model)''')
			c.execute('''CREATE INDEX idx5 ON logs(ac)''')
		else:
			c.execute('SELECT date FROM logs ORDER BY date DESC')
			dtime=c.fetchone()
			print("Last log data recorded: "+dtime[0])
		getlogdbcon.has_been_called=True
	return c

def getconfigdbcon(conn): #Get cursor for config database
	#print("Initializing config database cursor...")
	c = conn.cursor()
	if not getconfigdbcon.has_been_called:	
		c.execute("SELECT COUNT(*) FROM sqlite_master WHERE type = 'table'")
		exist=c.fetchone()
		if exist[0]==0: #Table does not exist, create table
			print("Creating config tables...")
			c.execute('''CREATE TABLE aircraft
				 (ac text, crew real, seats real, cruise real, gph real, fuel real, mtow real, ew real, price real, ext1 real, ltip real, laux real, lmain real, c1 real, c2 real, c3 real, rmain real, raux real, rtip real, ext2 real, fcap real, eng real, engprice real)''')
			c.execute('''CREATE INDEX idx1 ON aircraft(ac)''')
			c.execute('''CREATE INDEX idx2 ON aircraft(price)''')
			c.execute('''CREATE INDEX idx3 ON aircraft(mtow)''')
			c.execute('''CREATE INDEX idx4 ON aircraft(ew)''')
			c.execute('''CREATE INDEX idx5 ON aircraft(fcap)''')
		getconfigdbcon.has_been_called=True
	return c

def getmaxiter(conn): #Return the number of latest query, which is also the number of queries (YES IT IS SHUT UP)
	c = conn.cursor()
	c.execute('SELECT iter FROM queries ORDER BY iter DESC')
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
	airplanes = fserequest(1,'query=aircraft&search=key','Aircraft','xml')
	for plane in airplanes:
		row=getbtns(plane, [("Location", 0), ("Registration", 0), ("EngineTime", 0), ("TimeLast100hr", 0)])
		#planes[reg]=(loc,eng,chk)
		print(row[1]+" at "+row[0]+"  tot: "+row[2]+"  last: "+row[3])

def jobsfrom(apts,price,pax): #High paying jobs from airports
	jobs=[]
	print("Sending request for jobs from "+apts+"...")
	assignments = fserequest(0,'query=icao&search=jobsfrom&icaos='+apts,'Assignment','xml')
	for assignment in assignments:
		jobs=jobstest(assignment,jobs,price,pax)
		global totalfrom
		totalfrom+=1
	return jobs

def jobsto(apts,price,pax): #High paying jobs to airports
	jobs=[]
	print("Sending request for jobs to "+apts+"...")
	assignments = fserequest(0,'query=icao&search=jobsto&icaos='+apts,'Assignment','xml')
	for assignment in assignments:
		jobs=jobstest(assignment,jobs,price,pax)
		global totalto
		totalto+=1
	return jobs

def jobstest(assignment,jobs,price,pax): #Only add job to array if meeting minumum pax and pay values
	pay = float(gebtn(assignment, "Pay"))
	if pay>price:
		amt = gebtn(assignment, "Amount")
		typ = gebtn(assignment, "UnitType")
		if not(int(amt)>pax and typ=="passengers"):
			#dep = gebtn(assignment, "FromIcao")
			arr = gebtn(assignment, "ToIcao")
			loc = gebtn(assignment, "Location")
			exp = gebtn(assignment, "Expires")
			jobs.append((loc,arr,amt,typ,pay,exp))
			#if dep==loc:
			#	print (amt+" "+typ+" "+dep+"-"+arr+" $"+str(int(pay))+" "+exp)
			#else:
			#	print (amt+" "+typ+" @"+loc+"-"+arr+" $"+str(int(pay))+" "+exp)
	return jobs

def paxto(apts,minpax,maxpax): #Pax jobs to airports (incl green jobs)
	print("Sending request incl pax jobs to "+apts+"...")
	assignments = fserequest(0,'query=icao&search=jobsto&icaos='+apts,'Assignment','xml')
	jobs=paxtest(assignments,minpax,maxpax,"to")
	return jobs

def paxfrom(apts,minpax,maxpax): #Pax jobs from airports (incl green jobs)
	print("Sending request incl pax jobs from "+apts+"...")
	assignments = fserequest(0,'query=icao&search=jobsfrom&icaos='+apts,'Assignment','xml')
	jobs=paxtest(assignments,minpax,maxpax,"from")
	return jobs

def paxtest(assignments,minpax,maxpax,tofrom): #Return assignments meeting min and max pax requirements
	candidates=[]
	apts={}
	jobs=[]
	for assignment in assignments:
		loc = gebtn(assignment, "Location")
		arr = gebtn(assignment, "ToIcao")
		amt = gebtn(assignment, "Amount")
		typ = gebtn(assignment, "UnitType")
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
			pay = float(gebtn(assignment, "Pay"))
			#dep = assignment, "FromIcao")[0].firstChild.nodeValue
			exp = gebtn(assignment, "Expires")
			candidates.append((loc,arr,amt,typ,pay,exp))
			try:
				tot=apts[key]
				tot+=amt
			except (KeyError,IndexError):
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
		#print(job[2]+" "+job[3]+" "+job[0]+"-"+job[1]+" $"+str(int(job[4]))+" "+str(distbwt(job[0],job[1]))+" "+job[5])
		print('%s %s %s-%s $%i %f %s' % (job[2],job[3],job[0],job[1],int(job[4]),distbwt(job[0],job[1]),job[5]))

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

def build_csv(info): #Return a dictionary of info using FSE csv file
	loc_dict = {}
	with open('/mnt/data/XPLANE10/XSDK/icaodata.csv', 'r') as f:
		out=readcsv(f)
		for row in out:
			if info=="latlon": #airport coordinates
				loc_dict[row[0]]=(float(row[1]),float(row[2])) #Code = lat, lon
			elif info=="country": #airport countries
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
	loc_dict=build_csv("latlon")
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
			jobs=jobsfrom(area,30000,8)  #30k is big, right?
		else:
			jobs=jobsto(airport,30000,8)
		printjobs(jobs,0)
		total+=len(jobs)
	word="from near" if dir==0 else "to"
	print("Found these "+str(total)+" big jobs "+word+" those airports:")

def dcoord(coord,delta,dirn): # Change coordinate by delta without exceeding a max
	if dirn=='lon':
		lmax=179.9
	else:
		lmax=89.9
	new=coord+delta
	if new<-lmax:
		new=-lmax
	elif new>lmax:
		nex=lmax
	return new

def mapper(what, points, mincoords, maxcoords, title): # Put the points on a map
	print("Mapping "+str(len(points))+" points...") #points is list of lists containing lat,lon, then possibly addtional data
	print("min: "+str(mincoords[0])+","+str(mincoords[1])+"  max: "+str(maxcoords[0])+","+str(maxcoords[1]))
	if maxcoords[1]-mincoords[1]>180 or maxcoords[0]-mincoords[0]>60: # Big spread, world with center aligned
		#print("Using world map")
		m = Basemap(projection='hammer', resolution=None, lon_0=(maxcoords[1]+mincoords[1])/2)
	else: # Center map on area
		#print("Using regional map")
		if len(points)>1:
			width=maxcoords[1]-mincoords[1]
			height=maxcoords[0]-mincoords[0]
		else: # Provide good window for plotting one point
			width=100
			height=100
		#print("Width: "+str(width)+"  Height: "+str(height))
		llclo=dcoord(mincoords[1],-0.25*width,'lon')
		llcla=dcoord(mincoords[0],-0.25*height,'lat')
		urclo=dcoord(maxcoords[1],0.25*width,'lon')
		urcla=dcoord(maxcoords[0],0.25*height,'lat')
		#print("ll="+str(llclo)+","+str(llcla)+"  ur="+str(urclo)+","+str(urcla))
		m = Basemap(projection='cyl', resolution=None, llcrnrlon=llclo, llcrnrlat=llcla, urcrnrlon=urclo, urcrnrlat=urcla)
	if what=="ac":
		if len(points) < 30: #Use awesome airplane symbol
			verts = list(zip([0.,1.,1.,10.,10.,9.,6.,1.,1.,4.,1.,0.,-1.,-4.,-1.,-1.,-5.,-9.,-10.,-10.,-1.,-1.,0.],[9.,8.,3.,-1.,-2.,-2.,0.,0.,-5.,-8.,-8.,-9.,-8.,-8.,-5.,0.,0.,-2.,-2.,-1.,3.,8.,9.])) #Supposed to be an airplane
			mk=(verts,0)
			ptsize=50
		else: #Use boring but more compact dots
			mk='o'
			ptsize=2
		print(points)
		m.shadedrelief(scale=0.2)
		x, y = m([i[1] for i in points], [i[0] for i in points])
		c='b'
		m.scatter(x,y,s=ptsize,marker=mk,c=c)
	elif what=="fuel" or what=="mtrl":
		maxsz=0
		for loc in points:
			thous=int(round(loc[2])) #Size of point will be based on fuel amount
			if thous>maxsz:
				maxsz=thous
			loc[2]=thous
		pts=[] #rows=thous, columns=colors, contents=list of points
		for i in range(maxsz+1):
			pts.append([[],[],[]]) #Add a new empty row
			for loc in points:
				if loc[2]==i+1: #If size matches, add the point
					pts[i][loc[3]].append((loc[0],loc[1]))
		for i in range(maxsz+1): #Set size/color of points
			sz=(i+1)/6 #Size based on amount
			if pts[i]!=[[],[],[]]: #Check if any list has points
				for j in range(3):
					if pts[i][j]!=[]: #Check if this list has any points
						print(pts[i][j])
						x, y = m([k[1] for k in pts[i][j]], [k[0] for k in pts[i][j]]) #Populate points
						if j==0: #Set color
							c='#cc9900'
						elif j==1:
							c='b'
						else:
							c='k'
						print(sz)
						m.scatter(x,y,s=sz,marker='o',c=c) #Plot the points with these properties
						for l in range(len(x)):
							gals=int(round(i/2.65))
							plt.text(x[l]-math.sqrt(sz/100),y[l],"~"+str(gals)+" gal",fontsize=7)
						m.shadedrelief(scale=0.2)
	plt.title(title,fontsize=12)
	plt.show()

def gettimeforsale(conn,timetype): # Get data for all ac of timetype for sale
	c=getdbcon(conn)
	d=getdbcon(conn)
	e=getdbcon(conn)
	print("Getting sales data for "+timetype+"...")
	listings=[]
	i=0
	#(serial real, type text, loc text, locname text, hours real, price real, obsiter real)
	for dac in c.execute('SELECT DISTINCT serial FROM allac WHERE type = ?',(timetype,)):
		listings.append([])
		for qp in d.execute('SELECT price, obsiter FROM allac WHERE serial = ?',(dac[0],)):
			qtime=e.execute('SELECT qtime FROM queries WHERE iter = ?',(qp[1],))
			date=getdtime(e.fetchone()[0])
			#print("AC: "+str(dac[0])+"  "+str(date)+": "+str(qp[0]))
			listings[i].append([date,int(float(qp[0]))])
		i+=1
	return listings

def gettotals(conn,actype,fr,to): #Return list of total aircraft for sale at each query time
	c=getdbcon(conn)
	d=getdbcon(conn)
	totals=[]
	print("Finding total aircraft for sale from "+fr+" to "+to+"...")
	for query in c.execute('SELECT * FROM queries WHERE qtime BETWEEN ? AND ?', (fr,to)):
		#print("Reading query "+str(query[0])+" from "+query[1])
		if actype=="aircraft":
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

def getbaseprice(actype): #Return the base price for this actype
	conn=sqlite3.connect('/mnt/data/XPLANE10/XSDK/configs.db')
	c=getconfigdbcon(conn)
	for i in range(2):
		c.execute('SELECT price FROM aircraft WHERE ac = ?',(actype,))
		price=c.fetchone()
		if price is not None:
			baseprice=price[0]+73333 #Add equipment price
			break
		elif i==1:
			baseprice=0
			break
		logconfigs(conn) #No match, try updating the configs?
	conn.close()
	return baseprice

def getdtime(strin): #Return datetime for the Y-M-D H:M input
	adate,atime=strin.split()
	year,month,day=adate.split('-', 2)
	hour,mnt=atime.split(':')
	return datetime(int(year),int(month),int(day),int(hour),int(mnt))

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

def getfuelprices(conn): #Plot fuel prices over time
	c=getpaydbcon(conn)
	print("Getting flight logs...")
	dgas=[]
	dprice=[]
	eprice=[]
	i=-1
	#(date text, payto text, payfrom text, amount real, reason text, location text, aircraft text, pid real, comment text)
	for log in c.execute('SELECT date, amount, comment FROM payments WHERE reason = "Refuelling with JetA" ORDER BY date'):
		#User ID: xxxxx Amount (gals): 428.9, $ per Gal: $3.75
		gals=float(log[2].split(':',3)[2].split(',')[0])
		pergal=float(log[2].split(':',3)[3].replace(' $',''))
		pdate=log[0].split()[0] #Get just date portion
		#print("i="+str(i)+"  len(dgas)="+str(len(dgas)))
		if len(dgas)>0 and dgas[i][0]==pdate:
			#print("Adding "+str(gals)+" gals")
			dgas[i][1]+=gals #Keep total of gallons
			dgas[i][2]+=log[1] #Keep total of money
		else:
			#print("New day with "+str(gals)+" gals")
			i+=1
			dgas.append([pdate,gals,log[1]])
		eprice.append([pdate,pergal])
	for day in dgas: #Calculate stats for each day
		avg=day[2]/day[1]
		ssprice=0
		num=0
		for price in eprice:
			if price[0]==day[0]:
				ssprice+=math.pow(price[1]-avg,2)
				num+=1
		stdev=math.sqrt(ssprice/num)
		print("New day "+day[0]+" with "+str(avg)+" per gal, sd "+str(stdev))
		dprice.append((getdtime(day[0]+" 00:01"),avg,stdev))
	return dprice

def getapstats(conn,actype): #Return something about airplane flight logs
	#(fid real, type text, time text, dist real, sn real, ac text, model text, dep text, arr text, fltime text, income real, pfee real, crew real, bkfee real, bonus real, fuel real, gndfee real, rprice real, rtype text, runits text, rcost real)
	c=getlogdbcon(conn)
	gals=0
	ftime=0
	dist=0
	tgals=[0,0,0,0,0,0,0,0] #dist <50 <100 <150 <200 <250 <300 <350 >400
	tftime=[0,0,0,0,0,0,0,0]
	tdist=[0,0,0,0,0,0,0,0]
	tflts=[0,0,0,0,0,0,0,0] #Total number of flights
	aspeed=[[],[],[],[],[],[],[],[]] #for standard deviation calc
	agph=[[],[],[],[],[],[],[],[]]
	print("Getting flight logs for "+actype+"...")
	for log in c.execute('SELECT dist, fltime, fuel FROM logs WHERE model = ? AND type = "flight" AND fuel > 0.0', (actype,)):
		#print("Found flight: "+str(log[0])+" nmi, "+log[1])
		gal=float(log[2])/3.5
		gals+=gal #For overall averages
		ldist=log[0]
		dist+=ldist
		secs=int(log[1].split(':')[0])*3600+int(log[1].split(':')[1])*60
		ftime+=secs
		bucket=math.floor(ldist/50) #For averages per distance bucket
		if bucket>7:
			bucket=7
		tgals[bucket]+=gal
		tftime[bucket]+=secs
		tdist[bucket]+=ldist
		tflts[bucket]+=1
		hrs=secs/3600 #Store actual values for computing standard deviation
		gph=gal/hrs
		speed=ldist/hrs
		agph[bucket].append(gph)
		aspeed[bucket].append(speed)
	hrs=ftime/3600 #Print out the overall averages
	speed=dist/hrs
	gph=gals/hrs
	#print("\nStats for "+actype)
	#print("-----------------------------------------")
	#print("Avg speed: "+str(int(round(speed)))+" kt")
	#print("Avg gph: "+str(int(round(gph,2)))+" gph\n")
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
			lbl="<"+str(idx)
		else:
			lbl=">"+str(idx)
		xax.append((val,lbl))
		ssgph=0
		ssspd=0
		for j in range(tflts[i]): #Compute standard deviation
			ssgph+=math.pow(aspeed[i][j]-speed,2)
			ssspd+=math.pow(agph[i][j]-gph,2)
		stdgph.append(math.sqrt(ssgph/tflts[i]))
		stdspd.append(math.sqrt(ssspd/tflts[i]))
	print("Plotting figure for "+actype+" stats...")
	fig, ax = plt.subplots()
	# ax.plot([i[0] for i in xax], [i[0] for i in dspeed], 'o-')
	# ax.plot([i[0] for i in xax], [i[0] for i in dgph], 'o-')
	ax.errorbar([i[0] for i in xax], [i for i in dspeed], yerr=stdspd, fmt='--o')
	ax.errorbar([i[0] for i in xax], [i for i in dgph], yerr=stdgph, fmt='--o', c='#cc9900', ecolor='#cc9900')
	ax.set_xticklabels([i[1] for i in xax])
	plt.title("Speed and gph for sector length - "+actype,fontsize=12)
	plt.xlabel("Length")
	plt.ylabel("Speed/gph")
	plt.show()
	print("Plotting figure for "+actype+" distances...")
	fig, ax = plt.subplots()
	ind=([i[0]-25 for i in xax])
	width=20
	rects1 = ax.bar(ind, tflts, width, color='r')
	ax.set_ylabel('Flights')
	ax.set_title('Flights by sector length - '+actype)
	print(ind)
	print(width)
	ax.set_xticks([i+width for i in ind])
	ax.set_xticklabels( [i[1] for i in xax] )
	ax.legend( (i[1] for i in xax) )
	plt.show()

def getcommo(ctype): # Adds up locations and quantities of stuff to send to the mapper
	if ctype=="fuel":
		t1="JetA Fuel"
		t2="100LL Fuel"
	elif ctype=="mtrl":
		t1="Supplies"
		t2="Building materials"
	else:
		print("Commodity type "+ctype+" not recognized!")
	if t1 is not None:
		print("Sending request for commodities...")
		commo = fserequest(1,'query=commodities&search=key','Commodity','xml')
		print("Sorting results...")
		stuff = []
		for item in commo: #Parse commodity info
			typ = gebtn(item, "Type")
			if typ==t1 or typ==t2:
				loc = gebtn(item, "Location")
				amt = gebtn(item, "Amount")
				stuff.append((loc,typ,amt))
		if stuff!=[]: #Add up quantity per location
			qty=[] #List to hold quantities and types
			for item in stuff:
				match=-1
				i=-1
				for prev in qty:
					i+=1
					if item[0]==qty[0]: #Test if the location has already been added
						match=1
						break
				if match==-1: #If location not added, then add new location/quantity
					if item[1]==t1:
						idx=0
					else: #t2
						idx=1
					qty.append([item[0],int(item[2].split()[0]),idx])
				else: #If location already added, then sum with other quantity
					qty[i][1]+=item[2].split()
					qty[i][2]=2 #Indicates a mix of t1 and t2
			coords,cmin,cmax=getcoords(i[0] for i in qty)
			if len(coords)==len(qty): #If not, there was some key error I guess
				locations=[]
				print("Working with "+str(len(coords))+" coords...")
				for i in range(len(coords)):
					print("Apending "+str(coords[i][0])+","+str(coords[i][1])+","+str(qty[i][1])+","+str(qty[i][2]))
					locations.append([coords[i][0],coords[i][1],qty[i][1],qty[i][2]])
				return locations,cmin,cmax
		else:
			print("No "+ctype+" found!")

def getlistings(conn,actype,lo,hi): #Return list of time for aircraft to sell
	c=getdbcon(conn)
	d=getdbcon(conn)
	cdict=build_csv("country")
	rdict=dicts.getregiondict()
	listings=[]
	print("Finding sell times for: "+actype+", "+str(lo)+" to "+str(hi)+"...")
	for query in c.execute('SELECT obsiter FROM queries'):
	#serial real, type text, loc text, locname text, hours real, price real, obsiter real
		for sale in d.execute('SELECT serial, loc, price FROM allac WHERE obsiter = ? AND type = ? AND price BETWEEN ? AND ?', (query[0],actype,lo,hi)):
			country=cdict[sale[1]]
			region=rdict[country]
			match=0
			for i in range(len(listings)):
				if sale[0]==listings[i][0]: #Check for matching listing
					if region==listings[i][1] and sale[2]==listings[i][2]:
						listings[i][4]=query[0] #Update "to" date in current list
						match=1
					else: #Price/region changed, assume not sold, remove old listing and will append a new one
						listings.remove(listings[i]) 
					break
			if match==0: #New/updated listing: SN, region, price, first iter, last iter
				listings.append([sale[0],region,int(sale[2]),query[0],query[0]]) 
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
	locations,cmin,cmax=getcoords([i[0] for i in c.execute(q1)])
	if len(locations)>0:
		mapper('ac', locations, cmin, cmax, title)

def getcoords(data): #Get coordinates for a list of airports
	print("Building airport location dictionary from csv...")
	loc_dict=build_csv("latlon")
	print("Creating locations list...")
	locations=[]
	#lat_tot=0
	#lon_tot=0
	latmax,lonmax,latmin,lonmin=100,200,100,200 #garbage to signal init
	for row in data:
		try:
			print(row)
			lat,lon=loc_dict[row]
		except KeyError: #Probably "Airborne"
			print("Key error on: "+str(row))
			continue
		locations.append([lat,lon])
		#lat_tot+=lat
		#lon_tot+=lon
		if lat<latmin or abs(latmin)>90: #Look for min/max of coordinates
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
		#center=(lat_tot/pts,lon_tot/pts) # Not currently used, also needs the totals above
	return locations,(latmin,lonmin),(latmax,lonmax)

def plotdates(dlist,title,ylbl,sym,clr,save): #Plot a list of data vs. dates
	if clr is None: #Allows for easy defaults I guess
		clr=['']
	if sym is None:
		sym=['-o']
	print("Plotting figure for: "+title)
	fig, ax = plt.subplots()
	formatter=DateFormatter('%Y-%m-%d %H:%M')
	ax.xaxis.set_major_formatter(formatter)
	items=len(dlist)
	syms=len(sym)
	clrs=len(clr)
	# print(sym)
	# print(clr)
	# print(items)
	i=0
	ii=1 if 2<syms<items+1 else 0 #Changes whether each plot moves down a list of symbols/colors
	j=0
	jj=1 if 2<clrs<items+1 else 0
	for data in dlist:
#		print("Iter i "+str(i)+" by "+str(ii)+"  j "+str(j)+" by "+str(jj))
		if clr[j] is None:
			clr[j]=''
		if len(data[0])==2:
			#print("Plotting data with symbol "+sym[i]+" and color "+clr[j])
			ax.plot([date2num(x[0]) for x in data], [x[1] for x in data], clr[j]+sym[i])
		else:
			ax.errorbar([date2num(x[0]) for x in data], [x[1] for x in data], yerr=[x[2] for x in data], fmt=sym[i], c=clr[j])
		if i<syms-1: #Reference next symbol/color, if one is provided for each data entry
			i+=ii
		else: #Go back to zero if reaching length of data list
			i-=i
		if j<clrs-1:
			j+=jj
		else:
			j-=j
		if items>1 and data==dlist[-2]: #If only two elements given, second is for the last dataset
			if len(sym)==2:
				i=1
			if len(clr)==2:
				j=1
	if dlist[-1][1][0]==getdtime("2100-12-31 23:59"): #Don't consider base price in range finding
		del dlist[-1]
	daterange=[min(min(date2num(i[0]) for i in j) for j in dlist),max(max(date2num(i[0]) for i in j) for j in dlist)]
	if isinstance(dlist[0][0][1], (list, tuple)):
		minprice=min(min(i[1][0] for i in j) for j in dlist)
		maxprice=max(max(i[1][0] for i in j) for j in dlist)
	else:
		minprice=min(min(i[1] for i in j) for j in dlist)
		maxprice=max(max(i[1] for i in j) for j in dlist)
	delta=maxprice-minprice
	pricerange=[minprice-0.1*delta, maxprice+0.1*delta]
	formatter=DateFormatter('%Y-%m-%d')
	ax.xaxis.set_major_formatter(formatter)
	fig.autofmt_xdate()
	plt.xlim(daterange)
	plt.ylim(pricerange)
	plt.title(title,fontsize=12)
	plt.xlabel("Date")
	plt.ylabel(ylbl)
	if save==0:
		plt.show()
	else:
		plt.savefig('/mnt/data/Dropbox/'+title.replace(' ','_')+'.png')

def plotpayments(conn,fromdate,todate): #Plot payment totals per category
	c=getpaydbcon(conn)
	user=getname()
	delta=timedelta(days=1)
	fyear,fmonth,fday=fromdate.split('-', 2)
	tyear,tmonth,tday=todate.split('-', 2)
	fdate=date(int(fyear),int(fmonth),int(fday))
	tdate=date(int(tyear),int(tmonth),int(tday))
	rentexp, rentinc, assnmtexp, assnmtinc, pltfee, addcrewfee, gndcrewfee, bkgfee, ref100, refjet, mxexp, eqinstl, acsold, acbought, fboref100, fborefjet, fbogndcrew, fborepinc, fborepexp, fboeqpexp, fboeqpinc, ptrentinc, ptrentexp, fbosell, fbobuy, wsbuy100, wssell100, wsbuyjet, wsselljet, wsbuybld, wssellbld, wsbuysupp, wssellsupp, grpay=([[fdate,0]] for i in range(34))
	allthat=[rentexp, rentinc, assnmtexp, assnmtinc, pltfee, addcrewfee, gndcrewfee, bkgfee, ref100, refjet, mxexp, eqinstl, acsold, acbought, fboref100, fborefjet, fbogndcrew, fborepinc, fborepexp, fboeqpexp, fboeqpinc, ptrentinc, ptrentexp, fbosell, fbobuy, wsbuy100, wssell100, wsbuyjet, wsselljet, wsbuybld, wssellbld, wsbuysupp, wssellsupp, grpay]
	categories=[("Rental of aircraft", rentinc, rentexp),
				("Pay for assignment", assnmtinc, assnmtexp),
				("Crew fee", addcrewfee, addcrewfee),
				("FBO ground crew fee", fbogndcrew, gndcrewfee),
				("Booking Fee", bkgfee, bkgfee),
				("Refuelling with JetA", fborefjet, refjet),
				("Refuelling with 100LL", fboref100, ref100),
				("Aircraft maintenance", fborepinc, mxexp),
				("Aircraft sale", acsold, acbought),
				("Sale of wholesale JetA", wsselljet, wsbuyjet),
				("Sale of wholesale 100LL", wssell100, wsbuy100),
				("Sale of supplies", wssellsupp, wsbuysupp),
				("Sale of building materials", wssellbld, wsbuybld),
				("Group payment", grpay, grpay),
				("Pilot fee", pltfee, pltfee),
				("Installation of equipment in aircraft", fboeqpinc, eqinstl)]
	i=0
	print('Tallying daily payments from %i-%i to %i-%i...' % (fdate.year,fdate.month,tdate.year,tdate.month))
	#(date text, to text, from text, amount real, reason text, location real, aircraft real)
	while fdate <= tdate:
		fdateq=fdate.isoformat()+" 00:00:01" #To match logged format
		tdateq=fdate.isoformat()+" 23:59:59"
		if i>0:
			for var in allthat:
				var.append([fdate,var[i-1][1]]) #Carry over the previous totals to new date
		for payment in c.execute('SELECT payfrom, amount, reason FROM payments WHERE date BETWEEN ? AND ?',(fdateq,tdateq)):
			for cat in categories:
				if payment[2]==cat[0]: #Test if category matches
					if payment[0]!=user: #If payment not from user
						cat[1][i][1]+=payment[1]
					else:
						cat[2][i][1]+=payment[1]
					break
		fdate += delta
		i += 1
	plotdates([refjet, addcrewfee, gndcrewfee],"Money","Money",['-'],None,0)

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
	categories=[("Rental of aircraft", rentinc, rentexp), #Tag name, if to, if from
				("Pay for assignment", assnmtinc, assnmtexp),
				("Crew fee", addcrewfee, addcrewfee),
				("FBO ground crew fee", fbogndcrew, gndcrewfee),
				("Booking Fee", bkgfee, bkgfee),
				("Refuelling with JetA", fborefjet, refjet),
				("Refuelling with 100LL", fboref100, ref100),
				("Aircraft maintenance", fborepinc, mxexp),
				("Aircraft sale", acsold, acbought),
				("Sale of wholesale JetA", wsselljet, wsbuyjet),
				("Sale of wholesale 100LL", wssell100, wsbuy100),
				("Sale of supplies", wssellsupp, wsbuysupp),
				("Sale of building materials", wssellbld, wsbuybld),
				("Group payment", grpay, grpay),
				("Pilot fee", pltfee, pltfee),
				("Installation of equipment in aircraft", fboeqpinc, eqinstl)]
	user=getname()
	fromdate=fdate+" 00:01"
	todate=tdate+" 23:59"
	print("Tallying payments from"+str(fdate[0])+"-"+str(fdate[1])+" to "+str(tdate[0])+"-"+str(tdate[1])+"...")
	#(date text, to text, from text, amount real, reason text, location real, aircraft real)
	for payment in c.execute('SELECT payfrom, amount, reason FROM payments WHERE date BETWEEN ? AND ?',(fromdate,todate)):
		for cat in categories:
			if payment[2]==cat[0]:
				if payment[0]!=user:
					cat[1][0]+=payment[1]
				else:
					cat[2][0]+=payment[1]
				break
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
	z=[[],""]
	items=[rent,assnmtinc,pltfee,addcrewfee,gndcrewfee,bkgfee,ref100,refjet,mxexp,eqinstl,acbuy,z]
	categories=[("Rental of aircraft", rent, rent),
				("Pay for assignment", assnmtinc, z),
				("Crew fee", addcrewfee, addcrewfee),
				("FBO ground crew fee", z, gndcrewfee),
				("Booking Fee", z, bkgfee),
				("Refuelling with JetA", z, refjet),
				("Refuelling with 100LL", z, ref100),
				("Aircraft maintenance", z, mxexp),
				("Aircraft sale", acbuy, acbuy),
				("Pilot fee", pltfee, pltfee),
				("Installation of equipment in aircraft", z, eqinstl)]
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
			var[0].append(0) # Initialize with 0 values for this aircraft
		i+=1
		for payment in d.execute('SELECT payfrom, amount, reason FROM payments WHERE date BETWEEN ? AND ? AND aircraft = ?',(fromdate,todate,dac[0])):
			for cat in categories:
				if payment[2]==cat[0]:
					if payment[0]!=user:
						cat[1][0][i]+=payment[1]
					else:
						cat[2][0][i]-=payment[1]
					break
	for i in range(len(ac)): #Sum up all categories for each aircraft
		for var in items:
			ac[i][0]+=var[0][i]
		ac[i][0]-=z[0][i] #z is for garbage, take this back out
		i+=1
	pieplot(ac,None,5,"Aircraft Income")

def pieplot(data, total, min, stitle): #Create a pie plot
	labels=[]
	sizes=[]
	other=0
	if total is None: #Calc total if not given
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
	actype="aircraft"
	try:
		if icao!="":
			actype=icaodict[icao]
		success=True
	except (KeyError,IndexError):
		print("Name for code "+icao+" not found!")
		success=False
	return actype, success

def main(argv): #This is where the magic happens
	syntaxstring='pricelog.py -acdgmx <aircraft> -bhjknpqsuvz -e <fuel/mtrls> -ft <YYYY-MM-DD> -il <price>'
	try: #_____________no__r________
		opts, args = getopt.getopt(argv,"a:bc:d:e:f:g:hi:jkl:m:pqst:uvwx:y:z",["duration=","map=","average=","cheapest=","from=","to=","low=","high=","total=","commodity=","typestats=","timeforsale="])
	except getopt.GetoptError:
		print(syntaxstring)
		sys.exit(2)
	tot, avg, low, dur, pay, ppay, spay, stot, stat, logs, com, lowprice, fuel, domap, sale, tots, pout, tfs=(False,)*18
	getdbcon.has_been_called=False #To know when it's the first cursor initialized
	getpaydbcon.has_been_called=False
	getlogdbcon.has_been_called=False
	getconfigdbcon.has_been_called=False
	highprice=99999999
	fromdate="2014-01-01"
	todate="2020-12-31"
	for opt, arg in opts:
		if opt in ("-a", "--average"): #Plots average prices for type
			avgtype,avg=gettype(arg)
		elif opt=="-b": #Logs a month of flight logs, based on the date given
			logs=True
		elif opt in ("-c", "--cheapest"): #Plots the cheapest aircraft of this type
			lowtype,low=gettype(arg)
		elif opt in ("-d", "--duration"): #Calculates duration to sell for a type (in work)
			durtype,dur=gettype(arg)
		elif opt in ("-e", "--commodity"): #Maps locations and amounts of commodities
			locations,cmin,cmax=getcommo(arg)
			mapper(arg, locations, cmin, cmax, "Locations of Commodities")
		elif opt in ("-f", "--from"): #First date to be used in different functions
			fromdate=arg
		elif opt in ("-g", "--total"): #Plots total aircraft of this type for sale
			tottype,tot=gettype(arg)
		elif opt=='-h': #plshelp
			print(syntaxstring)
			sys.exit()
		elif opt in ("-i", "--high"): #Highest price to be considered in other functions
			highprice=arg
		elif opt=="-j": #Plots fuel prices, averaged for each day
			fuel=True
		elif opt=="-k": #Updates the configuration database
			cconn=sqlite3.connect('/mnt/data/XPLANE10/XSDK/configs.db')
			logconfigs(cconn)
			cconn.close()
		elif opt in ("-l", "--low"): #Lowest price to be considered in other functions
			lowprice=arg
		elif opt in ("-m", "--map"): #Map locations of a type for sale
			maptype,domap=gettype(arg)
		elif opt=="-p": #Log a month of payments based on the date given
			pay=True
		elif opt=="-q": #Plots payment totals over date range
			ppay=True
		elif opt=="-s": #Plots payment percentage per category
			spay=True
		elif opt in ("-t", "--to"): #Last date to be used in different functions
			todate=arg
		elif opt=='-u': #Logs the aircraft currently for sale
			sale=True
		elif opt=="-v": #Plots the percentages of payment categories per aircraft
			stot=True
		elif opt=="-w": #Saves plots for aircraft specified in a file
			pout=True
		elif opt in ("-x", "--typestats"): #Plots stats for given type
			stattype,stat=gettype(arg)
		elif opt in ("-y", "--timeforsale"): #Plots sale prices per aircraft over time
			timetype,tfs=gettype(arg)
		elif opt=="-z": #Temporary - Adds comments to a month of payment logs
			com=True
	print("Running option...")
	if True in (pay, ppay, spay, stot, com, fuel):
		conn=sqlite3.connect('/mnt/data/XPLANE10/XSDK/payments.db')
		if pay:
			logpaymonth(conn,fromdate)
		if ppay:
			plotpayments(conn,fromdate,todate)
		if spay:
			sumpayments(conn,fromdate,todate)
		if stot:
			sumacpayments(conn,fromdate,todate)
		if com:
			logpaymonthcom(conn,fromdate)
		if fuel:
			prices=getfuelprices(conn)
			plotdates([prices],"Average fuel price","Price",['o-'],None,0)
		conn.close()
	
	if True in (logs, stat):
		conn=sqlite3.connect('/mnt/data/XPLANE10/XSDK/flightlogs.db')
		if stat:
			getapstats(conn,stattype)
		if logs:
			loglogmonth(conn,fromdate)
		conn.close()
	
	if True in (tot, avg, low, dur, domap, sale, tots, pout, tfs):
		conn=sqlite3.connect('/mnt/data/XPLANE10/XSDK/forsale.db')
		if domap:
			mapaclocations(conn,maptype)
		if sale:
			acforsale(conn)
		if tfs:
			times=gettimeforsale(conn,timetype)
			bprice=getbaseprice(timetype)
			times.append([[getdtime("2014-01-01 00:01"),bprice],[getdtime("2100-12-31 23:59"),bprice]])
			plotdates(times,"Prices of "+timetype,"Price",['o-','--'],[None,'r'],0)
		if tot:
			totals=gettotals(conn,tottype,fromdate,todate)
			plotdates([totals],"Number of "+tottype+" for sale","Aircraft",['o-'],None,0)
		if avg:
			averages=getaverages(conn,avgtype,fromdate,todate)
			bprice=getbaseprice(avgtype)
			baseprice=[[getdtime("2014-01-01 00:01"),bprice],[getdtime("2100-12-31 23:59"),bprice]] #Ensure it covers the whole range
			plotdates([averages,baseprice],"Average price for "+avgtype,"Price",['o-','--'],['b','r'],0)
		if low:
			lows=getlows(conn,lowtype,fromdate,todate)
			bprice=getbaseprice(lowtype)
			baseprice=[[getdtime("2014-01-01 00:01"),bprice],[getdtime("2100-12-31 23:59"),bprice]]
			plotdates([lows,baseprice],"Lowest price for "+lowtype,"Price",['o-','--'],['b','r'],0)
		if dur:
			listings=getlistings(conn,durtype,lowprice,highprice)
			durations=[]
			for listing in listings:
				duration=listings[4]-listings[3]
				durations.append((listings[2],duration))
				print(str(listings[2])+": "+str(duration))
			plotdates([durations],"Time to sell for "+durtype,"Days",['o-'],None,0)
		if pout:
			actypes=[]
			with open('/mnt/data/XPLANE10/XSDK/dailytypes.txt', 'r') as f:
				for actype in f:
					actype=actype.strip()
					print("Saving figure for "+actype)
					ptype,ret=gettype(actype)
					if ret:
						lows=getlows(conn,ptype,fromdate,todate)
						bprice=getbaseprice(ptype)
						baseprice=[[getdtime("2014-01-01 00:01"),bprice],[getdtime("2100-12-31 23:59"),bprice]]
						plotdates([lows,baseprice],"Lowest price for "+ptype,"Price",['o-','--'],['b','r'],1)
		conn.close()
	print("Finished!")

if __name__ == "__main__":
   main(sys.argv[1:])
