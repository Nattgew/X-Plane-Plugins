#!/usr/bin/python
from xml.dom import minidom
import urllib.request
import math
import os, re, fileinput, csv
import locale, time
import sys, getopt
import regions, actypes
import sqlite3
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt

def fserequest(rqst,tagname):
	file='/mnt/data/XPLANE10/XSDK/mykey.txt'
	with open(file, 'r') as f:
		mykey = f.readline()
	mykey=mykey.strip()
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

def getdbcon(conn):
	print("Initializing database cursor...")
	c = conn.cursor()
	c.execute("select count(*) from sqlite_master where type = 'table';")
	exist=c.fetchone()
	print("Found " + str(exist[0]) + " tables...")
	if  exist[0]== 0:
		print("Creating tables...")
		c.execute('''CREATE TABLE allac
			 (serial real, type text, loc text, locname text, hours real, price real, obsiter real)''')
		c.execute('''CREATE TABLE queries
			 (obsiter real, qtime text)''')
		# Save (commit) the changes
		conn.commit()
	return c
	
def getmaxiter(conn):
	c = conn.cursor()
	c.execute('SELECT iter FROM queries ORDER BY iter DESC;')
	count=c.fetchone()
	print("Found "+str(count)+" previous queries")
	if count is not None:
		current=int(count[0])
	else:
		current=0
	return current

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
	print("Mapping points...")
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
	#for i in range(len(points)):
		#print("Plotting division "+str(i))
		# x, y = m([k[1] for k in divs[i]], [k[0] for k in divs[i]])
#			print("Plotting coord "+str(divs[i][j][0])+", "+str(divs[i][j][1]))
		# x, y = m(points[i][1],points[i][0])
	x, y = m([i[1] for i in points], [i[0] for i in points])
	ptsize=2
	c='b'
	m.plot(x,y,markersize=ptsize,marker='o',markerfacecolor=c)
	plt.title('Locations of aircraft for sale',fontsize=12)
	plt.show()

def gettotals(conn,fr,to):
	c=getdbcon(conn)
	totals=[]
	print("Finding total aircraft for sale from "+fr+" to "+to+"...")
	for query in c.execute('SELECT * FROM queries WHERE qtime BETWEEN ? AND ?', (fr,to)):
		qtime=query[1]
		print("Reading query "+str(query[0])+" from "+qtime)
		c.execute('SELECT COUNT(*) FROM allac WHERE obsiter = ?', (query[0],))
		total=int(c.fetchone()[0])
		totals.append((qtime,total))
	return totals

def getaverages(conn,actype,fr,to):
	c=getdbcon(conn)
	averages=[]
	print("Finding averages for: "+actype+"...")
	for query in c.execute('SELECT * FROM queries WHERE qtime BETWEEN ? AND ?', (fr,to)):
		numforsale=0
		totalprice=0
		qtime=query[1]
		for sale in c.execute('SELECT price FROM allac WHERE obsiter = ? AND type = ?', (query[0],actype)):
			totalprice+=int(sale[0])
			numforsale+=1
		if numforsale>0:
			avg=totalprice/numforsale
			averages.append((qtime,avg))
	return averages

def maplocations(conn):
	c=getdbcon(conn)
	print("Building airport location dictionary from csv...")
	loc_dict=build_csv()
	print("Creating locations list...")
	locations=[]
	lat_tot=0
	lon_tot=0
	iters=getmaxiter(conn)
	latmax,lonmax,latmin,lonmin=100,200,100,200 #garbage to signal init
	for row in c.execute('SELECT loc FROM allac WHERE obsiter = ?', (iters,)):
		try:
			lat,lon=loc_dict[row[0]]
		except KeyError:
			continue
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

def plotdates(prices,title,ylbl):
	print("Plotting figure for: "+title)
	fig, ax = plt.subplots()
	ax.plot([i[0] for i in prices], [i[1] for i in prices], 'o-')
	fig.autofmt_xdate()
	plt.title(title,fontsize=12)
	plt.xlabel("Date")
	plt.ylabel(ylbl)
	plt.show()

def gettype(icao):
	icaodict=actypes.getdict()
	try:
		actype=icaodict[icao]
		success=1
	except (KeyError,IndexError) as e:
		print("Name for code "+icao+" not found!")
		actype=""
		success=0
	return actype, success

def main(argv):
	
	syntaxstring='pricelog.py -unm -a <aircraft icao> -f <YYYY-MM-DD> -t <YYYY-MM-DD>'
	try:
		opts, args = getopt.getopt(argv,"unma:l:f:t:",["average=","lowest=","from=","to="])
	except getopt.GetoptError:
		print(syntaxstring)
		sys.exit(2)
	conn = sqlite3.connect('/mnt/data/XPLANE10/XSDK/forsale.db')
	avg=0
	tot=0
	low=0
	fromdate=""
	todate=""
	for opt, arg in opts:
		if opt=='-h':
			print(syntaxstring)
			sys.exit()
		elif opt=='-u':
			acforsale(conn)
		elif opt=='-n':
			tot=1
		elif opt=='-m':
			maplocations(conn)
		elif opt in ("-f", "--from"):
			fromdate=arg
		elif opt in ("-t", "--to"):
			todate=arg
		elif opt in ("-a", "--average"):
			avgtype,avg=gettype(arg)
		elif opt in ("-l", "--lowest"):
			lowtype,low=gettype(arg)
	if fromdate=="":
		fromdate="0000-01-01"
	if todate=="":
		todate="9999-12-31"
	
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
	
	# We can also close the connection if we are done with it.
	# Just be sure any changes have been committed or they will be lost. FOREVER
	print("Finished, closing database...")
	conn.close()
	
if __name__ == "__main__":
   main(sys.argv[1:])
