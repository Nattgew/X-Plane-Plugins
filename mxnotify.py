#!/usr/bin/python
from xml.dom import minidom
import urllib.request, math, smtplib
#import dicts # My script for custom dictionaries
# import os, re, fileinput, csv, sqlite3
# import locale, time
# from datetime import timedelta, date, datetime
# from mpl_toolkits.basemap import Basemap
# from matplotlib.dates import DateFormatter, date2num
# import matplotlib.pyplot as plt

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

def getemail(): #Gets email info stored in file
	with open('emailfile', 'r') as f:
		addr=f.readline().strip()
		uname=f.readline().strip()
		passw=f.readline().strip()
		return addr,uname,passw

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

def nearest(icao,rad): #Find distances of other airports from given airport
	#print("Looking for airports near "+icao)
	loc_dict=build_csv("latlon")
	clat,clon=loc_dict[icao]
	dists=[]
	for apt,coords in loc_dict.items():
		if apt!=icao:
			#print("Dist from "+str(clat)+" "+str(clon)+" to "+str(coords[0])+" "+str(coords[1]))
			dist=cosinedist(clat,clon,coords[0],coords[1])
			dists.append((apt,dist))
	return sorted(dists, key=lambda dist: dist[1])

def cosinedist(lat1,lon1,lat2,lon2): #Use cosine to find distance between coordinates
	phi1 = math.radians(lat1)
	phi2 = math.radians(lat2)
	dellamb = math.radians(lon2-lon1)
	R = 3440.06479 # Nmi
	# gives d in Nmi
	d = math.acos( math.sin(phi1)*math.sin(phi2) + math.cos(phi1)*math.cos(phi2) * math.cos(dellamb) ) * R
	return int(round(d))

def getshops(icao):
	services=fserequest(1,'query=icao&search=fbo&icao='+icao,'FBO','xml')
	options=[]
	if len(services)>0:
		for opt in services:
			thisfbo=getbtns(opt, [("Status", 0), ("RepairShop", 0)])
			if thisfbo==["Active", "Yes"]:
				options.append(tuple(getbtns(opt, [("Name", 0), ("Owner", 0)])))
	return options

aog=[] #List of planes and FBO options
print("Sending request for aircraft list...")
airplanes = fserequest(1,'query=aircraft&search=key','Aircraft','xml')
for plane in airplanes:
	row=getbtns(plane, [("NeedsRepair", 1), ("TimeLast100hr", 0)]) #Indications repair is needed
	since100=int(row[1].split(":")[0])
	mx=0
	if row[0]>0: #Needs repair
		mx=1
	if since100>100: #100 hr past due
		mx+=2
	if mx>0: #Something is broken
		row=getbtns(plane, [("Registration", 0), ("MakeModel", 0), ("Location", 0)]) #License and registration please
		shops=getshops(row[2]) #Get list of shops here
		if len(shops)==0: #Start looking around
			relatives=nearest(row[2]) #List of all airports sorted by closest to this one
			for neighbor in relatives
				shops=getshops(neighbor[0]) #Got any gwapes?
				if len(shops)>0:
					break
		aog.append((row[0],row[1],row[2],mx,shops)) #Reg, Type, Loc, repair, options
msg="Airplanes in need of repair:"
print(msg)
if len(aog)>0:
	for plane in aog:
		if plane[3]==1:
			repair="repair"
		elif plane[3]==2:
			repair="100-hour"
		else:
			repair="repair and 100-hr"
		out=plane[0]+"  "+plane[1]+" at "+plane[2]
		msg+="\n"+out
		print(out)
		out="Needs "+repair+", options are:"
		msg+="\n"+out
		print(out)
		for opt in plane[4]:
			out=opt[0]+" owned by "+opt[1]
			msg+="\n"+out
			print(out)
		msg+="\n"
		print()
	print(msg)
	addr,uname,passw=getemail()
	server=smtplib.SMTP('smtp.gmail.com:587')
	server.starttls()
	server.login(uname,passw)
	server.sendmail(addr,addr,msg)
	server.quit()
else:
	print("None")
