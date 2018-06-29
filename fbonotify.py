#!/usr/bin/python
import smtplib, sys
import fseutils # My custom FSE functions
from pathlib import Path

def isnew(newdearth,file):
	#This function prevents repeat notifications for the same shortage
	#A list of airports with shortages is stored in a text file
	filename=Path(file+'.txt')
	if not filename.is_file():
		filename.touch()
	print("Checking for low "+file)
	oldnews=[] #List of shortages already notified
	with open(filename, 'r+') as f:
		for olddearth in f: #Loop over all shortages in the file
			for current in newdearth: #Loop over all current shortanges
				if current[0]==olddearth: #Shortage was already listed in the file
					oldnews.append(current)
					break
	with open(filename, 'w') as f: #Overwrite the file with the new list of shortages
		for current in newdearth:
			f.write(current[0]+"\n")
	for oldie in oldnews: #Remove shortages already notified from the list
		newdearth.remove(oldie)
	return newdearth

warndays = 14 #Days of supplies to first send warning
warnjeta = 1000 #Gallons of Jet A to first send warning
warn100ll = 1000 #Gallons of 100LL to first send warning
print("Sending request for FBO list...")
commo = fseutils.fserequest_new('fbos','key','FBO','xml',2,0)
print(commo)
lowjeta = []
low100ll = []
lowsupp = []
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
	if fja/2.65 < warnjeta+1:
		lowjeta.append((icao,round(fja/2.65)))
	if f100 < warn100ll+1:
		low100ll.append((icao,round(f100/2.65)))
	if days < warndays+1:
		lowsupp.append((icao,days))
#print(msg)
lowjeta=isnew(lowjeta,"lowjeta")
low100ll=isnew(low100ll,"low100ll")
lowsupp=isnew(lowsupp,"lowsupp")
print("Building message...")
msg=""
if len(lowsupp)>0:
	msg+="Airports with low supplies:\n"
	for airport in lowsupp: #Add airport and qty to message
		msg+=airport[0]+" - "+str(airport[1])+" days\n"
	msg+="\n"
if len(lowjeta)>0:
	msg+="Airports with low Jet A:\n"
	for airport in lowjeta: #Add airport and qty to message
		msg+=airport[0]+" - "+str(airport[1])+" gals\n"
	msg+="\n"
if len(low100ll)>0:
	msg+="Airports with low 100LL:\n"
	for airport in low100ll: #Add airport and qty to message
		msg+=airport[0]+" - "+str(airport[1])+" gals\n"
	msg+="\n"
#print(msg)
if msg!="":
	fseutils.sendemail("FSE FBO Shortages",msg)
