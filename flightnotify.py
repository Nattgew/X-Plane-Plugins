#!/usr/bin/python
import smtplib, sys
import fseutils # My custom FSE functions
#import dicts # My script for custom dictionaries
# import os, re, fileinput, csv, sqlite3
import time #locale
from datetime import timedelta, date, datetime

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

def printsleep(towait):
	print("Reaching 10 requests/min limit, sleeping "+str(towait)+" secs.")
	for i in range(towait):
		print('Resuming in '+str(towait-i)+' seconds...   ', end='\r')
		time.sleep(1)
	print('Hopefully we have appeased the rate limiter gods, resuming requests')

requests=0
i=0 #Index of plane in list
foundlogs=0
daysago=2 #How many days back to go
k=0 #Index of month in list
listofdays=[]
listofmonths=[]
today = date.today()
month=today.month
year=today.year
day=today.day
listofmonths.append(month)
for j in range(daysago):
	history=today - timedelta(j+1)
	listofdays.append(history)
#	print(str(listofdays[j].month)+"/"+str(listofdays[j].day))
	if history.month!=listofmonths[k]:
		listofmonths.append(history.month)
		k+=1
me=fseutils.getname()
ns = {'sfn': 'http://server.fseconomy.net'} #namespace for XML stuff
plogs=[]
firstrqtime=int(time.time())
print("Sending request for aircraft list...")
requests+=1
airplanes = fseutils.fserequest_new('aircraft','key','Aircraft','xml',1,1)
#print(airplanes)
print("Processing list...")
for plane in airplanes:
	thisac=fseutils.getbtns(plane, [("Registration", 0), ("MakeModel", 0), ("SerialNumber", 0)])
	plogs.append((thisac[0],[]))
	for eachmonth in listofmonths:
		if requests>8:
			printsleep(120)
			requests=0
		print("Sending request for "+thisac[0]+" ("+thisac[2]+") logs for "+str(eachmonth)+"/"+str(year)+"...")
		requests+=1
		logs=fseutils.fserequest_new('flightlogs','monthyear','FlightLog','xml',0,1,'&serialnumber='+thisac[2]+'&month='+str(month)+'&year='+str(year))
		print("Processing "+str(len(logs))+" logs...")
		for flt in logs:
			fltime = flt.find('sfn:Time', ns).text
			thepilot=flt.find('sfn:Pilot', ns).text
			#print(thepilot+" at "+fltime)
			#2016/02/04 02:48:34
			fltdtime = datetime.strptime(fltime, '%Y/%m/%d %H:%M:%S')
			if thepilot!=me:
				inrange=0
				#print("Testing 3p flight: "+thepilot+" on "+str(fltdtime.month)+"/"+str(fltdtime.day))
				for eachday in listofdays:
					if fltdtime.day==eachday.day:
						inrange=1
						break
				if inrange==1:
					#print("Flight found: "+thepilot+" on "+str(fltdtime.month)+"/"+str(fltdtime.day))
					logtype=flt.find('sfn:Type', ns).text
					row=[logtype,thepilot]
					if logtype=="flight":
						row.extend(fseutils.getbtns(flt, [("From", 0), ("To", 0), ("FlightTime", 0), ("Bonus", 2)]))
					elif logtype=="refuel":
						row.extend(fseutils.getbtns(flt, [("FuelCost", 2)]))
					plogs[i][1].append(row)
					foundlogs+=1
	i+=1

numdays=len(listofdays)
if numdays==1:
	daystr=str(listofdays[0].month)+"/"+str(listofdays[0].day)
else:
	daystr=str(listofdays[0].month)+"/"+str(listofdays[0].day)+"-"+str(listofdays[numdays-1].month)+"/"+str(listofdays[numdays-1].day)
msg="Airplane rentals on "+daystr+":\n"
print(msg)
if foundlogs>0:
	print(plogs)
	for plane in plogs:
		if plane[1]!=[]:
			#print("Adding flights to message for "+plane[0])
			msg+="\n"+plane[0]+":\n"
			for thislog in plane[1]:
				if thislog[0]=="flight":
					msg+=thislog[2]+"-"+thislog[3]+"  "+thislog[4]+"  $"+str(thislog[5])+"  "+thislog[1]+"\n"
				elif thislog[0]=="refuel":
					msg+="Refuel: $"+str(thislog[2])+"  "+thislog[1]+"\n"
	fseutils.sendemail("FSE Aircraft Activity",msg)
#print()
#print(msg)
