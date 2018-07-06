#!/usr/bin/python3
import smtplib, sys
import fseutils # My custom FSE functions
from pathlib import Path
from appdirs import AppDirs

def isnew(newdearth,file): #TODO: Add this to fseutils
	#This function prevents repeat notifications for the same shortage
	#A list of airports with shortages is stored in a text file
	dirs=AppDirs("nattgew-xpp","Nattgew")
	filename=Path(dirs.user_data_dir).joinpath(file+'.txt')
	try:
		filename.touch(exist_ok=True) #Create file if it doesn't exist
		print("Checking for low "+str(file))
		oldnews=[] #List of shortages already notified
		with filename.open() as f:
			for olddearth in f: #Loop over all shortages in the file
				for current in newdearth: #Loop over all current shortanges
					if current[0]==olddearth: #Shortage was already listed in the file
						oldnews.append(current)
						break
		with filename.open('w') as f: #Overwrite the file with the new list of shortages
			for current in newdearth:
				f.write(current[0]+"\n")
		for oldie in oldnews: #Remove shortages already notified from the list
			newdearth.remove(oldie)
	except IOError:
		print("Could not open file: "+str(file))
	return newdearth

cautdays = 14 #Days of supplies to first send first notification
cautjeta = 1000 #Gallons of Jet A to first send first notification
caut100ll = 1000 #Gallons of 100LL to first send first notification
warndays = 0 #Second notifications
warnjeta = 0
warn100ll = 0
print("Sending request for FBO list...")
commo = fseutils.fserequest_new('fbos','key','FBO','xml',2,0)
print(commo)
lowjeta = []
low100ll = []
lowsupp = []
nojeta = []
no100ll = []
nosupp = []
for fbo in commo: #Parse commodity info
	#print(fbo)
	icao = fseutils.gebtn(fbo,"Icao",0)
	print("ICAO="+icao)
	f100 = int(fseutils.gebtn(fbo,"Fuel100LL",0))
	print("f100="+str(f100))
	fja = int(fseutils.gebtn(fbo,"FuelJetA",0))
	print("fja="+str(fja))
	days = int(fseutils.gebtn(fbo,"SuppliedDays",0))
	print("days="+str(days))
	if fja<1:
		nojeta.append((icao,round(fja/2.65)))
	elif fja/2.65 < warnjeta+1:
		lowjeta.append((icao,round(fja/2.65)))
	if f100 < 0:
		no100ll.append((icao,round(f100/2.65)))
	elif f100 < warn100ll+1:
		low100ll.append((icao,round(f100/2.65)))
	if days < 1:
		nosupp.append((icao,days))
	elif days < warndays+1:
		lowsupp.append((icao,days))
#print(msg)
lowjeta=isnew(lowjeta,"lowjeta")
low100ll=isnew(low100ll,"low100ll")
lowsupp=isnew(lowsupp,"lowsupp")
nojeta=isnew(lowjeta,"nojeta")
no100ll=isnew(low100ll,"no100ll")
nosupp=isnew(lowsupp,"nosupp")
print("Building message...")
msg=""
#TODO: functions for these?
if len(nosupp)>0:
	msg+="Airports with NO supplies:\n"
	for airport in nosupp: #Add airport and qty to message
		msg+=airport[0]+" - "+airport[1]+" days\n"
	msg+="\n"
if len(lowsupp)>0:
	msg+="Airports with low supplies:\n"
	for airport in lowsupp: #Add airport and qty to message
		msg+=airport[0]+" - "+airport[1]+" days\n"
	msg+="\n"
if len(nojeta)>0:
	msg+="Airports with NO Jet A:\n"
	for airport in nojeta: #Add airport and qty to message
		msg+=airport[0]+" - "+airport[1]+" gals\n"
	msg+="\n"
if len(lowjeta)>0:
	msg+="Airports with low Jet A:\n"
	for airport in lowjeta: #Add airport and qty to message
		msg+=airport[0]+" - "+airport[1]+" gals\n"
	msg+="\n"
if len(no100ll)>0:
	msg+="Airports with NO 100LL:\n"
	for airport in no100ll: #Add airport and qty to message
		msg+=airport[0]+" - "+airport[1]+" gals\n"
	msg+="\n"
if len(low100ll)>0:
	msg+="Airports with low 100LL:\n"
	for airport in low100ll: #Add airport and qty to message
		msg+=airport[0]+" - "+airport[1]+" gals\n"
	msg+="\n"
#print(msg)
if msg!="":
	print("Sending FBO shortage report")
	fseutils.sendemail("FSE FBO Shortages",msg)
else:
	print("No new shortages to report")
