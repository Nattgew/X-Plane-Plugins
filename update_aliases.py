#!/usr/bin/python
#from xml.dom import minidom
import xml.etree.ElementTree as etree
import urllib.request
import os, fileinput, csv

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

def fserequest(ra,rqst,tagname,fmt,ns): #Requests data in format, returns instances requested tag
	if ra==1:
		rakey="&readaccesskey="+getkey()
	else:
		rakey=""
	rq = "http://server.fseconomy.net/data?userkey="+getkey()+rakey+'&format='+fmt+'&'+rqst
	print("Will make request: "+rq)
	data = urllib.request.urlopen(rq)
	if fmt=='xml':
		tags=readxml(data,tagname,ns)
	elif fmt=='csv':
		tags=readcsv(data)
	else:
		print("Format "+fmt+" not recognized!")
		tags=[]
	return tags

def readxml(data,tagname,ns): #Parses XML, returns list of requested tagname
	print("Parsing XML data...")
	tree = etree.parse(data)
	root = tree.getroot()
	error = root.findall('sfn:Error',ns)
	if error!=[]:
		print("Received error: "+error[0].text)
		tags=[]
	else:
		print("Gettings tags: "+tagname)
		tags = root.findall(tagname,ns)
	return tags

def readcsv(data): #Eats Gary's lunch
	print("Parsing CSV data...")
	has_header = csv.Sniffer().has_header(data.read(1024))
	data.seek(0) # rewind
	reader = csv.reader(data)
	if has_header:
		next(reader) # skip header row
	return reader

def getbtns(field,tags, ns): #Shorter way to get list of tags
	vals=[]
	for tag in tags: #Converts value based on second field
		val=field.find(tag[0],ns).text
		if tag[1]==1:
			val=int(val)
		elif tag[1]==2:
			val=float(val)
		elif tag[1]==3:
			val=int(float(val))
		vals.append(val)
	return vals


ns = {'sfn': 'http://server.fseconomy.net'} #namespace for XML stuff
print("Sending request for alias listing...")
aliases = fserequest(0,'query=aircraft&search=aliases','sfn:AircraftAliases','xml',ns)
print("Sending request for configs...")
configs = fserequest(1,'query=aircraft&search=configs','sfn:AircraftConfig','xml',ns)
if configs!=[] and aliases!=[]:
	payloads=[] #Holds payload calculations
	print("Processing data...")
	cfields=(("sfn:MakeModel", 0), ("sfn:MTOW", 1), ("sfn:EmptyWeight", 1))
	aliaslist=[] #holds list of list of aliases
	i=0 #To store which alias we are adding to
	print("Getting payloads...")
	for config in configs: #Calculate payloads
		thisac=getbtns(config, cfields, ns)
		payload=thisac[1]-thisac[2]
		#print(thisac[0],payload)
		payloads.append((thisac[0], payload)) #Store the name and payload
	print("Getting aliases...")
	for model in aliases: #List the aliases
		themake=model.find('sfn:MakeModel',ns).text #Get the make/model
		if themake==payloads[i][0]: #Test if this matches the corresponding payload plane
			print("Appending list for "+themake)
			aliaslist.append([]) #Start a new list of aliases
			for alias in model.findall('sfn:Alias',ns):
				aliaslist[i].append(alias.text) #Add aliases to list
		else: #Something went wrong, this doesn't match up
			print("Config "+thisac[0]+" does not match "+payloads[i][0])
		i+=1
	paylist=[]
	for entry in payloads:
		paylist.append(entry[1])
	print(paylist)
	print(aliaslist)

