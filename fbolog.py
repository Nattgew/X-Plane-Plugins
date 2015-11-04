#!/usr/bin/python
from xml.dom import minidom
import urllib.request, math, sys, getopt
import dicts # My script for custom dictionaries
import os, re, fileinput, csv, sqlite3
import locale, time
from datetime import timedelta, date, datetime
from mpl_toolkits.basemap import Basemap
from matplotlib.dates import DateFormatter, date2num
import matplotlib.pyplot as plt

def getkey(): #Returns API key stored in file
	with open('/mnt/data/XPLANE10/XSDK/myfbokey.txt', 'r') as f:
		mykey = f.readline()
	mykey=mykey.strip()
	return mykey

def getname(): #Returns username stored in file
	with open('/mnt/data/XPLANE10/XSDK/myfbokey.txt', 'r') as f:
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
		val=gebtn(field,tag[0])
		if tag[1]==1:
			val=int(val)
		elif tag[1]==2:
			val=float(val)
		elif tag[1]==3:
			val=int(float(val))
		vals.append(val)
	return vals

def logpaymonth(conn,fromdate): #Log a month of payments
	year,month,*rest=fromdate.split('-', 2)
	print("Sending request for payment listing...")
	payments = fserequest(1,'query=payments&search=monthyear&month='+month+'&year='+year,'Payment','xml')
	if payments!=[]:
		c=getpaydbcon(conn)
		rows=[]
		fields=(("Date", 0), ("To", 0), ("From", 0), ("Amount", 2), ("Reason", 0), ("Location", 0), ("Fbo", 0), ("Aircraft", 0), ("Id", 1),  ("Comment", 0))
		print("Recording data...")
		for payment in payments:
			row=getbtns(payment,fields)
			if row[8]=="null":
				row[8]=""
			row[0]=row[0].replace('/','-')
			rows.append(tuple(row))
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
			c.execute('''CREATE TABLE payments
				 (date text, payto text, payfrom text, amount real, reason text, location text, fbo text, aircraft text, pid real, comment text)''')
			c.execute('''CREATE INDEX idx1 ON payments(date)''')
		else:
			c.execute('SELECT date FROM payments ORDER BY date DESC')
			dtime=c.fetchone()
			print("Last payment data recorded: "+dtime[0])
		getpaydbcon.has_been_called=True
	return c

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

def getdtime(strin): #Return datetime for the Y-M-D H:M input
	adate,atime=strin.split()
	year,month,day=adate.split('-', 2)
	hour,mnt=atime.split(':')
	return datetime(int(year),int(month),int(day),int(hour),int(mnt))

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
	elif what in ("fuel", "mtrl", "money"):
		maxsz=max(points[:][2]) #Find largest value in list
		for loc in points: #Normalize all values
			loc[2]/=maxsz
		pts=[] #rows=thous, columns=colors, contents=list of points
		for i in range(maxsz+1):
			pts.append([[],[],[]]) #Add a new empty row
			for loc in points:
				if loc[2]==i+1: #If size matches, add the point
					pts[i][loc[3]].append((loc[0],loc[1]))
		for i in range(maxsz+1): #Set size/color of points
			sz=i #Size based on amount
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
	for log in c.execute('SELECT date, amount, reason, fbo, comment FROM payments WHERE payto = ? ORDER BY date DESC',(getname(),)):
		for cat in categories: #See if payment is a category we care about
			if log[2]==cat:
				for rev in revs: #See if payment is for FBO we care about
					if log[3]==rev[0]:
						rev[1]+=log[1] #Add the revenue
						dt=getdtime(log[0])
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
	for pay in c.execute('SELECT date, amount, reason, fbo, comment FROM payments WHERE payto = ? ORDER BY date DESC',(getname(),)):
		for cat in categories:
			if log[2]==cat:
				for fbo in fbos:
					if log[3]==fbo: #Ok we actually care about this payment and FBO
						thedate=getdtime(pay[0])
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
	for place in c.execute('SELECT DISTINCT fbo FROM payments WHERE payto = ?',(getname(),)):
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
	
def main(argv): #This is where the magic happens
	syntaxstring='fbolog.py -acdgmx <aircraft> -bhjknpqsuvz -e <fuel/mtrls> -ft <YYYY-MM-DD> -il <price>'
	try: #_____________n___r________
		opts, args = getopt.getopt(argv,"a:bc:d:e:f:g:hi:jkl:m:opqst:uvwx:y:z",["duration=","map=","average=","cheapest=","from=","to=","low=","high=","total=","commodity=","typestats=","timeforsale="])
	except getopt.GetoptError:
		print(syntaxstring)
		sys.exit(2)
	tot, avg, low, dur, pay, ppay, spay, stot, stat, logs, com, lowprice, fuel, domap, sale, tots, pout, tfs, fbo=(False,)*19
	getpaydbcon.has_been_called=False #To know when it's the first cursor initialized
	highprice=99999999
	fromdate="2014-01-01"
	todate="2020-12-31"
	for opt, arg in opts:
		if opt in ("-a", "--average"): #Plots average prices for type
			avgtype,avg=gettype(arg)
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
			conn=sqlite3.connect('/mnt/data/XPLANE10/XSDK/fbopayments.db')
			if pay:
				logpaymonth(conn,fromdate)
			if plrev:
				revs=getwkrev(conn)
				coords,cmin,cmax=getcoords(i[0][:4] for i in revs)
				locations=[]
				for i in range(len(coords)):
					locations.append(coords[i][0],coords[i][1],revs[i][1])
					#plotdates(dlist,title,ylbl,sym,clr,save):
				(money, locations, cmin, cmax, "Revenue by FBO")
			if maprev:
				revs=getfborev(conn)
				coords,cmin,cmax=getcoords(i[0][:4] for i in revs)
				locations=[]
				for i in range(len(coords)):
					locations.append(coords[i][0],coords[i][1],revs[i][1])
				mapper(money, locations, cmin, cmax, "Revenue by FBO")
			conn.close()
	print("Finished!")

if __name__ == "__main__":
   main(sys.argv[1:])
