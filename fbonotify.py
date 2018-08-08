#!/usr/bin/python3
import fseutils # My custom FSE functions
from pathlib import Path
from appdirs import AppDirs

cautdays = 14 #Days of supplies to first send first notification
cautjeta = 1000 #Gallons of Jet A to first send first notification
caut100ll = 1000 #Gallons of 100LL to first send first notification
warndays = 0 #Second notifications
warnjeta = 0
warn100ll = 0
print("Sending request for FBO list...")
commo = fseutils.fserequest_new('fbos','key','FBO','xml',2,0)
#print(commo)
lowjeta = []
low100ll = []
lowsupp = []
nojeta = []
no100ll = []
nosupp = []
for fbo in commo: #Parse commodity info
	#print(fbo)
	icao = fseutils.gebtn(fbo,"Icao",0)
	#print("ICAO="+icao)
	f100 = int(fseutils.gebtn(fbo,"Fuel100LL",0))
	#print("f100="+str(f100))
	fja = int(fseutils.gebtn(fbo,"FuelJetA",0))
	#print("fja="+str(fja))
	days = int(fseutils.gebtn(fbo,"SuppliedDays",0))
	#print("days="+str(days))
	if fja<1:
		nojeta.append((icao,str(round(fja/2.65))))
	elif fja/2.65 <= cautjeta:
		lowjeta.append((icao,str(round(fja/2.65))))
		#print(lowjeta)
	if f100 < 1:
		no100ll.append((icao,str(round(f100/2.65))))
	elif f100/2.65 <= caut100ll:
		low100ll.append((icao,str(round(f100/2.65))))
		#print(low100ll)
	if days <= warndays:
		nosupp.append((icao,str(days)))
	elif days <= cautdays:
		lowsupp.append((icao,str(days)))
		#print(lowsupp)
#print(msg)
lowjeta=fseutils.isnew(lowjeta,"lowjeta")
low100ll=fseutils.isnew(low100ll,"low100ll")
lowsupp=fseutils.isnew(lowsupp,"lowsupp")
nojeta=fseutils.isnew(nojeta,"nojeta")
no100ll=fseutils.isnew(no100ll,"no100ll")
nosupp=fseutils.isnew(nosupp,"nosupp")
print("Building message...")
msg=""

def supmsg(clist,no,type):
	msg=""
	if len(clist)>0:
		amt="NO " if no==1 else "low "
		unit=" days"  if type=="supplies" else " gals"
		msg+="Airports with "+amt+type+":\n"
		for airport in clist:
			msg+=airport[0]+" - "+airport[1]+unit+"\n"
		msg+="\n"
	return msg

for clist in nosupp,lowsupp,nojeta,lowjeta,no100ll,low100ll:
	msg+=supmsg(clist)

# if len(nosupp)>0:
	# msg+="Airports with NO supplies:\n"
	# for airport in nosupp: #Add airport and qty to message
		# msg+=airport[0]+" - "+airport[1]+" days\n"
	# msg+="\n"
# if len(lowsupp)>0:
	# msg+="Airports with low supplies:\n"
	# for airport in lowsupp: #Add airport and qty to message
		# msg+=airport[0]+" - "+airport[1]+" days\n"
	# msg+="\n"
# if len(nojeta)>0:
	# msg+="Airports with NO Jet A:\n"
	# for airport in nojeta: #Add airport and qty to message
		# msg+=airport[0]+" - "+airport[1]+" gals\n"
	# msg+="\n"
# if len(lowjeta)>0:
	# msg+="Airports with low Jet A:\n"
	# for airport in lowjeta: #Add airport and qty to message
		# msg+=airport[0]+" - "+airport[1]+" gals\n"
	# msg+="\n"
# if len(no100ll)>0:
	# msg+="Airports with NO 100LL:\n"
	# for airport in no100ll: #Add airport and qty to message
		# msg+=airport[0]+" - "+airport[1]+" gals\n"
	# msg+="\n"
# if len(low100ll)>0:
	# msg+="Airports with low 100LL:\n"
	# for airport in low100ll: #Add airport and qty to message
		# msg+=airport[0]+" - "+airport[1]+" gals\n"
	# msg+="\n"
#print(msg)
if msg!="":
	print("Sending FBO shortage report")
	fseutils.sendemail("FSE FBO Shortages",msg)
else:
	print("No new shortages to report")
