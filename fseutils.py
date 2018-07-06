#!/usr/bin/python3
import xml.etree.ElementTree as etree
import urllib.request, math, csv, time
import dicts # My script for custom dictionaries
from datetime import datetime
import smtplib, sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from appdirs import AppDirs
from pathlib import Path

def getkey(grp): #Returns API key stored in file
	dirs=AppDirs("nattgew-xpp","Nattgew")
	if grp==0: #User key
		filename=Path(dirs.user_data_dir).joinpath('mykey.txt')
	else: #Group key
		filename=Path(dirs.user_data_dir).joinpath('mygroupkey.txt')
	try:
		with filename.open() as f:
			mykey = f.readline()
			mykey=mykey.strip()
	except IOError:
		print("Could not open key file")
		mykey=""
	return mykey

def getemail(): #Gets email info stored in file
	dirs=AppDirs("nattgew-xpp","Nattgew")
	filename=Path(dirs.user_data_dir).joinpath('creds.txt')
	try:
		with filename.open() as f:
			srvr=f.readline().strip()
			addr=f.readline().strip()
			passw=f.readline().strip()
			addrto=f.readline().strip()
	except IOError:
		print("Could not open email credentials file")
		srv, addr, passw, addrto=("",)*4
	return srvr,addrto,addr,passw

def sendemail(subj,msg): #Sends email
	srvr,addrto,addr,passw=getemail()
	#message="""\From: %s\nTo: %s\nSubject: %s\n\n%s""" % (addr, addrto, subj, msg)
	message = MIMEMultipart('alternative')
	body = MIMEText(msg.encode('utf-8'), 'html', _charset='utf-8')
	message['From'] = addr
	message['To'] = addrto
	message['Subject'] = subj
	message.attach(body)
	try:
		#print("Sending mail from "+addr+" to "+addrto)
		server=smtplib.SMTP_SSL(srvr, 465)
		server.ehlo()
		server.login(addr,passw)
		server.sendmail(addr,addrto,message.as_string())
		server.close()
		#print("Successfully sent the mail:")
	except:
		e = sys.exc_info()[0]
		print("Failed to send the mail with error:")
		print(e)

def isnew(currents,filename):
	#This function prevents repeat notifications for the same situation
	dirs=AppDirs("nattgew-xpp","Nattgew")
	file=Path(dirs.user_data_dir).joinpath(filename+'.txt')
	try:
		file.touch(exist_ok=True) #Create file if it doesn't exist
		print("Checking for low "+str(file))
		repeats=[] #List of items already notified
		with file.open() as f:
			for oldnews in f: #Loop over all shortages in the file
				for current in currents: #Loop over all current shortanges
					if current[0]==oldnews: #Shortage was already listed in the file
						repeats.append(current) #Full list item to be logged and removed from notification list
						break
		with file.open('w') as f: #Overwrite the file with the new list of shortages
			for current in currents:
				f.write(current[0]+"\n")
		for oldie in repeats: #Remove shortages already notified from the list
			currents.remove(oldie)
	except IOError:
		print("Could not open file: "+str(file))
	return currents

def fserequest(ra,rqst,tagname,fmt): #Requests data in format, returns list of requested tag
	if ra==1: #Some queries seem to need this, others don't
		rakey="&readaccesskey="+getkey(0)
	else:
		rakey=""
	rq = "http://server.fseconomy.net/data?userkey="+getkey(0)+rakey+'&format='+fmt+'&'+rqst
	#print("Will make request: "+rq)
	data = urllib.request.urlopen(rq)
	if fmt=='xml':
		tags=readxml(data,tagname,1)
	elif fmt=='csv':
		tags=readcsv(data)
	else:
		print("Format "+fmt+" not recognized!")
		tags=[]
	return tags

def fserequest_new(qry,srch,tagname,fmt,ra,nsb,more=""): #Requests data in format, returns list of requested tag
	if ra==1: #User RA key
		rakey="&readaccesskey="+getkey(0)
	elif ra==2: #Group RA key
		rakey="&readaccesskey="+getkey(1)
	else: #Not needed
		rakey=""
	rq = "http://server.fseconomy.net/data?userkey="+getkey(0)+'&format='+fmt+'&query='+qry+'&search='+srch+more+rakey
	#print("Will make request: "+rq)
	try:
		data = urllib.request.urlopen(rq)
		if fmt=='xml':
			tags=readxml(data,tagname,nsb)
		elif fmt=='csv':
			tags=readcsv(data)
		else:
			print("Format "+fmt+" not recognized!")
			tags=[]
	except:
		e = sys.exc_info()[0]
		print("Failed to send request with error:")
		print(e)
		tags=[]
	return tags

def readxml(data,tagname,nsb): #Parses XML, returns list of requested tagname
	ns = {'sfn': 'http://server.fseconomy.net'} #namespace for XML stuff, required for etree
	#print("Parsing XML data for "+tagname+"...")
	try:
		tree = etree.parse(data)
		#print("Tree:")
		#print(tree)
		try:
			root = tree.getroot()
			#print("Root:")
			#print(root)
			try:
				if nsb==1: #Most queries need the namespace defined, but not all
					error = root.findall('sfn:Error',ns)
				else:
					error = root.findall('Error')
				if error!=[]:
					print("Received error: "+error[0].text)
					tags=[]
				else:
					#print("Finding tag: "+tagname)
					try:
						if nsb==1:
							tags = root.findall('sfn:'+tagname,ns)
						else:
							tags = root.findall(tagname)
					except:
						print("Failed to search for requested tag name")
						tags=[]
			except:
				print("Failed to search for error returned")
				tags=[]
		except:
			print("Failed to get root of XML tree")
			tags=[]
	except:
		print("Failed to parse XML")
		tags=[]
	return tags

def readcsv(data): #Eats Gary's lunch
	#print("Parsing CSV data...")
	try:
		has_header = csv.Sniffer().has_header(data.read(1024))
		data.seek(0) # rewind
		reader = csv.reader(data)
		if has_header:
			next(reader) # skip header row
	except:
		print("Failed to read csv")
		reader = ""
	return reader

def gebtn(field,tag,nsb=1): #Shorter way to get tags
	ns = {'sfn': 'http://server.fseconomy.net'} #namespace for XML stuff
	try:
		if nsb==1:
			tags=field.find('sfn:'+tag,ns).text  #field.getElementsByTagName(tag)[0].firstChild.nodeValue
		else:
			tags=field.find(tag).text  #field.getElementsByTagName(tag)[0].firstChild.nodeValue
	except: #Borked XML, more common than you may think
		print("Bad XML")
		tags=""
	return tags

def getbtns(field,tags): #Shorter way to get list of tags
	ns = {'sfn': 'http://server.fseconomy.net'} #namespace for XML stuff
	vals=[]
	for tag in tags: #Converts value based on second field
		val=gebtn(field,tag[0])
		if tag[1]==1: #Convert to int
			val=int(val)
		elif tag[1]==2: #Convert to float
			val=float(val)
		elif tag[1]==3: #Round float to int
			val=int(float(val))
		vals.append(val)
	return vals

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
	loc_dict=build_csv("latlon")
	lat1,lon1=loc_dict[icaofrom]
	lat2,lon2=loc_dict[icaoto]
	hdg=inithdg(lat1,lon1,lat2,lon2)
	return hdg

def distbwt(icaofrom,icaoto): #Find distance from one airport to another
	loc_dict=build_csv("latlon")
	lat1,lon1=loc_dict[icaofrom]
	lat2,lon2=loc_dict[icaoto]
	dist=cosinedist(lat1,lon1,lat2,lon2)
	return dist

def getdtime(strin): #Return datetime for the Y-M-D H:M input
	adate,atime=strin.split()
	year,month,day=adate.split('-', 2)
	hour,mnt=atime.split(':')
	return datetime(int(year),int(month),int(day),int(hour),int(mnt))

def build_csv(info): #Return a dictionary of info using FSE csv file
	loc_dict = {}
	dirs=AppDirs("nattgew-xpp","Nattgew")
	filename=Path(dirs.user_data_dir).joinpath('icaodata.csv')
	try:
		with filename.open() as f:
			out=readcsv(f)
			for row in out:
				if info=="latlon": #airport coordinates
					loc_dict[row[0]]=(float(row[1]),float(row[2])) #Code = lat, lon
				elif info=="country": #airport countries
					loc_dict[row[0]]=row[8] #Code = Country
	except IOError:
		print("Could not open ICAO data csv")
	return loc_dict

def chgdir(hdg,delt): #Add delta to heading and fix if passing 0 or 360
	hdg+=delt
	if hdg>360:
		hdg-=360
	elif hdg<=0:
		hdg+=360
	return hdg

def dcoord(coord,delta,dirn): # Change coordinate by delta without exceeding a max
	if dirn=='lon':
		lmax=179.9 #TODO: I'll fix this later
	else:
		lmax=89.9
	new=coord+delta
	if new<-lmax:
		new=-lmax
	elif new>lmax:
		nex=lmax
	return new

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
			#print(row)
			lat,lon=loc_dict[row]
		except KeyError: #Probably "Airborne"
			print("Key error on: "+str(row))
			continue #What could possibly go wrong
		locations.append([lat,lon])
		#lat_tot+=lat
		#lon_tot+=lon
		if lat<latmin: #or abs(latmin)>90: #Look for min/max of coordinates
			latmin=lat
		if lat>latmax: #or abs(latmax)>90:  #These abs() things just seem wrong to me
			latmax=lat
		if lon<lonmin: #or abs(lonmin)>180:
			lonmin=lon
		if lon>lonmax: #or abs(lonmax)>180:
			lonmax=lon
	pts=len(locations)
	if pts==0:
		print("No locations found!")
	#else:
		#center=(lat_tot/pts,lon_tot/pts) # Not currently used, also needs the totals above
	return locations,(latmin,lonmin),(latmax,lonmax)

def gettype(icao): #Return name of aircraft type or error if not found
	#Dictionary of ICAO code to aircraft type name
	icaodict=dicts.getactypedict()
	actype="aircraft" #default, if passed blank string
	try:
		if icao!="": #try to look it up
			actype=icaodict[icao]
		success=True
	except (KeyError,IndexError):
		print("Name for code "+icao+" not found!")
		success=False
	return actype, success

def mapper(what, points, mincoords, maxcoords, title): # Put the points on a map
	from mpl_toolkits.basemap import Basemap
	import matplotlib.pyplot as plt
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
		llclo=dcoord(mincoords[1],-0.25*width,'lon') #Lower left corner long
		llcla=dcoord(mincoords[0],-0.25*height,'lat') #Lower left corner lat
		urclo=dcoord(maxcoords[1],0.25*width,'lon') #Upper right corner long
		urcla=dcoord(maxcoords[0],0.25*height,'lat') #Upper right corner lat
		#print("ll="+str(llclo)+","+str(llcla)+"  ur="+str(urclo)+","+str(urcla))
		m = Basemap(projection='cyl', resolution=None, llcrnrlon=llclo, llcrnrlat=llcla, urcrnrlon=urclo, urcrnrlat=urcla)
	#More options based on what we are plotting
	if what=="ac":
		if len(points) < 30: #Use awesome airplane symbol
			verts = list(zip([0.,1.,1.,10.,10.,9.,6.,1.,1.,4.,1.,0.,-1.,-4.,-1.,-1.,-5.,-9.,-10.,-10.,-1.,-1.,0.],[9.,8.,3.,-1.,-2.,-2.,0.,0.,-5.,-8.,-8.,-9.,-8.,-8.,-5.,0.,0.,-2.,-2.,-1.,3.,8.,9.])) #Supposed to be an airplane
			mk=(verts,0)
			ptsize=50
		else: #Use boring but more compact dots
			mk='o'
			ptsize=2
		#print(points)
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
						#print(pts[i][j])
						x, y = m([k[1] for k in pts[i][j]], [k[0] for k in pts[i][j]]) #Populate points
						if j==0: #Set color
							c='#cc9900' #A fuel like color
						elif j==1: #Materials
							c='b'
						else:
							c='k'
						#print(sz)
						m.scatter(x,y,s=sz,marker='o',c=c) #Plot the points with these properties
						for l in range(len(x)):
							gals=int(round(i/2.65)) #Convert kg to gal
							plt.text(x[l]-math.sqrt(sz/100),y[l],"~"+str(gals)+" gal",fontsize=7)
						m.shadedrelief(scale=0.2)
	plt.title(title,fontsize=12)
	plt.show()

def plotdates(dlist,title,ylbl,sym,clr,save): #Plot a list of data vs. dates
	from matplotlib.dates import DateFormatter, date2num
	import matplotlib.pyplot as plt
	#print("sym: ")
	#print(sym)
	#print("clr: ")
	#print(clr)
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
		if len(data[0])==2: #If only 2 fields then just plot them
			#print("Plotting data with symbol "+sym[i]+" and color "+clr[j])
			ax.plot([date2num(x[0]) for x in data], [x[1] for x in data], clr[j]+sym[i], ms=4)
		else: #Extra field is error bar
			#print("Plotting data with symbol "+sym[i]+" and color "+clr[j])
			if clr[j]=='':
				ax.errorbar([date2num(x[0]) for x in data], [x[1] for x in data], yerr=[x[2] for x in data], fmt=sym[i])
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
	#Get range of dates for plot
	daterange=[min(min(date2num(i[0]) for i in j) for j in dlist),max(max(date2num(i[0]) for i in j) for j in dlist)]
	#Get range of prices to use
	if isinstance(dlist[0][0][1], (list, tuple)): #See how deep this rabbit hole goes
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
		plt.savefig('/mnt/data/Dropbox/'+title.replace(' ','_').replace('/','_')+'.png')

def pieplot(data, total, min, stitle): #Create a pie plot... mmm, pie
	import matplotlib.pyplot as plt
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
	if other>0.1: #Include the rest if it's significant
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
