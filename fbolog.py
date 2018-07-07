#!/usr/bin/python
import sys, getopt, sqlite3
import locale, time
import fseutils # My custom FSE functions
from datetime import timedelta, date
from appdirs import AppDirs
from pathlib import Path

def logpaymonth(conn,fromdate): #Log a month of payments
	year,month,*rest=fromdate.split('-', 2)
	print("Sending request for payment listing...")
	payments = fseutils.fserequest_new('payments','monthyear','Payment','xml',1,1,'&month='+month+'&year='+year)
	if payments!=[]:
		c=getpaydbcon(conn)
		rows=[]
		fields=(("Date", 0), ("To", 0), ("From", 0), ("Amount", 2), ("Reason", 0), ("Location", 0), ("Fbo", 0), ("Aircraft", 0), ("Id", 1),  ("Comment", 0))
		print("Recording data...")
		for payment in payments:
			row=fseutils.getbtns(payment,fields)
			if row[8]=="null":
				row[8]=""
			row[0]=row[0].replace('/','-')
			rows.append(tuple(row))
		c.execute('BEGIN TRANSACTION')
		c.executemany('INSERT INTO payments VALUES (?,?,?,?,?,?,?,?,?,?)',rows)
		conn.commit()

def getpaydbcon(conn): #Get cursor for payment database
	#print("Initializing payment database cursor...")
	c = conn.cursor()
	if not getpaydbcon.has_been_called:
		c.execute("SELECT COUNT(*) FROM sqlite_master WHERE type = 'table'")
		exist=c.fetchone()
		if exist[0]==0: #Table does not exist, create table
			print("Creating payment tables...")
			c.execute('BEGIN TRANSACTION')
			c.execute('''CREATE TABLE payments
				 (date text, payto text, payfrom text, amount real, reason text, location text, fbo text, aircraft text, pid real, comment text)''')
			c.execute('''CREATE INDEX idx1 ON payments(date)''')
			conn.commit()
		else:
			c.execute('SELECT date FROM payments ORDER BY date DESC')
			dtime=c.fetchone()
			print("Last payment data recorded: "+dtime[0])
		getpaydbcon.has_been_called=True
	return c

def getfborev(conn): #Gets the revenues for FBO's
	c=getpaydbcon(conn)
	print("Getting FBO logs...")
	#galjet=["","",0] #1st date, last date, total
	#gal100=["","",0]
	#assnmtcost,gndcrew,refjet,ref100,repinc,wsjet,ws100,wssupp,wsbld,eqpinstl=([["","",0]] for i in range(10))
	categories=("FBO ground crew fee", "Refuelling with JetA", "Refuelling with 100LL", "Aircraft maintenance", "Sale of wholesale JetA", "Sale of wholesale 100LL", "Sale of supplies", "Sale of building materials", "Installation of equipment in aircraft")
	revs=[]
	for fbo in getfbos(conn):
		revs.append([fbo,0,"",""]) #location, revenue total, first revenue, last revenue
	#(date text, payto text, payfrom text, amount real, reason text, location text, fbo text, aircraft text, pid real, comment text)
	for log in c.execute('SELECT date, amount, reason, fbo, comment FROM payments WHERE payto = ? ORDER BY date DESC',(fseutils.getname(),)):
		for cat in categories: #See if payment is a category we care about
			if log[2]==cat:
				for rev in revs: #See if payment is for FBO we care about
					if log[3]==rev[0]:
						rev[1]+=log[1] #Add the revenue
						dt=fseutils.getdtime(log[0])
						if rev[2]=="": #First payment, set the dates
							rev[2]=dt
							rev[2]=dt
						else: #Last payment, update the last date
							rev[3]=dt
						break
					else:
						print("Did not recognize FBO: "+log[3])
				break
	for fbo in revs:
		delta=fbo[3]-fbo[2]
		if delta>0:
			weeks=timedelta.total_seconds(delta)/604800 #Number of seconds in a week
			fbo[1]/=weeks
		else: #Can't divide by zero
			fbo[1]=0
	#gals=float(log[4].split(':',3)[2].split(',')[0])
	return revs

def getwkrev(conn): #Gets the revenue/week of FBO's
	c=getpaydbcon(conn)
	print("Getting FBO logs...")
	categories=("FBO ground crew fee", "Refuelling with JetA", "Refuelling with 100LL", "Aircraft maintenance", "Sale of wholesale JetA", "Sale of wholesale 100LL", "Sale of supplies", "Sale of building materials", "Installation of equipment in aircraft")
	revs=[] #List of revenue per week for each week
	fbos=getfbos(conn) #FBO's we care about
	wk=0 #Track which week is being added
	for pay in c.execute('SELECT date, amount, reason, fbo, comment FROM payments WHERE payto = ? ORDER BY date DESC',(fseutils.getname(),)):
		for cat in categories:
			if log[2]==cat:
				for fbo in fbos:
					if log[3]==fbo: #Ok we actually care about this payment and FBO
						thedate=fseutils.getdtime(pay[0])
						if wk==0: #Add first payment info
							wk=1
							revs.append([thedate,pay[1]])
						else: #Figure it out I guess
							delta=thedate-revs[0][0]
							thisweek=timedelta.total_seconds(delta)/604800
							if thisweek<wk: #Add to current week
								revs[wk-1][1]+=log[1]
							else: #Add new week
								revs.append([thedate,pay[1]])
						break
				break
	return revs

def getfbos(conn): #Returns a list of all user's FBO's in the log
	c=getpaydbcon(conn)
	print("Getting list of FBO's...")
	fbos=[]
	for place in c.execute('SELECT DISTINCT fbo FROM payments WHERE payto = ?',(fseutils.getname(),)):
		if place[0]!="N/A":
			fbos.append(place[0])
	return fbos

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
		commo = fseutils.fserequest_new('commodities','key','Commodity','xml',1,1)
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

def plotpayments(conn,fromdate,todate): #Plot payment totals per category
	c=getpaydbcon(conn)
	user=fseutils.getname()
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
	
def main(argv): #This is where the magic happens
	syntaxstring='fbolog.py -acdgmx <aircraft> -bhjknpqsuvz -e <fuel/mtrls> -ft <YYYY-MM-DD> -il <price>'
	try: #abcd____ijkl_nopqrstuvwxyz
		opts, args = getopt.getopt(argv,"e:f:gm",["commodity=","from="])
	except getopt.GetoptError:
		print(syntaxstring)
		sys.exit(2)
	avg, pay, maprev, plrev=(False,)*4
	getpaydbcon.has_been_called=False #To know when it's the first cursor initialized
	highprice=99999999
	fromdate="2014-01-01"
	todate="2020-12-31"
	for opt, arg in opts:
		elif opt in ("-e", "--commodity"): #Maps locations and amounts of commodities
			locations,cmin,cmax=getcommo(arg)
			mapper(arg, locations, cmin, cmax, "Locations of Commodities")
		elif opt in ("-f", "--from"): #First date to be used in different functions
			fromdate=arg
		elif opt=="-p": #Log a month of payments based on the date given
			pay=True
		elif opt=="-m": #Map revenues of FBO's
			maprev=True
		elif opt=="-g": #Plot revenues of FBO's
			plrev=True
	
		if True in (pay, plrev, maprev):
			dirs=AppDirs("nattgew-xpp","Nattgew")
			filename=str(Path(dirs.user_data_dir).joinpath('fbopayments.db'))
			conn=sqlite3.connect(filename)
			if pay:
				logpaymonth(conn,fromdate)
			if plrev:
				revs=getwkrev(conn)
				coords,cmin,cmax=fseutils.getcoords(i[0][:4] for i in revs)
				locations=[]
				for i in range(len(coords)):
					locations.append(coords[i][0],coords[i][1],revs[i][1])
					#plotdates(dlist,title,ylbl,sym,clr,save):
				fseutils.mapper(money, locations, cmin, cmax, "Revenue by FBO")
			if maprev:
				revs=getfborev(conn)
				coords,cmin,cmax=fseutils.getcoords(i[0][:4] for i in revs)
				locations=[]
				for i in range(len(coords)):
					locations.append(coords[i][0],coords[i][1],revs[i][1])
				fseutils.mapper(money, locations, cmin, cmax, "Revenue by FBO")
			conn.close()
	print("Finished!")

if __name__ == "__main__":
   main(sys.argv[1:])
