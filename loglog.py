#!/usr/bin/python
import math, sys, getopt, sqlite3
import fseutils # My custom FSE functions
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt

def loglogmonth(conn,fromdate): #Log a month of logs
	year,month,*rest=fromdate.split('-', 2)
	print("Sending request for logs...")
	logs = fseutils.fserequest(1,'query=flightlogs&search=monthyear&month='+month+'&year='+year,'FlightLog','xml')
	if logs!=[]:
		c=getlogdbcon(conn)
		rows=[]
		fields=(("Id", 1), ("Type", 0), ("Time", 0), ("Distance", 1), ("SerialNumber", 1), ("Aircraft", 0), ("MakeModel", 0), ("From", 0), ("To", 0), ("FlightTime", 0), ("Income", 2), ("PilotFee", 2), ("CrewCost", 2), ("BookingFee", 2), ("Bonus", 2), ("FuelCost", 2), ("GCF", 2), ("RentalPrice", 2), ("RentalType", 0), ("RentalUnits", 0), ("RentalCost", 2))
		print("Recording data...")
		for log in logs:
			row=fseutils.getbtns(log, fields)
			row[2]=row[2].replace('/','-')
			rows.append(tuple(row))
		c.executemany('INSERT INTO logs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',rows)
		conn.commit()

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

def getcountries(conn): #Return list of countries?
	cdict=fseutils.build_csv("country")
	c=getlogdbcon(conn)
	countries=[] #List of countries found
	#(fid real, type text, date text, dist real, sn real, ac text, model text, dep text, arr text, fltime text, income real, pfee real, crew real, bkfee real, bonus real, fuel real, gndfee real, rprice real, rtype text, runits text, rcost real)
	for log in c.execute('SELECT dep, arr FROM logs'):
		logc=(cdict[log[0]],cdict[log[1]]) #Look up countries of these airports
		match=[0,0] #Track if each has been matched
		for visited in countries: #Check current list
			for i in range(2):
				if logc[i]==visited: #Already in the list
					match[i]=1
					if match[i-1]==1: #Other one too, stop looking
						break
	for i in range(2):
		if match[i]==0: #Add to list if not already there
			countries.append(logc[i])
	return countries

def mapcountries(countries): #Map list of countries?
	fig = plt.figure(figsize=(11.7,8.3))
	plt.subplots_adjust()
	m = Basemap(projection='hammer', resolution=None, lon_0=0)
	m.drawcountries(linewidth=0.5)
	m.drawcoastlines(linewidth=0.5)
	
	from shapelib import ShapeFile
	import dbflib
	from matplotlib.collections import LineCollection
	from matplotlib import cm
	
	#for ctry in countries:
	shp = ShapeFile(r"borders/world_adm1")
	dbf = dbflib.open(r"borders/world_adm1")
	
	for npoly in range(shp.info()[0]):
		shpsegs = []
		shpinfo = []
		shp_object = shp.read_obj(npoly)
		verts = shp_object.vertices()
		rings = len(verts)
		for ring in range(rings):
			lons, lats = zip(*verts[ring])
			if max(lons)>721. or min(lons)<-721. or max(lats) >91. or min(lats) < -91.:
				raise ValueError,msg
			x, y = m(lons, lats)
			shpsegs.append(zip(x,y))
			if ring == 0:
				shapedict = dbf.read_record(npoly)
			name = shapedict["NAME_1"]
			
			shapedict['RINGNUM'] = ring+1
			shapedict['SHAPENUM'] = npoly+1
			shpinfo.append(shapedict)
		print(name)
		lines = LineCollection(shpsegs,antialiaseds=(1,))
		lines.set_facecolors(cm.jet(0.5))
		lines.set_edgecolors('k')
		lines.set_linewidth(0.3)
		ax.add_collection(lines)
	
	plt.show()

def main(argv): #This is where the magic happens
	syntaxstring='loglog.py -ax <aircraft>'
	try: #a__defg_ijklmnopqrstuvw_yz
		opts, args = getopt.getopt(argv,"bcx:",["typestats="])
	except getopt.GetoptError:
		print(syntaxstring)
		sys.exit(2)
	stat, map, logs=(False,)*3
	getlogdbcon.has_been_called=False
	highprice=99999999
	fromdate="2014-01-01"
	todate="2020-12-31"
	for opt, arg in opts:
		if opt=="-b": #Logs a month of flight logs, based on the date given
			logs=True
		elif opt=="-c": #Maps countries visited
			map=True			
		elif opt in ("-x", "--typestats"): #Plots stats for given type
			stattype,stat=fseutils.gettype(arg)

	if True in (logs, map, stat):
		conn=sqlite3.connect('/mnt/data/XPLANE10/XSDK/flightlogs.db')
		if stat:
			getapstats(conn,stattype)
		if map:
			countries=getcountries(conn)
			print(countries)
			mapcountries(countries)
		if logs:
			loglogmonth(conn,fromdate)
		conn.close()

if __name__ == "__main__":
   main(sys.argv[1:])
