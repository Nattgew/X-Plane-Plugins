#!/usr/bin/python
import smtplib, sys
import fseutils # My custom FSE functions
#import dicts # My script for custom dictionaries
# import os, re, fileinput, csv, sqlite3
# import locale, time
# from datetime import timedelta, date, datetime
# from mpl_toolkits.basemap import Basemap
# from matplotlib.dates import DateFormatter, date2num
# import matplotlib.pyplot as plt

def reldist(icao,rad): #Find distances of other airports from given airport
	#print("Looking for airports near "+icao)
	loc_dict=fseutils.build_csv("latlon")
	clat,clon=loc_dict[icao]
	dists=[]
	for apt,coords in loc_dict.items():
		if apt!=icao:
			#print("Dist from "+str(clat)+" "+str(clon)+" to "+str(coords[0])+" "+str(coords[1]))
			dist=fseutils.cosinedist(clat,clon,coords[0],coords[1])
			dists.append((apt,dist))
	return sorted(dists, key=lambda dist: dist[1])

def getshops(icao):
	services=fseutils.fserequest(1,'query=icao&search=fbo&icao='+icao,'FBO','xml')
	options=[]
	if len(services)>0:
		for opt in services:
			thisfbo=fseutils.getbtns(opt, [("Status", 0), ("RepairShop", 0)])
			if thisfbo==["Active", "Yes"]:
				options.append(tuple(fseutils.getbtns(opt, [("Name", 0), ("Owner", 0)])))
	return options

def isnew(needfixes):
	oldnews=[]
	fixed=[]
	with open('aog.txt', 'r+') as f:
		for aog in f:
			for current in needfixes:
				if current[0]==aog:
					oldnews.append(current[0])
					break
	with open('aog.txt', 'w') as f:
		for current in needfixes:
			f.write(current[0])
	for oldie in oldnews:
		needfixes.remove(oldie)
	return needfixes

ns = {'sfn': 'http://server.fseconomy.net'} #namespace for XML stuff
aog=[] #List of planes and FBO options
#print("Sending request for aircraft list...")
airplanes = fseutils.fserequest(1,'query=aircraft&search=key','Aircraft','xml')
#print(airplanes)
for plane in airplanes:
	nr=int(plane.find('sfn:NeedsRepair', ns).text) #Indications repair is needed
	since100=int(plane.find('sfn:TimeLast100hr', ns).text.split(":")[0])
	mx=0
	#print(str(nr)+" "+str(since100))
	if nr>0:
		mx=1
	if since100>99: #100 hr past due
		mx=2
	if mx>0: #Something is broken
		row=fseutils.getbtns(plane, [("Registration", 0), ("MakeModel", 0), ("Location", 0)]) #License and registration please
		shops=getshops(row[2]) #Get list of shops here
		if len(shops)==0: #Start looking around
			relatives=reldist(row[2]) #List of all airports sorted by closest to this one
			for neighbor in relatives:
				shops=getshops(neighbor[0]) #Got any gwapes?
				if len(shops)>0:
					break
		aog.append((row[0],row[1],row[2],mx,shops)) #Reg, Type, Loc, repair, options
aog=isnew(aog)
srvr,addrto,addr,passw=fseutils.getemail()
msg="Airplanes in need of repair:"
#print(msg)
if len(aog)>0:
	for plane in aog:
		if plane[3]==1:
			repair="repair"
		else:
			repair="100-hour"
		out=plane[0]+"  "+plane[1]+" at "+plane[2]
		msg+="\n"+out
		#print(out)
		out="Needs "+repair+", options are:"
		msg+="\n"+out
		#print(out)
		for opt in plane[4]:
			out=opt[0]+" owned by "+opt[1]
			msg+="\n"+out
			#print(out)
		msg+="\n"
		#print()
	fseutils.sendemail("FSE Aircraft Mx",msg)
else:
	msg+="\nNone"
#print()
#print(msg)
