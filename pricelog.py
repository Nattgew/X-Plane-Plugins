#!/usr/bin/env python
from xml.dom import minidom
import xml.etree.ElementTree as etree
import urllib.request, math, sys, getopt
import dicts # My script for custom dictionaries
import fseutils # My custom FSE functions
import csv, sqlite3, time
from datetime import timedelta, date, datetime
from mpl_toolkits.basemap import Basemap
from matplotlib.dates import DateFormatter, date2num
import matplotlib.pyplot as plt

def getname(): #Returns username stored in file
	with open('/mnt/data/XPLANE/XSDK/mykey.txt', 'r') as f:
		nothing = f.readline() #skip the key
		myname = f.readline()
		myname=myname.strip()
		return myname

def acforsale(conn): #Log aircraft currently for sale
	print("Sending request for sales listing...")
	airplanes = fseutils.fserequest(0,'query=aircraft&search=forsale','Aircraft','xml')
	if airplanes!=[]:
		print("Recording data...")
		c=getdbcon(conn)
		count=getmaxiter(conn)+1 #Index for this new iteration
		now=time.strftime("%Y-%m-%d %H:%M", time.gmtime())
		row=(count, now) #Record time and index of this iteration
		c.execute('INSERT INTO queries VALUES (?,?)',row) #Record date/time of this query
		goodones=[]
		file='/mnt/data/XPLANE/XSDK/pricewatch.csv'
		with open(file, 'r') as f:
			has_header = csv.Sniffer().has_header(f.read(1024)) #could not determine delimiter
			f.seek(0)  # rewind
			reader = csv.reader(f)
			if has_header:
				next(reader)  # skip header row
			for row in reader:
				goodones.append((row[0],row[1],int(row[2]),int(row[3]))) #actype, icao?, price, hours
		fields=(("SerialNumber", 1), ("MakeModel", 0), ("Location", 0), ("LocationName", 0), ("AirframeTime", 0), ("SalePrice", 2))
		rows=[] #List to INSERT, each row is a tuple
		bargains=[]
		for airplane in airplanes: #Record aircraft for sale
			row=fseutils.getbtns(airplane,fields)
			row[4]=int(row[4].split(":")[0])
			row.append(count) #Add iteration to end
			rows.append(tuple(row)) #Add row as tuple to list
			for option in goodones:
				if row[1]==option[0] and row[5]<option[2] and row[4]<option[3]:
					bargains.append(option[1]+" | $"+str(row[5])+" | "+str(row[4])+" hrs | "+row[2])
		c.executemany('INSERT INTO allac VALUES (?,?,?,?,?,?,?)',rows)
		if bargains!=[]: #Found some bargains to send by email
			msg="Good aircraft deals: \n"
			for bargain in bargains:
				msg+="\n"+bargain
			fseutils.sendemail("Aircraft Deals",msg)
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
	print("Sending request for payment listing for "+fromdate+"...")
	payments = fseutils.fserequest(1,'query=payments&search=monthyear&month='+month+'&year='+year,'Payment','xml')
	if payments!=[]:
		c=getpaydbcon(conn)
		rows=[]
		fields=(("Date", 0), ("To", 0), ("From", 0), ("Amount", 2), ("Reason", 0), ("Location", 0), ("Id", 1), ("Aircraft", 0), ("Comment", 0))
		print("Recording data...")
		for payment in payments:
			row=fseutils.getbtns(payment,fields)
			if row[8]=="null":
				row[8]=""
			row[0]=row[0].replace('/','-')
			rows.append(tuple(row))
		c.executemany('INSERT INTO payments VALUES (?,?,?,?,?,?,?,?,?)',rows)
		conn.commit()
	else:
		print("No payments received for: "+'query=payments&search=monthyear&month='+month+'&year='+year,'Payment')

def logconfigs(conn): #Update database of aircraft configs
	print("Sending request for configs...")
	configs = fseutils.fserequest(1,'query=aircraft&search=configs','AircraftConfig','xml')
	if configs!=[]:
		c=getconfigdbcon(conn)
		d=getconfigdbcon(conn)
		fields=(("MakeModel", 0), ("Crew", 1), ("Seats", 1), ("CruiseSpeed", 1), ("GPH", 1), ("FuelType", 1), ("MTOW", 1), ("EmptyWeight", 1), ("Price", 3), ("Ext1", 1), ("LTip", 1), ("LAux", 1), ("LMain", 1), ("Center1", 1), ("Center2", 1), ("Center3", 1), ("RMain", 1), ("RAux", 1), ("RTip", 1), ("Ext2", 1), ("Engines", 1), ("EnginePrice", 3))
		print("Updating config data...")
		for config in configs:
			row=fseutils.getbtns(config, fields)
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
			date=fseutils.getdtime(e.fetchone()[0])
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
		totals.append((fseutils.getdtime(query[1]),total))
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
			averages.append((fseutils.getdtime(query[1]),avg,stdev))
	return averages

def getbaseprice(actype): #Return the base price for this actype
	conn=sqlite3.connect('/mnt/data/XPLANE/XSDK/configs.db')
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

def getlows(conn,actype,fr,to): #Return list of lowest price for aircraft in each query
	c=getdbcon(conn)
	d=getdbcon(conn)
	lows=[]
	print("Finding low low prices for: "+actype+"...")
	for query in c.execute('SELECT * FROM queries WHERE qtime BETWEEN ? AND ?', (fr,to)):
		d.execute('SELECT price FROM allac WHERE obsiter = ? AND type = ? ORDER BY price', (query[0],actype))
		price=d.fetchone()
		if price is not None:
			lows.append((fseutils.getdtime(query[1]),price))
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
		dprice.append((fseutils.getdtime(day[0]+" 00:01"),avg,stdev))
	return dprice

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
		commo = fseutils.fserequest(1,'query=commodities&search=key','Commodity','xml')
		print("Sorting results...")
		stuff = []
		for item in commo: #Parse commodity info
			typ = fseutils.gebtn(item, "Type")
			if typ==t1 or typ==t2:
				loc = fseutils.gebtn(item, "Location")
				amt = fseutils.gebtn(item, "Amount")
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
			coords,cmin,cmax=fseutils.getcoords(i[0] for i in qty)
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
	cdict=fseutils.build_csv("country")
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
	locations,cmin,cmax=fseutils.getcoords([i[0] for i in c.execute(q1)])
	if len(locations)>0:
		fseutils.mapper('ac', locations, cmin, cmax, title)

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
	fseutils.plotdates([refjet, addcrewfee, gndcrewfee],"Money","Money",['-'],None,0)

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
	ownership=[0,"Ownership Fee"]
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
				("Installation of equipment in aircraft", fboeqpinc, eqinstl),
				("Ownership Fee", ownership, ownership)]
	user=getname()
	fromdate=fdate+" 00:01"
	todate=tdate+" 23:59"
	print("Tallying payments from "+str(fdate[0])+"-"+str(fdate[1])+" to "+str(tdate[0])+"-"+str(tdate[1])+"...")
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
	expnet=[ref100, refjet, bkgfee, gndcrewfee, addcrewfee, pltfee, mxexp, ownership] #Always negative
	netinc=0
	netexp=ref100[0]+refjet[0]+bkgfee[0]+gndcrewfee[0]+addcrewfee[0]+pltfee[0]+mxexp[0]+ownership[0]
	for net in incnets: #Test if category represents an expense or income
		if net[0]>0:
			incnet.append(net)
			netinc+=net[0]
		else:
			expnet.append(net)
			netexp+=net[0]
	fseutils.pieplot(incnet,netinc,5,"Income sources")
	fseutils.pieplot(expnet,netexp,5,"Expense sources")
	#Totals income/expenses
	revs=[rentinc, assnmtinc, acsold, fboref100, fborefjet, fbogndcrew, fborepinc, fboeqpinc, ptrentinc, fbosell, wssell100, wsselljet, wssellbld, wssellsupp]
	exps=[rentexp, assnmtexp, pltfee, addcrewfee, gndcrewfee, bkgfee, ref100, refjet, mxexp, eqinstl, acbought, fborepexp, fboeqpexp, fbobuy, wsbuy100, wsbuyjet, wsbuybld, wsbuysupp]
	fseutils.pieplot(revs,None,5,"Revenues")
	fseutils.pieplot(exps,None,5,"Expenses")

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
	fseutils.pieplot(ac,None,5,"Aircraft Income")

def main(argv): #This is where the magic happens
	syntaxstring='pricelog.py -acdgm <aircraft> -hjknpqsuvz -e <fuel/mtrls> -ft <YYYY-MM-DD> -il <price>'
	try: #_b___________no__r_____x__
		opts, args = getopt.getopt(argv,"a:c:d:e:f:g:hi:jkl:m:pqst:uvwy:z",["duration=","map=","average=","cheapest=","from=","to=","low=","high=","total=","commodity=","timeforsale="])
	except getopt.GetoptError:
		print(syntaxstring)
		sys.exit(2)
	tot, avg, low, dur, pay, ppay, spay, stot, com, lowprice, fuel, domap, sale, tots, pout, tfs=(False,)*16
	getdbcon.has_been_called=False #To know when it's the first cursor initialized
	getpaydbcon.has_been_called=False
	getconfigdbcon.has_been_called=False
	highprice=99999999
	fromdate="2014-01-01"
	todate="2020-12-31"
	for opt, arg in opts:
		if opt in ("-a", "--average"): #Plots average prices for type
			avgtype,avg=fseutils.gettype(arg)
		elif opt in ("-c", "--cheapest"): #Plots the cheapest aircraft of this type
			lowtype,low=fseutils.gettype(arg)
		elif opt in ("-d", "--duration"): #Calculates duration to sell for a type (in work)
			durtype,dur=fseutils.gettype(arg)
		elif opt in ("-e", "--commodity"): #Maps locations and amounts of commodities
			locations,cmin,cmax=getcommo(arg)
			fseutils.mapper(arg, locations, cmin, cmax, "Locations of Commodities")
		elif opt in ("-f", "--from"): #First date to be used in different functions
			fromdate=arg
		elif opt in ("-g", "--total"): #Plots total aircraft of this type for sale
			tottype,tot=fseutils.gettype(arg)
		elif opt=='-h': #plshelp
			print(syntaxstring)
			sys.exit()
		elif opt in ("-i", "--high"): #Highest price to be considered in other functions
			highprice=arg
		elif opt=="-j": #Plots fuel prices, averaged for each day
			fuel=True
		elif opt=="-k": #Updates the configuration database
			cconn=sqlite3.connect('/mnt/data/XPLANE/XSDK/configs.db')
			logconfigs(cconn)
			cconn.close()
		elif opt in ("-l", "--low"): #Lowest price to be considered in other functions
			lowprice=arg
		elif opt in ("-m", "--map"): #Map locations of a type for sale
			maptype,domap=fseutils.gettype(arg)
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
		elif opt in ("-y", "--timeforsale"): #Plots sale prices per aircraft over time
			timetype,tfs=fseutils.gettype(arg)
		elif opt=="-z": #Temporary - Adds comments to a month of payment logs
			com=True
	print("Running option...")
	if True in (pay, ppay, spay, stot, com, fuel):
		conn=sqlite3.connect('/mnt/data/XPLANE/XSDK/payments.db')
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
			fseutils.plotdates([prices],"Average fuel price","Price",['o-'],None,0)
		conn.close()

	if True in (tot, avg, low, dur, domap, sale, tots, pout, tfs):
		conn=sqlite3.connect('/mnt/data/XPLANE/XSDK/forsale.db')
		if domap:
			mapaclocations(conn,maptype)
		if sale:
			acforsale(conn)
		if tfs:
			times=gettimeforsale(conn,timetype)
			bprice=getbaseprice(timetype)
			times.append([[fseutils.getdtime("2014-01-01 00:01"),bprice],[fseutils.getdtime("2100-12-31 23:59"),bprice]])
			fseutils.plotdates(times,"Prices of "+timetype,"Price",['o-','--'],[None,'r'],0)
		if tot:
			totals=gettotals(conn,tottype,fromdate,todate)
			fseutils.plotdates([totals],"Number of "+tottype+" for sale","Aircraft",['o-'],None,0)
		if avg:
			averages=getaverages(conn,avgtype,fromdate,todate)
			bprice=getbaseprice(avgtype)
			baseprice=[[fseutils.getdtime("2014-01-01 00:01"),bprice],[fseutils.getdtime("2100-12-31 23:59"),bprice]] #Ensure it covers the whole range
			fseutils.plotdates([averages,baseprice],"Average price for "+avgtype,"Price",['o-','--'],['b','r'],0)
		if low:
			lows=getlows(conn,lowtype,fromdate,todate)
			bprice=getbaseprice(lowtype)
			baseprice=[[fseutils.getdtime("2014-01-01 00:01"),bprice],[fseutils.getdtime("2100-12-31 23:59"),bprice]]
			fseutils.plotdates([lows,baseprice],"Lowest price for "+lowtype,"Price",['o-','--'],['b','r'],0)
		if dur:
			listings=getlistings(conn,durtype,lowprice,highprice)
			durations=[]
			for listing in listings:
				duration=listings[4]-listings[3]
				durations.append((listings[2],duration))
				print(str(listings[2])+": "+str(duration))
			fseutils.plotdates([durations],"Time to sell for "+durtype,"Days",['o-'],None,0)
		if pout:
			actypes=[]
			with open('/mnt/data/XPLANE/XSDK/dailytypes.txt', 'r') as f:
				for actype in f:
					actype=actype.strip()
					print("Saving figure for "+actype)
					ptype,ret=fseutils.gettype(actype)
					if ret:
						lows=getlows(conn,ptype,fromdate,todate)
						bprice=getbaseprice(ptype)
						baseprice=[[fseutils.getdtime("2014-01-01 00:01"),bprice],[fseutils.getdtime("2100-12-31 23:59"),bprice]]
						fseutils.plotdates([lows,baseprice],"Lowest price for "+ptype,"Price",['o-','--'],['b','r'],1)
		conn.close()
	print("Finished!")

if __name__ == "__main__":
   main(sys.argv[1:])
