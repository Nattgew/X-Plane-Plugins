#!/usr/bin/python
from xml.dom import minidom
import urllib.request
import math
import os, re, fileinput, csv, sqlite3
import locale, time
import sys, getopt
import dicts
from datetime import timedelta, date
from mpl_toolkits.basemap import Basemap
from matplotlib.dates import DateFormatter
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

def fserequest(rqst,tagname):
	data = urllib.request.urlopen('http://server.fseconomy.net/data?userkey='+getkey()+'&format=xml&'+rqst)
	print("Parsing data...")
	xmldoc = minidom.parse(data)
	error = xmldoc.getElementsByTagName('Error')
	if error!=[]:
		print("Received error: "+error[0].firstChild.nodeValue)
		tags=[]
	else:
		tags = xmldoc.getElementsByTagName(tagname)
	return tags

def acforsale(conn):
	print("Sending request for sales listing...")
	airplanes = fserequest('query=aircraft&search=forsale','Aircraft')
	print("Recording data...")
	c=getdbcon(conn)
	count=getmaxiter(conn)
	count+=1
	now=time.strftime("%Y-%m-%d %H:%M", time.gmtime())
	row=(count, now)
	c.execute('INSERT INTO queries VALUES (?,?);',row)
	for airplane in airplanes:
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

def logpaymonth(conn,year,month):
	print("Sending requrest for payment listing...")
	payments = fserequest('query=payments&search=monthyear&readaccesskey='+getkey()+'&month='+month+'&year='+year)
	print("Recording data...")
	c=getpaydbcon(conn)
	for payment in payments:
		date = payment.getElementsByTagName("Date")[0].firstChild.nodeValue
		to = payment.getElementsByTagName("To")[0].firstChild.nodeValue
		fr = payment.getElementsByTagName("From")[0].firstChild.nodeValue
		amt = float(payment.getElementsByTagName("Amount")[0].firstChild.nodeValue)
		rsn = payment.getElementsByTagName("Reason")[0].firstChild.nodeValue
		loc = payment.getElementsByTagName("Location")[0].firstChild.nodeValue
		ac = payment.getElementsByTagName("Aircraft")[0].firstChild.nodeValue
		row=(date, to, fr, amt, rsn, loc, ac)
		c.execute('INSERT INTO payments VALUES (?,?,?,?,?,?,?);',row)
	conn.commit()

def getdbcon(conn):
	print("Initializing database cursor...")
	c = conn.cursor()
	c.execute("select count(*) from sqlite_master where type = 'table';")
	exist=c.fetchone()
	#print("Found " + str(exist[0]) + " tables...")
	if  exist[0]== 0:
		print("Creating tables...")
		c.execute('''CREATE TABLE allac
			 (serial real, type text, loc text, locname text, hours real, price real, obsiter real)''')
		c.execute('''CREATE TABLE queries
			 (obsiter real, qtime text)''')
		conn.commit()
	return c
	
def getpaydbcon(conn):
	print("Initializing payment database cursor...")
	c = conn.cursor()
	c.execute("select count(*) from sqlite_master where type = 'table';")
	exist=c.fetchone()
	#print("Found " + str(exist[0]) + " tables...")
	if  exist[0]== 0:
		print("Creating tables...")
		c.execute('''CREATE TABLE payments
			 (date text, to text, from text, amount real, reason text, location real, aircraft real)''')
		conn.commit()
	return c
	
def getmaxiter(conn):
	c = conn.cursor()
	c.execute('SELECT iter FROM queries ORDER BY iter DESC;')
	count=c.fetchone()
	#print("Found "+str(count)+" previous queries")
	if count is not None:
		current=int(count[0])
	else:
		current=0
	return current

def dudewheresmyairplane():
	#planes={}
	print("Sending request for aircraft list...")
	airplanes = fserequest('query=aircraft&search=key&readaccesskey='+getkey(),'Aircraft')
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
	assignments = fserequest('query=icao&search=jobsfrom&icaos='+apts,'Assignment')
	for assignment in assignments:
		jobs=jobstest(assignment,jobs,price,pax)
		global totalfrom
		totalfrom+=1
	return jobs

def jobsto(apts,price,pax): #High paying jobs to airports
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

def paxto(apts,minpax,maxpax): #Pax jobs to airports (incl green jobs)
	print("Sending request incl pax jobs to "+apts+"...")
	assignments = fserequest('query=icao&search=jobsto&icaos='+apts,'Assignment')
	jobs=paxtest(assignments,minpax,maxpax,"to")
	return jobs

def paxfrom(apts,minpax,maxpax): #Pax jobs from airports (incl green jobs)
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
		print(job[2]+" "+job[3]+" "+job[0]+"-"+job[1]+" $"+str(int(job[4]))+" "+str(distbwt(job[0],job[1]])+" "+job[5])

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
			#print("Dist from "+str(clat)+" "+str(clon)+" to "+str(coords[0])+" "+str(coords[1]])
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
	
def mapper(points, mincoords, maxcoords, title): # Put the points on a map, color by division
	print("Mapping points...")
	if maxcoords[1]-mincoords[1]>180 or maxcoords[0]-mincoords[0]>60: # World with center aligned
		m = Basemap(projection='hammer',lon_0=(maxcoords[1]+mincoords[1])/2)
	else: # Center map on area
		width=maxcoords[1]-mincoords[1]
		height=maxcoords[0]-mincoords[0]
		m = Basemap(projection='cyl', resolution=None, llcrnrlon=mincoords[1]-0.1*width, llcrnrlat=mincoords[0]-0.1*height, urcrnrlon=maxcoords[1]+0.1*width, urcrnrlat=maxcoords[0]+0.1*height)
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
	plt.title(title,fontsize=12)
	plt.show()

def gettotals(conn,fr,to):
	c=getdbcon(conn)
	totals=[]
	print("Finding total aircraft for sale from "+fr+" to "+to+"...")
	for query in c.execute('SELECT * FROM queries WHERE qtime BETWEEN ? AND ?', (fr,to)):
		print("Reading query "+str(query[0])+" from "+query[1])
		c.execute('SELECT COUNT(*) FROM allac WHERE obsiter = ?', (query[0],))
		total=int(c.fetchone()[0])
		totals.append((query[1],total))
	return totals

def getaverages(conn,actype,fr,to):
	c=getdbcon(conn)
	averages=[]
	print("Finding averages for: "+actype+"...")
	for query in c.execute('SELECT * FROM queries WHERE qtime BETWEEN ? AND ?', (fr,to)):
		numforsale=0
		totalprice=0
		for sale in c.execute('SELECT price FROM allac WHERE obsiter = ? AND type = ?', (query[0],actype)):
			totalprice+=int(sale[0])
			numforsale+=1
		if numforsale>0:
			avg=totalprice/numforsale
			averages.append((query[1],avg))
			print("Average is "+str(avg))
	return averages

def getlows(conn,actype,fr,to):
	c=getdbcon(conn)
	lows=[]
	print("Finding low low prices for: "+actype+"...")
	for query in c.execute('SELECT * FROM queries WHERE qtime BETWEEN ? AND ?', (fr,to)):
		c.execute('SELECT price FROM allac WHERE obsiter = ? AND type = ? ORDER BY price', (query[0],actype))
		#'SELECT price FROM allac WHERE sto > ? AND s sfrom < ?', (fr,to)
		price=c.fetchone()
		if price is not None:
			lows.append((query[1],int(price[0])))
	return lows

def getlistings(conn,actype,lo,hi):
	c=getdbcon(conn)
	rdict=dicts.getregiondict()
	listings=[]
	print("Finding sell times for: "+actype+", "+str(lo)+" to "+str(hi)+"...")
	for query in c.execute('SELECT * FROM queries'):
	#serial real, type text, loc text, locname text, hours real, price real, obsiter real
		for sale in c.execute('SELECT * FROM allac WHERE obsiter = ? AND type = ? AND price BETWEEN ? AND ?', (query[0],actype,lo,hi)):
			region=rdict(sale[2])
			match=0
			for i in range(len(listings)):
				if sale[0]==listings[i][0] and region==listings[i][1] and sale[5]==listings[i][2]:
					listings[i][4]=query[0]
					match=1
					break
			if match==0:
				listings.append((sale[0],region,int(sale[5]),query[0],query[0]))
				
	return listings
	
def maplocations(conn,actype):
	c=getdbcon(conn)
	print("Building airport location dictionary from csv...")
	loc_dict=build_csv()
	print("Creating locations list...")
	locations=[]
	lat_tot=0
	lon_tot=0
	iters=getmaxiter(conn)
	latmax,lonmax,latmin,lonmin=100,200,100,200 #garbage to signal init
	q1="SELECT loc FROM allac WHERE obsiter = "+str(iters)
	if actype=="":
		title="Locations of all aircraft for sale"
	else:
		q1+=" AND type = '"+actype+"'"
		title="Locations of "+actype+" for sale"
#	print("Running query: "+q1)
	for row in c.execute(q1):
		try:
			lat,lon=loc_dict[row[0]]
		except KeyError: #Probably "Airborne"
			continue
		locations.append((lat,lon))
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
	if pts>0:
		center=(lat_tot/pts,lon_tot/pts)
		mapper(locations, (latmin,lonmin), (latmax,lonmax), title)
	else:
		print("No locations found for: "+actype)

def plotdates(data,title,ylbl):
	print("Plotting figure for: "+title)
	fig, ax = plt.subplots()
	formatter=DateFormatter('%Y-%m-%d %H:%M')
	ax.xaxis.set_major_formatter(formatter)
	print("Attempting to plot the following "+str(len(data))+" dates:")
	for date in [i[0] for i in data]:
		print(date)
	ax.plot([i[0] for i in data], [i[1] for i in data], 'o-')
	fig.autofmt_xdate()
	plt.title(title,fontsize=12)
	plt.xlabel("Date")
	plt.ylabel(ylbl)
	plt.show()

def plotpayments(conn,fdate,tdate):
	c=getpaydbcon(conn)
	rentexp, rentinc, assnmtexp, assnmtinc, pltfees, addcrewfee, gndcrewfee, bkgfee, ref100, refjet, mxexp, eqinstl, acsold, acbought, fboref100, fborefjet, fbogndcrew, fborepinc, fborepexp, fboeqpexp, fboeqpinc, ptrentinc, ptrentexp, fbosell, fbobuy, wsbuy100, wssell100, wsbuyjet, wsselljet, wsbuybld, wssellbld, wsbuysupp, wssellsupp, grpay=([fdate,0] for i in range(35))
	allthat=[rentexp, rentinc, assnmtexp, assnmtinc, pltfees, addcrewfee, gndcrewfee, bkgfee, ref100, refjet, mxexp, eqinstl, acsold, acbought, fboref100, fborefjet, fbogndcrew, fborepinc, fborepexp, fboeqpexp, fboeqpinc, ptrentinc, ptrentexp, fbosell, fbobuy, wsbuy100, wssell100, wsbuyjet, wsselljet, wsbuybld, wssellbld, wsbuysupp, wssellsupp, grpay]
	# In case my understanding of variables has a fatal flaw
	# rentexp=[[fdate,0]]
	# rentinc=[[fdate,0]]
	# assnmtexp=[[fdate,0]]
	# assnmtinc=[[fdate,0]]
	# pltfees=[[fdate,0]]
	# addcrewfee=[[fdate,0]]
	# gndcrewfee=[[fdate,0]]
	# bkgfee=[[fdate,0]]
	# ref100=[[fdate,0]]
	# refjet=[[fdate,0]]
	# mxexp=[[fdate,0]]
	# eqinstl=[[fdate,0]]
	# acsold=[[fdate,0]]
	# acbought=[[fdate,0]]
	# fboref100=[[fdate,0]]
	# fborefjet=[[fdate,0]]
	# fbogndcrew=[[fdate,0]]
	# fborepinc=[[fdate,0]]
	# fborepexp=[[fdate,0]]
	# fboeqpexp=[[fdate,0]]
	# fboeqpinc=[[fdate,0]]
	# ptrentinc=[[fdate,0]]
	# ptrentexp=[[fdate,0]]
	# fbosell=[[fdate,0]]
	# fbobuy=[[fdate,0]]
	# wsbuy100=[[fdate,0]]
	# wssell100=[[fdate,0]]
	# wsbuyjet=[[fdate,0]]
	# wsselljet=[[fdate,0]]
	# wsbuybld=[[fdate,0]]
	# wssellbld=[[fdate,0]]
	# wsbuysupp=[[fdate,0]]
	# wssellsupp=[[fdate,0]]
	# grpay=[[fdate,0]]
	
	delta=datetime.timedelta(days=1)
	i=0
	print("Tallying daily payments from"+str(fdate[0])+"-"+str(fdate[1])+" to "+str(tdate[0])+"-"+str(tdate[1])+"...")
	#(date text, to text, from text, amount real, reason text, location real, aircraft real)
	while fdate <= todate:
		fromdate=fdate+" 00:01"
		todate=fdate+" 23:59"
		if i>0 then:
			for var in allthat:
				var.add([fdate,var[i-1][1]])
			# In case my understanding of variables has a fatal flaw
			# rentexp.add([fdate,rentexp[i-1][1]])
			# rentinc.add([fdate,rentinc[i-1][1]])
			# assnmtexp.add([fdate,assnmtexp[i-1][1]])
			# assnmtinc.add([fdate,assnmtinc[i-1][1]])
			# pltfees.add([fdate,pltfees[i-1][1]])
			# addcrewfee.add([fdate,addcrewfee[i-1][1]])
			# gndcrewfee.add([fdate,gndcrewfee[i-1][1]])
			# bkgfee.add([fdate,bkgfee[i-1][1]])
			# ref100.add([fdate,ref100[i-1][1]])
			# refjet.add([fdate,refjet[i-1][1]])
			# mxexp.add([fdate,mxexp[i-1][1]])
			# eqinstl.add([fdate,eqinstl[i-1][1]])
			# acsold.add([fdate,acsold[i-1][1]])
			# acbought.add([fdate,acbought[i-1][1]])
			# fboref100.add([fdate,fboref100[i-1][1]])
			# fborefjet.add([fdate,fborefjet[i-1][1]])
			# fbogndcrew.add([fdate,fbogndcrew[i-1][1]])
			# fborepinc.add([fdate,fborepinc[i-1][1]])
			# fborepexp.add([fdate,fborepexp[i-1][1]])
			# fboeqpexp.add([fdate,fboeqpexp[i-1][1]])
			# fboeqpinc.add([fdate,fboeqpinc[i-1][1]])
			# ptrentinc.add([fdate,ptrentinc[i-1][1]])
			# ptrentexp.add([fdate,ptrentexp[i-1][1]])
			# fbosell.add([fdate,fbosell[i-1][1]])
			# fbobuy.add([fdate,fbobuy[i-1][1]])
			# wsbuy100.add([fdate,wsbuy100[i-1][1]])
			# wssell100.add([fdate,wssell100[i-1][1]])
			# wsbuyjet.add([fdate,wsbuyjet[i-1][1]])
			# wsselljet.add([fdate,wsselljet[i-1][1]])
			# wsbuybld.add([fdate,wsbuybld[i-1][1]])
			# wssellbld.add([fdate,wssellbld[i-1][1]])
			# wsbuysupp.add([fdate,wsbuysupp[i-1][1]])
			# wssellsupp.add([fdate,wssellsupp[i-1][1]])
			# grpay.add([fdate,grpay[i-1][1]])

		for payment in c.execute('SELECT * FROM payments WHERE date BETWEEN ? AND ?',(fromdate,todate)):
			if payment[4]=="Rental of aircraft":
				if payment[2]==user:
					rentinc[i][1]+=payment[3]
				else:
					rentexp[i][1]+=payment[3]
			elif payment[4]=="Pay for assignment":
				if payment[2]==user:
					assnmtinc[i][1]+=payment[3]
				else:
					assnmtexp[i][1]+=payment[3]
			elif payment[4]=="Crew fee":
				addcrewfee+=payment[3]
			elif payment[4]=="FBO ground crew fee":
				if payment[2]==user:
					fbogndcrew[i][1]+=payment[3]
				else:
					gndcrewfee[i][1]+=payment[3]
			elif payment[4]=="Booking Fee":
				bkgfee[i][1]+=payment[3]
			elif payment[4]=="Refuelling with JetA":
				if payment[2]==user:
					fborefjet[i][1]+=payment[3]
				else:
					refjet[i][1]+=payment[3]
			elif payment[4]=="Refuelling with 100LL":
				if payment[2]==user:
					fboref100[i][1]+=payment[3]
				else:
					ref100[i][1]+=payment[3]
			elif payment[4]=="Aircraft maintenance":
				if payment[2]==user:
					fborepinc[i][1]+=payment[3]
				else:
					mxexp[i][1]+=payment[3]
			elif payment[4]=="Aircraft sale":
				if payment[2]==user:
					acsold[i][1]+=payment[3]
				else:
					acbought[i][1]+=payment[3]
			elif payment[4]=="Sale of wholesale JetA":
				if payment[2]==user:
					wsselljet[i][1]+=payment[3]
				else:
					wsbuyjet[i][1]+=payment[3]
			elif payment[4]=="Sale of wholesale 100LL":
				if payment[2]==user:
					wssell100[i][1]+=payment[3]
				else:
					wsbuy100[i][1]+=payment[3]
			elif payment[4]=="Sale of supplies":
				if payment[2]==user:
					wssellsupp[i][1]+=payment[3]
				else:
					wsbuysupp[i][1]+=payment[3]
			elif payment[4]=="Sale of building materials":
				if payment[2]==user:
					wssellbld[i][1]+=payment[3]
				else:
					wsbuybld[i][1]+=payment[3]
			elif payment[4]=="Group payment":
				if payment[2]==user:
					grpay[i][1]+=payment[3]
				else:
					grpay[i][1]-=payment[3]
			else:
				print("No category found for "+payment[4])
		fdate += delta
		i += 1
	
	title="Money Stuff"
	ylbl="Money"
	print("Plotting figure for: "+title)
	fig, ax = plt.subplots()
	formatter=DateFormatter('%Y-%m-%d %H:%M')
	ax.xaxis.set_major_formatter(formatter)
	for data in allthat:
		print("Attempting to plot the following "+str(len(data))+" dates:")
		for date in [i[0] for i in data]:
			print(date)
		ax.plot([i[0] for i in data], [i[1] for i in data], 'o-')
	fig.autofmt_xdate()
	plt.title(title,fontsize=12)
	plt.xlabel("Date")
	plt.ylabel(ylbl)
	plt.show()

def sumpayments(conn,fdate,tdate):
	c=getpaydbcon(conn)
	#Income
	rentinc=[0,"Rental income"]
	assnmtinc=[0,"Assignment income"]
	acsold=[0,"Aircraft sold"]
	fboref100=[0,"100LL pumped"]
	fborefjet=[0,"JetA pumped"]
	fbogndcrew=[0,"Ground crew income"]
	fborepinc[0,"Repair income"]
	fboeqpinc[0,"Eqp instl income"]
	ptrentinc=[0,"PT rent income"]
	fbosell=[0,"FBO sold"]
	wssell100=[0,"100LL sold"]
	wsselljet=[0,"JetA sold"]
	wssellbld=[0,"Building materials sold"]
	wssellsupp=[0,"Supplies sold"]]
	
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
	#rentexp, rentinc, assnmtexp, assnmtinc, pltfee, addcrewfee, gndcrewfee, bkgfee, ref100, refjet, mxexp, eqinstl, acsold, acbought, fboref100, fborefjet, fbogndcrew, fborepinc, fborepexp, fboeqpexp, fboeqpinc, ptrentinc, ptrentexp, fbosell, fbobuy, wsbuy100, wssell100, wsbuyjet, wsselljet, wsbuybld, wssellbld, wsbuysupp, wssellsupp, grpay=(0 for i in range(35))
	# rentexp=0
	# rentinc=0
	# assnmtexp=0
	# assnmtinc=0
	# pltfee=0
	# addcrewfee=0
	# gndcrewfee=0
	# bkgfee=0
	# ref100=0
	# refjet=0
	# mxexp=0
	# eqinstl=0
	# acsold=0
	# acbought=0
	# fboref100=0
	# fborefjet=0
	# fbogndcrew=0
	# fborepinc=0
	# fborepexp=0
	# fboeqpexp=0
	# fboeqpinc=0
	# ptrentinc=0
	# ptrentexp=0
	# fbosell=0
	# fbobuy=0
	# wsbuy100=0
	# wssell100=0
	# wsbuyjet=0
	# wsselljet=0
	# wsbuybld=0
	# wssellbld=0
	# wsbuysupp=0
	# wssellsupp=0
	# grpay=0
	user=getname()
	fromdate=fdate+" 00:01"
	todate=tdate+" 23:59"
	print("Tallying payments from"+str(fdate[0])+"-"+str(fdate[1])+" to "+str(tdate[0])+"-"+str(tdate[1])+"...")
	#(date text, to text, from text, amount real, reason text, location real, aircraft real)
	for payment in c.execute('SELECT * FROM payments WHERE date BETWEEN ? AND ?',(fromdate,todate)):
		if payment[4]=="Rental of aircraft":
			if payment[2]==user:
				rentinc[0]+=payment[3]
			else:
				rentexp[0]+=payment[3]
		elif payment[4]=="Pay for assignment":
			if payment[2]==user:
				assnmtinc[0]+=payment[3]
			else:
				assnmtexp[0]+=payment[3]
		elif payment[4]=="Crew fee":
			addcrewfee[0]+=payment[3]
		elif payment[4]=="FBO ground crew fee":
			if payment[2]==user:
				fbogndcrew[0]+=payment[3]
			else:
				gndcrewfee[0]+=payment[3]
		elif payment[4]=="Booking Fee":
			bkgfee[0]+=payment[3]
		elif payment[4]=="Refuelling with JetA":
			if payment[2]==user:
				fborefjet[0]+=payment[3]
			else:
				refjet[0]+=payment[3]
		elif payment[4]=="Refuelling with 100LL":
			if payment[2]==user:
				fboref100[0]+=payment[3]
			else:
				ref100[0]+=payment[3]
		elif payment[4]=="Aircraft maintenance":
			if payment[2]==user:
				fborepinc[0]+=payment[3]
			else:
				mxexp[0]+=payment[3]
		elif payment[4]=="Aircraft sale":
			if payment[2]==user:
				acsold[0]+=payment[3]
			else:
				acbought[0]+=payment[3]
		elif payment[4]=="Sale of wholesale JetA":
			if payment[2]==user:
				wsselljet[0]+=payment[3]
			else:
				wsbuyjet[0]+=payment[3]
		elif payment[4]=="Sale of wholesale 100LL":
			if payment[2]==user:
				wssell100[0]+=payment[3]
			else:
				wsbuy100[0]+=payment[3]
		elif payment[4]=="Sale of supplies":
			if payment[2]==user:
				wssellsupp[0]+=payment[3]
			else:
				wsbuysupp[0]+=payment[3]
		elif payment[4]=="Sale of building materials":
			if payment[2]==user:
				wssellbld[0]+=payment[3]
			else:
				wsbuybld[0]+=payment[3]
		elif payment[4]=="Group payment":
			if payment[2]==user:
				grpay[0]+=payment[3]
			else:
				grpay-=payment[3]
		else:
			print("No category found for "+payment[4])
	#rentexp, rentinc, assnmtexp, assnmtinc, pltfee, addcrewfee, gndcrewfee, bkgfee, ref100, refjet, mxexp, eqinstl, acsold, acbought, fboref100, fborefjet, fbogndcrew, fborepinc, fborepexp, fboeqpexp, fboeqpinc, ptrentinc, ptrentexp, fbosell, fbobuy, wsbuy100, wssell100, wsbuyjet, wsselljet, wsbuybld, wssellbld, wsbuysupp, wssellsupp, grpay=(0 for i in range(35))

	#Income nets
	rent=[rentinc-rentexp,"Rental"]
	assnmt=[assnmtinc-assnmtexp,"Assignments"]
	ac=[acsold-acbought,"Aircraft"]
	ws100=[fboref100+wssell100-wsbuy100,"WS 100LL"]
	wsjet=[fborefjet+wsselljet-wsbuyjet,"WS JetA"]
	fborep=[fborepinc-fborepexp,"FBO Repairs"]
	fboeqp=[fboeqpinc-fboeqpexp,"FBO Eqp Instl"]
	ptrent=[ptrentinc,"PT Rent"]
	fbo=[fbosell-fbobuy,"FBO"]
	sup=[wssellsupp-wsbuysupp,"Supplies"]
	bld=[wssellbld-wsbuybld,"Building Mtrls"]
	incnets=[rent, assnmt, ac, ws100, wsjet, fborep, fboeqp, ptrent, fbo, sup, bld]
	
	#Expense nets
	#mxexp
	#ref100
	#refjet
	#bkgfee
	#gndcrewfee
	#addcrewfee
	#pltfee
	
	incnet=[]
	expnet=[ref100, refjet, bkgfee, gndcrewfee, addcrewfee, pltfee, mxexp]
	netinc=0
	netexp=ref100[0]+refjet[0]+bkgfee[0]+gndcrewfee[0]+addcrewfee[0]+pltfee[0]+mxexp[0]
	for net in incnets:
		if net[0]>0:
			incnet.add(net)
			netinc+=net[0]
		else:
			expnet.add(net)
			netexp+=net[0]
	for net in incnet:
		net[0]=net[0]/netinc*100
	for net in expnet:
		net[0]=net[0]/netinc*100
	
	rlabels = incnet[:][1]
	elabels = expnet[:][1]
	rsizes = incnet[:][0]
	esizes = expnet[:][0]
	
	#Totals
	revs=[rentinc, assnmtinc, acsold, fboref100, fborefjet, fbogndcrew, fborepinc, fboeqpinc, ptrentinc, fbosell, wssell100, wsselljet, wssellbld, wssellsupp]
	exps=[rentexp, assnmtexp, pltfee, addcrewfee, gndcrewfee, bkgfee, ref100, refjet, mxexp, eqinstl, acbought, fborepexp, fboeqpexp, fbobuy, wsbuy100, wsbuyjet, wsbuybld, wsbuysupp]
	rev=0
	exp=0
	for this in revs:
		rev+=this[0]
	for this in exps:
		exp+=this[0]
	for this in revs:
		this[0]=this[0]/rev*100
	for this in exps:
		this[0]=this[0]/exp*100
	revo=[0,"Other"]
	expo=[0,"Other"]
	revchart=[]
	expchart=[]
	for this in revs:
		if this[0] < 10:
			revo[0]+=this[0]
		else:
			revchart.add(this)
	for this in exps:
		if this[0] < 10:
			expo[0]+=this[0]
		else:
			expchart.add(this)
	revchart.add(revo)
	expchart.add(expo)

	# The slices will be ordered and plotted counter-clockwise.
	#labels = 'Frogs', 'Hogs', 'Dogs', 'Logs'
	rlabels = revchart[:][1]
	elabels = expchart[:][1]
	#sizes = [15, 30, 45, 10]
	rsizes = revchart[:][0]
	esizes = expchart[:][0]
	#colors = ['yellowgreen', 'gold', 'lightskyblue', 'lightcoral']
	rcolors = ['yellowgreen', 'gold', 'lightskyblue', 'lightcoral']
	ecolors = ['yellowgreen', 'gold', 'lightskyblue', 'lightcoral']
	#explode = (0, 0.1, 0, 0) # only "explode" the 2nd slice (i.e. 'Hogs') # But I don't wanna explode...

	plt.pie(rsizes, labels=rlabels, colors=rcolors,
			autopct='%1.1f%%', shadow=True, startangle=90)
	plt.axis('equal') # Set aspect ratio to be equal so that pie is drawn as a circle.
	plt.show()
	plt.pie(esizes, labels=elabels, colors=ecolors,
			autopct='%1.1f%%', shadow=True, startangle=90)
	plt.axis('equal')
	plt.show()

def gettype(icao):
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

def main(argv):
	
	syntaxstring='pricelog.py -un -dmac <aircraft icao> -ft <YYYY-MM-DD> -lh <price>'
	try:
		opts, args = getopt.getopt(argv,"hund:m:a:c:f:t:l:i:",["duration=","map=","average=","cheapest=","from=","to=","low=","high="])
	except getopt.GetoptError:
		print(syntaxstring)
		sys.exit(2)
	conn = sqlite3.connect('/mnt/data/XPLANE10/XSDK/forsale.db')
	tot=0
	avg=0
	low=0
	dur=0
	pay=0
	ppay=0
	lowprice=0
	highprice=99999999
	fromdate="0000-01-01"
	todate="9999-12-31"
	for opt, arg in opts:
		if opt=='-h':
			print(syntaxstring)
			sys.exit()
		elif opt=='-u':
			acforsale(conn)
		elif opt=='-n':
			tot=1
		elif opt in ("-d", "--duration"):
			durtype,dur=gettype(arg)
		elif opt in ("-m", "--map"):
			maptype,domap=gettype(arg)
			maplocations(conn,maptype)
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
	
	if tot==1:
		totals=gettotals(conn,fromdate,todate)
		# for i in range(len(totals)):
			# print("Query "+str(i+1)+ " at "+totals[i][0]+" lists "+str(totals[i][1])+" planes for sale")
		plotdates(totals,"Aircraft for sale","Aircraft")
	
	if avg==1:
		averages=getaverages(conn,avgtype,fromdate,todate)
		plotdates(averages,"Average price for "+avgtype,"Price")
	
	if low==1:
		lows=getlows(conn,lowtype,fromdate,todate)
		plotdates(lows,"Lowest price for "+lowtype,"Price")
	
	if dur==1:
		listings=getlistings(conn,durtype,lowprice,highprice)
		durations=[]
		for listing in listings:
			duration=listings[4]-listings[3]
			durations.append((listings[2],duration))
			print(str(listings[2])+": "+str(duration))
		plotdates(durations,"Time to sell for "+durtype,"Days")
	
	if pay==1:
		conn2=sqlite3.connect('/mnt/data/XPLANE10/XSDK/payments.db')
		year=fromdate.split('-', 2)[0]
		month=fromdate.split('-', 2)[1]
		logpaymonth(conn,year,month)
	
	if ppay==1:
		# fyear=fromdate.split('-', 2)[0]
		# fmonth=fromdate.split('-', 2)[1]
		# fday=fromdate.split('-', 2)[2]
		# tyear=todate.split('-', 2)[0]
		# tmonth=todate.split('-', 2)[1]
		# tday=todate.split('-', 2)[2]
		# fdate=(fyear,fmonth,fday)
		# tdate=(tyear,tmonth,tday)
		plotpayments(conn,fromdate,todate)
	
	# We can also close the connection if we are done with it.
	# Just be sure any changes have been committed or they will be lost. FOREVER
	print("Finished, closing database...")
	conn.close()
	
if __name__ == "__main__":
   main(sys.argv[1:])
