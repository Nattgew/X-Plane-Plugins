#!/usr/bin/python3
import fseutils # My custom FSE functions

ns = {'sfn': 'http://server.fseconomy.net'} #namespace for XML stuff
print("Sending request for alias listing...")
#aliases = fserequest(0,'query=aircraft&search=aliases','sfn:AircraftAliases','xml',ns)
aliases = fseutils.fserequest_new('aircraft','aliases','AircraftAliases','xml',0,1)
print("Sending request for configs...")
#configs = fserequest(1,'query=aircraft&search=configs','sfn:AircraftConfig','xml',ns)
configs = fseutils.fserequest_new('aircraft','configs','AircraftConfig','xml',1,1)
if configs!=[] and aliases!=[]:
	payloads=[] #Holds payload calculations
	print("Processing data...")
	#cfields=(("sfn:MakeModel", 0), ("sfn:MTOW", 1), ("sfn:EmptyWeight", 1))
	cfields=(("MakeModel", 0), ("MTOW", 1), ("EmptyWeight", 1))
	aliaslist=[] #holds list of list of aliases
	i=0 #To store which alias we are adding to
	print("Getting payloads...")
	for config in configs: #Calculate payloads
		#thisac=getbtns(config, cfields, ns)
		thisac=fseutils.getbtns(config, cfields)
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
