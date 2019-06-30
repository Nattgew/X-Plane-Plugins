#!/usr/bin/python3

import fseutils # My custom FSE functions
from appdirs import AppDirs
from pathlib import Path

def reldist(icao): #Find distances of other airports from given airport
	#print("Looking for airports near "+icao)
	loc_dict=fseutils.build_csv("latlon")
	clat,clon=loc_dict[icao] #Get coordinates of current airport
	dists=[]
	for apt,coords in loc_dict.items():
		if apt!=icao:
			#print("Dist from "+str(clat)+" "+str(clon)+" to "+str(coords[0])+" "+str(coords[1]))
			dist=fseutils.cosinedist(clat,clon,coords[0],coords[1])
			dists.append((apt,dist))
	return sorted(dists, key=lambda dist: dist[1])

def getshops(icao):
	services=fseutils.fserequest_new('icao','fbo','FBO','xml',1,1,'&icao='+icao)
	options=[]
	if len(services)>0:
		for opt in services:
			thisfbo=fseutils.getbtns(opt, [("Status", 0), ("RepairShop", 0)])
			if thisfbo==["Active", "Yes"]:
				options.append(tuple(fseutils.getbtns(opt, [("Name", 0), ("Owner", 0)])))
	return options

def isnew(needfixes):
	#This function prevents repeat notifications for the same aircraft
	#A list of aircraft needing repair is stored in a text file
	dirs=AppDirs("nattgew-xpp","Nattgew")
	filename=Path(dirs.user_data_dir).joinpath('aog.txt')
	try:
		filename.touch(exist_ok=True) #Create file if it doesn't exist
		oldnews=[] #List of aircraft needing fixes already notified
		with filename.open() as f:
			for aog in f: #Loop over all aircraft in the file
				aog=aog.strip()
				#print("Checking for previously AOG: "+aog)
				for current in needfixes: #Loop over all aircraft currently in need of repair
					#print("Testing current AOG: "+current[0])
					if current[0]==aog: #Aircraft was already listed in the file
						#print("Matched, adding to list")
						oldnews.append(current)
						break
		#print("Came up with oldnews:")
		#print(oldnews)
		with filename.open('w') as f: #Overwrite the file with the new list of aircraft
			for current in needfixes:
				#print("Writing "+current[0]+" to file")
				f.write(current[0]+"\n")
		#print("Will remove oldnews from needfixes list:")
		#print(needfixes)
		for oldie in oldnews: #Remove aircraft already notified from the list
			#print("Removing "+oldie[0]+" from notify list")
			needfixes.remove(oldie)
	except IOError:
		print("Could not open file: "+str(filename))
	return needfixes

ns = {'sfn': 'http://server.fseconomy.net'} #namespace for XML stuff
aog=[] #List of planes and FBO options
print("Sending request for aircraft list...")
airplanes = fseutils.fserequest_new('aircraft','key','Aircraft','xml',1,1)
print("Received airplane list:")
print(airplanes)
for plane in airplanes:
	nr=int(plane.find('sfn:NeedsRepair',ns).text) #Indications repair is needed
	since100=int(plane.find('sfn:TimeLast100hr',ns).text.split(":")[0])
	mx=0
	print("Repair: "+str(nr)+"  100hr: "+str(since100))
	if nr>0:
		mx=1
	if since100>99: #100 hr past due
		mx=2
	if mx>0: #Something is broken
		row=fseutils.getbtns(plane, [("Registration", 0), ("MakeModel", 0), ("Location", 0)]) #License and registration please
		print("Finding repair options for "+row[0])
		shops=getshops(row[2]) #Get list of shops here
		if len(shops)==0: #Start looking around
			relatives=reldist(row[2]) #List of all airports sorted by closest to this one
			for neighbor in relatives:
				shops.append(getshops(neighbor[0])) #Got any gwapes?
				if len(shops)>1: #Get a couple of options
					break
		aog.append((row[0],row[1],row[2],mx,shops)) #Reg, Type, Loc, repair, options
print(aog)
aog=fseutils.isnew(aog,"aog") #Remove aircraft already notified
print(aog)
msg="Airplanes in need of repair:"
#print(msg)
if len(aog)>0:
	for plane in aog:
		#Type of repair needed
		if plane[3]==1:
			repair="repair"
		else:
			repair="100-hour"
		#Add airplane and location to message
		out=plane[0]+"  "+plane[1]+" at "+plane[2]
		msg+="\n"+out
		#print(out)
		#Add type of repair and shop options to message
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
print(msg)
