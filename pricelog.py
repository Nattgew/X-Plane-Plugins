#!/usr/bin/env python3
import dicts # My script for custom dictionaries
import fseutils # My custom FSE functions
from fsetemplates import html_email_template_basic
import csv, sqlite3, time, math, sys, getopt
from datetime import timedelta, date, datetime
from appdirs import AppDirs
from pathlib import Path

def acforsale(conn): #Log aircraft currently for sale
	#TODO: make friendlier variable names for the lists
	print("Sending request for sales listing...")
	airplanes = fseutils.fserequest_new('aircraft','forsale','Aircraft','xml',0,1)
	if airplanes!=[]:
		print("Recording data...")
		new=1 #Whether to add to new table
		c=getdbcon(conn)
		#d=getdbcon(conn)
		count=getmaxiter(conn)+1 #Index for this new iteration
		now=time.strftime("%Y-%m-%d %H:%M", time.gmtime())
		row=(count, now) #Record time and index of this iteration
		c.execute('BEGIN TRANSACTION')
		c.execute('INSERT INTO queries VALUES (?,?)',row) #Record date/time of this query
		goodones=[] #List of aircraft criteria will be read from file
		dirs=AppDirs("nattgew-xpp","Nattgew")
		filename=Path(dirs.user_data_dir).joinpath('pricewatch.csv')
		with filename.open() as f:
			reader=fseutils.readcsv(f)
			for row in reader:
				goodones.append((row[0],row[1],int(row[2]),int(row[3]))) #actype, icao?, price, hours
		fields=(("SerialNumber", 1), ("MakeModel", 0), ("Location", 0), ("AirframeTime", 0), ("SalePrice", 2))
		rows=[] #List to INSERT, each row is a tuple
		bargains=[] #List of aircraft for sale matching criteria
		oldbargains=[]
		for airplane in airplanes: #Compile list of aircraft for sale
			row=fseutils.getbtns(airplane,fields) #Extract the relevant fields
			row[3]=int(row[3].split(":")[0]) #Get hours as int
			row.append(count) #Add iteration to end
			rows.append(tuple(row)) #Add row as tuple to list
			if new==0:
				for option in goodones: #Check if any sales meet criteria for notify
					if row[1]==option[0] and row[4]<option[2] and row[3]<option[3]:
						pricedelta=option[2]-row[4]
						discount=round((1-row[4]/option[2])*100)
						#bargains.append((option[1],option[1]+" | $"+str(row[4])+" <span class='discount'>(-"+str(pricedelta)+")</span> | "+str(row[3])+" hrs | "+row[2]))
						bargains.append((str(row[0]),option[1],row[4],pricedelta,discount,row[3],row[2]))
		#Keep adding to old table until new one is stable
		#c.executemany('INSERT INTO allac VALUES (?,?,?,?,?,?)',rows) #Add all of the aircraft to the log
		#conn.commit()

		if new==1: #Add to new table
			added=0
			updated=0
			#c.execute('BEGIN TRANSACTION')
			for listing in rows:
				if listing[2]=="In Flight":
					#Don't select based on location of previous log
					c.execute('SELECT loc FROM listings WHERE serial = ? AND price = ? AND lastiter = ?',(listing[0], listing[4], count-1))
				else:
					c.execute('SELECT loc FROM listings WHERE serial = ? AND price = ? AND (loc = ? OR loc = "In Flight") AND lastiter = ?',(listing[0], listing[4], listing[2], count-1))
				result=c.fetchone()
				if result is None: #No exact match on previous iter, add new entry
					newlisting=list(listing)
					newlisting.append(count)
					c.execute('INSERT INTO listings VALUES (?,?,?,?,?,?,?)',([value for value in newlisting]))
					for option in goodones: #Check if any sales meet criteria for notify
						#Moved this here so we can avoid doing an isnew check, we already know it's a new listing
						#This way it will notify if location/price change too
						#TODO: indicate changes in price/location
						#makemodel,type,price,hours
						if listing[1]==option[0] and listing[4]<option[2] and listing[3]<option[3]:
							pricedelta=option[2]-listing[4]
							discount=round((1-listing[4]/option[2])*100)
							#bargains.append((option[1],option[1]+" | $"+str(listing[4])+" <span class='discount'>(-"+str(pricedelta)+")</span> | "+str(listing[3])+" hrs | "+listing[2]))
							#serial(for comparison),type,price,delta,discount,hours,loc
							bargains.append((str(listing[0]),option[1],listing[4],pricedelta,discount,listing[3],listing[2]))
					added+=1
				else: #Exact match, update iter and hours, maybe location too
					for option in goodones: #Check if any sales meet criteria for notify
						#Moved this here so we can avoid doing an isnew check, we already know it's a new listing
						#This way it will notify if location/price change too
						#TODO: indicate changes in price/location
						#makemodel,type,price,hours
						if listing[1]==option[0] and listing[4]<option[2] and listing[3]<option[3]:
							pricedelta=option[2]-listing[4]
							discount=round((1-listing[4]/option[2])*100)
							oldbargains.append((str(listing[0]),option[1],listing[4],pricedelta,discount,listing[3],listing[2]))
					if result[0]=="In Flight":
						#If previous log was "in flight" then update the location too
						#It may still be "in flight" but whatever
						c.execute('UPDATE listings SET lastiter = ?, hours = ?, loc = ? WHERE serial = ? AND lastiter = ?',(count, listing[3], listing[2], listing[0], count-1))
					else:
						#If last log wasn't "in flight" then it must have matched location, or listing is "in flight", don't need to update
						c.execute('UPDATE listings SET lastiter = ?, hours = ? WHERE serial = ? AND lastiter = ?',(count, listing[3], listing[0], count-1))
					#print('-', end='', flush=True)
					updated+=1
			#conn.commit()
			print("Updated "+str(updated)+" and added "+str(added)+" entries for iter "+str(count))

		conn.commit()
		if new==0:
			newbargains=fseutils.isnew(bargains,"bargains")
			for newbargain in newbargains:
				for oldbargain in bargains:
					if oldbargain==newbargain: #Remove the new ones from the bargain list
						bargians.remove(newbargain)
			oldbargains=bargains
			bargains=newbargains #Awkward but this will probably go away soon
		if bargains!=[]: #Found some bargains to send by email
			barglist=""
			for bargain in bargains: #Add new listings to message
				barglist+=bargain[1]+" | $"+str(bargain[2])+" <span class='discount'>(-$"+str(bargain[3])+" "+str(bargain[4])+"%)</span> | "+str(bargain[5])+" hrs | "+bargain[6]+"<br/>"
			if oldbargains!=[]: #Add old listings to message
				barglist+="<br/>Listed aircraft already notified:<br/>"
				for bargain in oldbargains:
					barglist+=bargain[1]+" | $"+str(bargain[2])+" <span class='discount'>(-$"+str(bargain[3])+" "+str(bargain[4])+"%)</span> | "+str(bargain[5])+" hrs | "+bargain[6]+"<br/>"
			if new==1: #Add info about added vs. updated entries in new table
				barglist+="<br/>Updated "+str(updated)+" and added "+str(added)+" entries for iter "+str(count)
			msg=html_email_template_basic.format(aclist=barglist)
			fseutils.sendemail("FSE Aircraft Deals",msg,1)

def salepickens(conn): #Convert log to compact format
	#Making a new table where each entry has a range of observations instead of one
	#This reduces the number of rows for aircraft that continue to show up for sale, at the cost of another column
	#Right now it is set up to optionally group listings by region or country
	#This may not be necessary as there are many rows that are exact duplicates (aircraft does not get flown)
	#See getlistings() for similar behavior
	print("Processing data...")
	region=0 #If 1 then combine entries in same region
	#If 1 then make a separate table matching serial to type
	#I highly doubt I'll do this, it decreases the entry size but not the number of entries
	#It also seriously affects every function that needs to select based on aircraft type
	sndb=0
	c=getdbcon(conn) #For reading old table
	d=getdbcon(conn) #For writing to new table
	rdict=dicts.getregiondict() #Get dictionary of which region each airport is in
	#now=time.strftime("%Y-%m-%d %H:%M", time.gmtime())
	#Create a new table to hold the converted info
	print("Creating new table...")
	c.execute('BEGIN TRANSACTION')
	#Assume new table does not exist
	if sndb==0:
		c.execute('''CREATE TABLE listings
				 (serial int, type text, loc text, hours real, price real, firstiter int, lastiter int)''')
		c.execute('''CREATE INDEX idx_firstiter ON listings(firstiter)''')
		c.execute('''CREATE INDEX idx_type_list ON listings(type)''')
		c.execute('''CREATE INDEX idx_price_list ON listings(price)''')
		c.execute('''CREATE INDEX idx_lastiter ON listings(lastiter)''')
		c.execute('''CREATE INDEX idx_serial_list ON listings(serial)''')
		c.execute('''CREATE INDEX idx_loc_list ON listings(loc)''')
		c.execute('''CREATE INDEX idx_hours_list ON listings(hours)''')
	else:
		c.execute('''CREATE TABLE listings
				 (serial int, loc text, hours real, price real, firstiter int, lastiter int)''')
		c.execute('''CREATE INDEX idx_firstiter ON listings(firstiter)''')
		c.execute('''CREATE INDEX idx_type_list ON listings(serial)''')
		c.execute('''CREATE INDEX idx_price_list ON listings(price)''')
		c.execute('''CREATE INDEX idx_lastiter ON listings(lastiter)''')
		#c.execute('''CREATE INDEX idx5 ON listings(hours)''')
		#Create table for serial numbers
		c.execute('''CREATE TABLE serials (serial int, type text)''')
		c.execute('''CREATE INDEX idx_serial_serials ON serials(serial)''')
		c.execute('''CREATE INDEX idx_type_serials ON serials(type)''')
	#conn.commit()
	maxiter=getmaxiter(conn)
	#d.execute('BEGIN TRANSACTION')
	for i in range(maxiter):
		#Process each query time
		print("Processing iter "+str(i+1)+" of "+str(maxiter)+"... ", end='')
		added=0
		updated=0
		for listing in c.execute('SELECT * FROM allac WHERE obsiter = ?',(i+1,)):
			if sndb==0:
				#All queries but the first
				if i>0: #Look for same airplane, same price, from previous iteration
					if region==0: #Disregard hours, airport must be same
						if listing[2]=="In Flight":
							#Don't select based on location of previous log
							d.execute('SELECT loc FROM listings WHERE serial = ? AND price = ? AND lastiter = ?',(listing[0], listing[4], i))
						else:
							d.execute('SELECT loc FROM listings WHERE serial = ? AND price = ? AND (loc = ? OR loc = "In Flight") AND lastiter = ?',(listing[0], listing[4], listing[2], i))
						result=d.fetchone()
						if result is None: #No exact match on previous iter, add new entry
							newlisting=list(listing)
							newlisting.append(i+1)
							d.execute('INSERT INTO listings VALUES (?,?,?,?,?,?,?)',([value for value in newlisting]))
							#print('+', end='', flush=True)
							added+=1
						else: #Exact match, update iter and hours, maybe location too
							if result[0]=="In Flight":
								#If previous log was "in flight" then update the location too
								#It may still be "in flight" but whatever
								d.execute('UPDATE listings SET lastiter = ?, hours = ?, loc = ? WHERE serial = ? AND lastiter = ?',(i+1, listing[3], listing[2], listing[0], i))
							else:
								#If last log wasn't "in flight" then it must have matched location, or listing is "in flight", don't need to update
								d.execute('UPDATE listings SET lastiter = ?, hours = ? WHERE serial = ? AND lastiter = ?',(i+1, listing[3], listing[0], i))
							#print('-', end='', flush=True)
							updated+=1
					else: #Disregard hours, region must be same
						if listing[2]=="In Flight":
							#Don't select based on location of previous log
							d.execute('SELECT loc FROM listings WHERE serial = ? AND price = ? AND lastiter = ?',(listing[0], listing[4], i))
						else:
							d.execute('SELECT loc FROM listings WHERE serial = ? AND price = ? AND (loc = ? OR loc = "In Flight") AND lastiter = ?',(listing[0], listing[4], listing[2], i))
						result=d.fetchone()
						if result is None or rdict[result[0]]!=rdict[listing[2]]: #No exact match on previous iter for exact or region, add new entry
							newlisting=list(listing)
							newlisting.append(i+1)
							d.execute('INSERT INTO listings VALUES (?,?,?,?,?,?,?)',([value for value in newlisting]))
							#print('+', end='', flush=True)
							added+=1
						else: #Same region, only last iter needs to be updated
							d.execute('UPDATE listings SET lastiter = ?, loc = ?, hours = ? WHERE serial = ? AND lastiter = ?',(i+1, listing[2], listing[3], listing[0], i))
				else: #This is the first iteration, just insert the data
					d.execute('INSERT INTO listings VALUES (?,?,?,?,?,?,1.0)',([value for value in listing]))
			else:
				#All queries but the first
				#TODO - remove type column when copying from old table
				if i>0: #Look for same airplane, same price, from previous iteration
					if region==0: #Disregard hours, airport must be same
						d.execute('SELECT COUNT(*) FROM listings WHERE serial = ? AND price = ? AND (loc = ? OR loc = "In Flight") AND lastiter = ?',(listing[0], listing[4], listing[2], i))
						result=d.fetchone()
						if result[0]==0: #No exact match on previous iter, add new entry
							newlisting=list(listing)
							newlisting.append(i+1)
							d.execute('INSERT INTO listings VALUES (?,?,?,?,?,?,?)',([value for value in newlisting]))
						else: #Exact match, update iter and hours
							d.execute('UPDATE listings SET lastiter = ?, hours = ? WHERE serial = ? AND lastiter = ?',(i+1, listing[3], listing[0], i))
					else: #Disregard hours, region must be same
						d.execute('SELECT loc FROM listings WHERE serial = ? AND price = ? AND loc = ? AND lastiter = ?',(listing[0], listing[4], i))
						result=d.fetchone()
						#Check if location is in same region as previous query
						#TODO: Think about how to handle airborne aircraft here
						if rdict[result[0]]!=rdict[listing[2]]: #Not same region, insert new row
							newlisting=list(listing)
							newlisting.append(i+1)
							d.execute('INSERT INTO listings VALUES (?,?,?,?,?,?,?)',([value for value in newlisting]))
						else: #Same region, only last iter needs to be updated
							d.execute('UPDATE listings SET lastiter = ?, loc = ? WHERE serial = ? AND price = ? AND lastiter = ? AND hours = ?',(i+1, listing[2], listing[0], listing[4], i, listing[3]))
				else: #This is the first iteration, just insert the data
					d.execute('INSERT INTO listings VALUES (?,?,?,?,?,?,1.0)',([value for value in listing]))
		#print('') #Newline
		print("Updated "+str(updated)+" and added "+str(added)+" entries.")
	conn.commit()

def sntotype(conn,sn): #Look up the type of a serial number
	c=getdbcon(conn)
	c.execute('SELECT type FROM serials WHERE serial = ?',(sn,))
	result=c.fetchone()
	return result[0]

def gettypesns(conn,type): #Look up serial numbers for an aircraft type
	c=getdbcon(conn)
	serials=[]
	for row in c.execute('SELECT serial FROM serials WHERE type = ?',(type,)):
		serials.append(row[0])
	return serials

def logpaymonth(conn,fromdate): #Log a month of payments
	year,month,*rest=fromdate.split('-', 2) #Get the year and month from the date
	print("Sending request for payment listing for "+fromdate+"...")
	payments = fseutils.fserequest_new('payments','monthyear','Payment','xml',1,1,'&month='+month+'&year='+year)
	if payments!=[]: #Check if we received any data
		c=getpaydbcon(conn)
		rows=[] #To hold processed rows
		#Fields to log
		fields=(("Date", 0), ("To", 0), ("From", 0), ("Amount", 2), ("Reason", 0), ("Location", 0), ("Id", 1), ("Aircraft", 0), ("Comment", 0))
		print("Processing data...")
		for payment in payments: #Process the results
			#Get all of the fields we want to log
			row=fseutils.getbtns(payment,fields)
			#Set null comments to blank
			if row[8]=="null":
				row[8]=""
			#Replace slashes in date with dashes
			row[0]=row[0].replace('/','-')
			#Add to list for later db insertion
			rows.append(tuple(row))
		#Add all processed rows to db
		print("Adding to database...")
		c.execute('BEGIN TRANSACTION')
		c.executemany('INSERT INTO payments VALUES (?,?,?,?,?,?,?,?,?)',rows)
		conn.commit()
	else:
		print("No payments received for: "+'query=payments&search=monthyear&month='+month+'&year='+year,'Payment')

def logconfigs(conn): #Update database of aircraft configs
	print("Sending request for configs...")
	configs = fseutils.fserequest_new('aircraft','configs','AircraftConfig','xml',1,1)
	if configs!=[]:
		#For reading current db info
		c=getconfigdbcon(conn)
		#For writing any updates
		d=getconfigdbcon(conn)
		#Fields we will log
		fields=(("MakeModel", 0), ("Crew", 1), ("Seats", 1), ("CruiseSpeed", 1), ("GPH", 1), ("FuelType", 1), ("MTOW", 1), ("EmptyWeight", 1), ("Price", 3), ("Ext1", 1), ("LTip", 1), ("LAux", 1), ("LMain", 1), ("Center1", 1), ("Center2", 1), ("Center3", 1), ("RMain", 1), ("RAux", 1), ("RTip", 1), ("Ext2", 1), ("Engines", 1), ("EnginePrice", 3))
		print("Updating config data...")
		#Process each aircraft
		c.execute('BEGIN TRANSACTION')
		for config in configs:
			#Get the fields for this aircraft
			row=fseutils.getbtns(config, fields)
			fcap=0
			for i in range(9,20): #Calc total fuel capacity
				fcap+=row[i]
			#Add total fuel capacity field after the tank fields
			row.insert(20,fcap)
			c.execute('SELECT * FROM aircraft WHERE ac = ?',(row[0],)) #Get stored info for current aircraft
			current=c.fetchone()
			#Check for this aircraft in existing db based on the name
			if current is not None and len(current)>0:
				#Get list of column names, to make sure we don't miss one
				cols=[]
				for col in c.execute('''PRAGMA table_info(aircraft)'''):
					cols.append(col[1])
				for i in range(len(row)):
					if current[i]!=row[i]: #Check if field has changed
						print("Updating "+row[0]+": "+cols[i]+" "+str(current[i])+" -> "+str(row[i]))
						d.execute('UPDATE aircraft SET {} = ? WHERE ac = ?'.format(cols[i]),(row[i], row[0]))
			else:
				#Couldn't find the aircraft in the db, adding new entry
				print("Adding new config: "+row[0])
				c.execute('INSERT INTO aircraft VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',row)
		conn.commit()
		print("Configs up to date")

def getdbcon(conn): #Get cursor for aircraft sale database
	print("Initializing sale database cursor...")
	#Create the cursor, which is the main thing this function is for
	c = conn.cursor()
	#Check if we've already initialized this
	#If we have, none of this is necessary to do again
	if not getdbcon.has_been_called:
		#Check if there are any tables in the db
		#If db does not exist we create a new one
		c.execute("SELECT COUNT(*) FROM sqlite_master WHERE type = 'table'")
		exist=c.fetchone()
		#print("Found " + str(exist[0]) + " tables...")
		if exist[0]==0: #Tables do not exist, create tables
			c.execute('BEGIN TRANSACTION')
			print("No existing table found! Creating tables...")
			c.execute('''CREATE TABLE allac
				 (serial real, type text, loc text, hours real, price real, obsiter real)''')
			c.execute('''CREATE TABLE queries
				 (obsiter real, qtime text)''')
			c.execute('''CREATE INDEX idx_iter ON allac(obsiter)''')
			c.execute('''CREATE INDEX idx_type ON allac(type)''')
			c.execute('''CREATE INDEX idx_price ON allac(price)''')
			c.execute('''CREATE INDEX idx_qtime ON queries(qtime)''')
			c.execute('''CREATE INDEX idx_loc ON allac(loc)''')
			c.execute('''CREATE INDEX idx_hours ON allac(hours)''')
			c.execute('''CREATE TABLE listings
				 (serial int, type text, loc text, hours real, price real, firstiter int, lastiter int)''')
			c.execute('''CREATE INDEX idx_firstiter ON listings(firstiter)''')
			c.execute('''CREATE INDEX idx_type_list ON listings(type)''')
			c.execute('''CREATE INDEX idx_price_list ON listings(price)''')
			c.execute('''CREATE INDEX idx_lastiter ON listings(lastiter)''')
			conn.commit()
		else:
			#Tables already exist, just check on last query time
			c.execute('SELECT qtime FROM queries ORDER BY iter DESC')
			dtime=c.fetchone()
			print("Sale data last updated: "+dtime[0])
		#Remember that this has been called
		getdbcon.has_been_called=True
	#Return the cursor
	return c

def getpaydbcon(conn): #Get cursor for payment database
	#print("Initializing payment database cursor...")
	c = conn.cursor()
	if not getpaydbcon.has_been_called:
		c.execute("SELECT COUNT(*) FROM sqlite_master WHERE type = 'table'")
		exist=c.fetchone()
		if exist[0]==0: #Table does not exist, create table
			print("No payments table found! Creating payment tables...")
			c.execute('BEGIN TRANSACTION')
			c.execute('''CREATE TABLE payments
				 (date text, payto text, payfrom text, amount real, reason text, location text, aircraft text, pid real, comment text)''')
			c.execute('''CREATE INDEX idx_pay_date ON payments(date)''')
			conn.commit()
		else:
			c.execute('SELECT date FROM payments ORDER BY date DESC')
			dtime=c.fetchone()
			print("Last payment data recorded: "+dtime[0])
		getpaydbcon.has_been_called=True
	return c

def getconfigdbcon(conn): #Get cursor for config database
	#print("Initializing config database cursor...")
	c = conn.cursor()
	if not getconfigdbcon.has_been_called:
		c.execute("SELECT COUNT(*) FROM sqlite_master WHERE type = 'table'")
		exist=c.fetchone()
		if exist[0]==0: #Table does not exist, create table
			print("No config table found! Creating config tables...")
			c.execute('BEGIN TRANSACTION')
			c.execute('''CREATE TABLE aircraft
				 (ac text, crew real, seats real, cruise real, gph real, fuel real, mtow real, ew real, price real, ext1 real, ltip real, laux real, lmain real, c1 real, c2 real, c3 real, rmain real, raux real, rtip real, ext2 real, fcap real, eng real, engprice real)''')
			c.execute('''CREATE INDEX idx_conf_ac ON aircraft(ac)''')
			c.execute('''CREATE INDEX idx_conf_price ON aircraft(price)''')
			c.execute('''CREATE INDEX idx_conf_mtow ON aircraft(mtow)''')
			c.execute('''CREATE INDEX idx_conf_ew ON aircraft(ew)''')
			c.execute('''CREATE INDEX idx_conf_fcap ON aircraft(fcap)''')
			conn.commit()
		getconfigdbcon.has_been_called=True
	return c

def getmaxiter(conn): #Return the number of latest query, which is also the total number of queries (YES IT IS SHUT UP)
	c = conn.cursor()
	c.execute('SELECT iter FROM queries ORDER BY iter DESC')
	count=c.fetchone()
	#print("Found "+str(count)+" previous queries")
	if count is not None:
		current=int(count[0])
	else:
		current=0
	return current

def gettimeforsale(conn,timetype): # Get data for all ac of timetype for sale
	#Returns list, containing a list for each aircraft, which lists all times it was for sale
	#For reading all serials
	c=getdbcon(conn)
	#For reading the price and date of each serial
	d=getdbcon(conn)
	#For reading the query info
	e=getdbcon(conn)
	print("Getting sales data for "+timetype+"...")
	listings=[]
	i=0
	#(serial real, type text, loc text, locname text, hours real, price real, obsiter real)
	#for dac in c.execute('SELECT DISTINCT serial FROM allac WHERE type = ?',(timetype,)):
	for dac in c.execute('SELECT DISTINCT serial FROM listings WHERE type = ?',(timetype,)):
		#Add a list to the list
		listings.append([])
		#for qp in d.execute('SELECT price, obsiter FROM allac WHERE serial = ?',(dac[0],)):
		for qp in d.execute('SELECT price, firstiter, lastiter FROM listings WHERE serial = ?',(dac[0],)):
			for j in range(qp[1],qp[2]): #Add each iter in the range to the list
				qtime=e.execute('SELECT qtime FROM queries WHERE iter = ?',(j,)) #Get date/time of this iter
				date=fseutils.getdtime(e.fetchone()[0])
				#print("AC: "+str(dac[0])+"  "+str(date)+": "+str(qp[0]))
				#Add this listing to the list for this aircraft
				listings[i].append([date,int(float(qp[0]))])
		i+=1 #Move on to new serial
	return listings

def gettotals(conn,actype,fr,to): #Return list of total aircraft for sale at each query time
	#For getting relevant queries
	c=getdbcon(conn)
	#For getting number of aircraft
	d=getdbcon(conn)
	#List, each entry will be a tuple of datetime and total
	totals=[]
	print("Finding total aircraft for sale from "+fr+" to "+to+"...")
	for query in c.execute('SELECT * FROM queries WHERE qtime BETWEEN ? AND ?', (fr,to)):
		#print("Reading query "+str(query[0])+" from "+query[1])
		if actype=="aircraft":
			#Count all aircraft
			#d.execute('SELECT COUNT(*) FROM allac WHERE obsiter = ?', (query[0],))
			d.execute('SELECT COUNT(*) FROM listings WHERE ? BETWEEN firstiter AND lastiter', (query[0],))
		else:
			#Count a specific aircraft type
			#d.execute('SELECT COUNT(*) FROM allac WHERE obsiter = ? AND type = ?', (query[0],actype))
			d.execute('SELECT COUNT(*) FROM listings WHERE (? BETWEEN firstiter AND lastiter) AND type = ?', (query[0],actype))
		total=int(d.fetchone()[0])
		#Add datetime and total to the list
		totals.append((fseutils.getdtime(query[1]),total))
	return totals

def getaverages(conn,actype,fr,to): #Return list of average prices for aircraft in each query time
	#TODO: throw out values well outside the stdev
	#Find relevant queries
	c=getdbcon(conn)
	#Select price of listings
	d=getdbcon(conn)
	#List containing tuples of datetime,average,stdev
	averages=[]
	fr=fr+" 00:01" #Add times to match the format in table
	to=to+" 23:59"
	print("Finding averages for: "+actype+" from "+fr+" to "+to+"...")
	for query in c.execute('SELECT * FROM queries WHERE qtime BETWEEN ? AND ?', (fr,to)): #Find the queries in this time range
		#Total planes, for calculating average
		numforsale=0
		#Total price, for calculating average
		totalprice=0
		#List of prices for calculating stdev
		prices=[]
		#Get prices for this query and aircraft type
		#for sale in d.execute('SELECT price FROM allac WHERE obsiter = ? AND type = ?', (query[0],actype)):
		for sale in d.execute('SELECT price FROM listings WHERE (? BETWEEN firstiter AND lastiter) AND type = ?', (query[0],actype)):
			#Add to total price
			totalprice+=int(sale[0])
			#Add price to list
			prices.append(sale[0])
			#Add one for total aircraft
			numforsale+=1
		if numforsale>0:
			#Calculate average price
			avg=totalprice/numforsale
			#Sum of squares
			ssprice=0
			#Sum the squares
			for price in prices:
				ssprice+=math.pow(price-avg,2)
			#Calculate stdev
			stdev=math.sqrt(ssprice/numforsale)
			#Add this to the list
			averages.append((fseutils.getdtime(query[1]),avg,stdev))
	return averages

def getbaseprice(actype): #Return the base price for this actype
	#Open the db where this information lives
	dirs=AppDirs("nattgew-xpp","Nattgew")
	filename=str(Path(dirs.user_data_dir).joinpath('configs.db'))
	conn=sqlite3.connect(filename)
	c=getconfigdbcon(conn)
	for i in range(2):
		c.execute('SELECT price FROM aircraft WHERE ac = ?',(actype,))
		price=c.fetchone()
		if price is not None:
			baseprice=price[0]+73333 #Add equipment price, assume fully loaded
			break
		elif i==1: #Updated configs and still no match, give up and return 0
			baseprice=0
			break
		logconfigs(conn) #No match, try updating the configs?
	conn.close()
	return baseprice

def getlows(conn,actype,fr,to): #Return list of lowest price for aircraft in each query
	#For getting relevant queries
	c=getdbcon(conn)
	#For getting prices
	d=getdbcon(conn)
	#List with tuples of datetime,low price
	lows=[]
	print("Finding low low prices for: "+actype+"...")
	for query in c.execute('SELECT * FROM queries WHERE qtime BETWEEN ? AND ?', (fr,to)):
		#Order by price for this type and get the lowest one
		#d.execute('SELECT price FROM allac WHERE obsiter = ? AND type = ? ORDER BY price', (query[0],actype))
		d.execute('SELECT price FROM listings WHERE (? BETWEEN firstiter AND lastiter) AND type = ? ORDER BY price', (query[0],actype))
		price=d.fetchone()
		if price is not None:
			#If we got a valid price add to list
			lows.append((fseutils.getdtime(query[1]),price))
	return lows

def getfuelprices(conn): #Plot fuel prices over time
	#For getting payments from db
	c=getpaydbcon(conn)
	print("Getting flight logs...")
	#One list entry per day
	#Each entry is list of total for gallons and money
	dgas=[]
	#List of datetime,avg,stdev for each day
	dprice=[]
	#List of payments, with date and price per gal
	eprice=[]
	i=-1
	#(date text, payto text, payfrom text, amount real, reason text, location text, aircraft text, pid real, comment text)
	for log in c.execute('SELECT date, amount, comment FROM payments WHERE reason = "Refuelling with JetA" ORDER BY date'):
		#comment in log[2] = User ID: xxxxx Amount (gals): 428.9, $ per Gal: $3.75
		#Extract gallons based on position of colon and comma
		gals=float(log[2].split(':',3)[2].split(',')[0])
		#Extracts price per gallon based on position of colon and dollar sign
		pergal=float(log[2].split(':',3)[3].replace(' $',''))
		pdate=log[0].split()[0] #Get just date portion
		#print("i="+str(i)+"  len(dgas)="+str(len(dgas)))
		if len(dgas)>0 and dgas[i][0]==pdate:
			#print("Adding "+str(gals)+" gals")
			dgas[i][1]+=gals #Keep total of gallons
			dgas[i][2]+=log[1] #Keep total of money
		else:
			#print("New day with "+str(gals)+" gals")
			i+=1
			#Add a new row for this day, initialize with current payment data
			dgas.append([pdate,gals,log[1]])
		#Add this payment date and price per gallon to list
		eprice.append([pdate,pergal])
	for day in dgas: #Calculate stats for each day
		#Calculate average price/gal for this day
		avg=day[2]/day[1]
		#For sum of squares
		ssprice=0
		#For number of payments
		num=0
		for price in eprice:
			#Find payments in list matching this day
			if price[0]==day[0]:
				#Add to sum of squares
				ssprice+=math.pow(price[1]-avg,2)
				#Another payment
				num+=1
		#Calculate stdev
		stdev=math.sqrt(ssprice/num)
		#print("New day "+day[0]+" with "+str(avg)+" per gal, sd "+str(stdev))
		#Add datetime,avg,stdev to list that we will return
		dprice.append((fseutils.getdtime(day[0]+" 00:01"),avg,stdev))
	return dprice

def getcommo(ctype): # Adds up locations and quantities of stuff to send to the mapper
	#This lets us use t1,t2 for either fuel or material
	if ctype=="fuel":
		t1="JetA Fuel"
		t2="100LL Fuel"
	elif ctype=="mtrl":
		t1="Supplies"
		t2="Building materials"
	else:
		print("Commodity type "+ctype+" not recognized!")
	if t1 is not None:
		print("Sending request for commodities...")
		commo = fseutils.fserequest_new('commodities','key','Commodity','xml',1,1)
		print("Sorting results...")
		#For list of the commodity we are looking for
		stuff = []
		for item in commo: #Parse commodity info
			#Find the type of commodity
			typ = fseutils.gebtn(item, "Type")
			if typ==t1 or typ==t2:
				#If it's the type we want, get location and amount
				loc = fseutils.gebtn(item, "Location")
				amt = fseutils.gebtn(item, "Amount")
				#Add to list of commodities
				stuff.append((loc,typ,amt))
		if stuff!=[]: #Add up quantity per location
			qty=[] #List to hold locations, quantities and types
			#The stuff list returns t1 and t2 amounts as separate entries
			#We will combine this into one entry per location here
			for item in stuff:
				match=-1
				i=-1
				for prev in qty:
					i+=1
					if item[0]==qty[0]: #Test if the location has already been added
						match=1
						break
				if match==-1: #If location not added, then add new location/quantity
					#Value of idx indicates type of commodity here
					if item[1]==t1:
						idx=0
					else: #t2
						idx=1
					#Add location, amount, and type code
					qty.append([item[0],int(item[2].split()[0]),idx])
				else: #If location already added, then sum with other quantity
					qty[i][1]+=item[2].split() #Add quantity to existing value
					qty[i][2]=2 #idx 2 indicates a mix of t1 and t2
			#Get list of coordinates for the airports
			coords,cmin,cmax=fseutils.getcoords(i[0] for i in qty)
			if len(coords)==len(qty): #If not, there was some key error I guess
				#List to hold coordinates and quantities, for mapping
				locations=[]
				print("Working with "+str(len(coords))+" coords...")
				for i in range(len(coords)):
					print("Apending "+str(coords[i][0])+","+str(coords[i][1])+","+str(qty[i][1])+","+str(qty[i][2]))
					#Add the coordinates, quantities, and types to list
					locations.append([coords[i][0],coords[i][1],qty[i][1],qty[i][2]])
				return locations,cmin,cmax
			else:
				print("Could not find coords for all airports!")
		else:
			print("No "+ctype+" found!")

def getlistings(conn,actype,lo,hi): #Return list of time for aircraft to sell
	#For getting query info
	c=getdbcon(conn)
	#For getting listings
	d=getdbcon(conn)
	#For getting dictionary listing country of each airport
	cdict=fseutils.build_csv("country")
	#For getting dctionary listing region of each country
	rdict=dicts.getregiondict()
	#For holding the listing data
	listings=[]
	print("Finding sell times for: "+actype+", "+str(lo)+" to "+str(hi)+"...")
	for query in c.execute('SELECT obsiter FROM queries'):
	#serial real, type text, loc text, locname text, hours real, price real, obsiter real
		#for sale in d.execute('SELECT serial, loc, price FROM allac WHERE obsiter = ? AND type = ? AND price BETWEEN ? AND ?', (query[0],actype,lo,hi)):
		for sale in d.execute('SELECT serial, loc, price FROM listings WHERE (? BETWEEN firstiter AND lastiter) AND type = ? AND price BETWEEN ? AND ?', (query[0],actype,lo,hi)):
			#Look up the country
			country=cdict[sale[1]]
			#Look up the region of the country
			region=rdict[country]
			match=0
			for i in range(len(listings)):
				#Check if this serial is already in list
				if sale[0]==listings[i][0]:
					#Check if region and price are the same
					if region==listings[i][1] and sale[2]==listings[i][2]:
						listings[i][4]=query[0] #Update "to" date in current list
						match=1
					else: #Price/region changed, assume not sold, remove old listing and will append a new one
						listings.remove(listings[i])
					break
			if match==0: #New/updated listing: SN, region, price, first iter, last iter
				listings.append([sale[0],region,int(sale[2]),query[0],query[0]])
	return listings

def mapaclocations(conn, actype): #Map locations of aircraft type for sale
	#For getting listing data
	c=getdbcon(conn)
	#Get most recent iteration
	iters=getmaxiter(conn)
	#q1="SELECT loc FROM allac WHERE obsiter = "+str(iters) #To allow adding to query
	q1="SELECT loc FROM listings WHERE "+str(iters)+" BETWEEN firstiter AND lastiter" #To allow adding to query
	#Check if we were passed an aircraft type
	if actype=="":
		#Title for the map
		title="Locations of all aircraft for sale"
	else:
		#Add to query the aircraft type
		q1+=" AND type = '"+actype+"'"
		title="Locations of "+actype+" for sale"
	#Gett coordinates for the airports
	locations,cmin,cmax=fseutils.getcoords([i[0] for i in c.execute(q1)])
	#If we got locations then map them
	if len(locations)>0:
		fseutils.mapper('ac', locations, cmin, cmax, title)

def plotpayments(conn,fromdate,todate): #Plot payment totals per category
	#For getting the payment data
	c=getpaydbcon(conn)
	#Get user name
	user=fseutils.getname()
	#timedelta of one day
	delta=timedelta(days=1)
	#Fields for from date
	fyear,fmonth,fday=fromdate.split('-', 2)
	#Fields for to date
	tyear,tmonth,tday=todate.split('-', 2)
	#Make dates for from and to
	fdate=date(int(fyear),int(fmonth),int(fday))
	tdate=date(int(tyear),int(tmonth),int(tday))
	#Initialize the payment lists
	rentexp, rentinc, assnmtexp, assnmtinc, pltfee, addcrewfee, gndcrewfee, bkgfee, ref100, refjet, mxexp, eqinstl, acsold, acbought, fboref100, fborefjet, fbogndcrew, fborepinc, fborepexp, fboeqpexp, fboeqpinc, ptrentinc, ptrentexp, fbosell, fbobuy, wsbuy100, wssell100, wsbuyjet, wsselljet, wsbuybld, wssellbld, wsbuysupp, wssellsupp, grpay=([[fdate,0]] for i in range(34))
	#List of list names
	allthat=[rentexp, rentinc, assnmtexp, assnmtinc, pltfee, addcrewfee, gndcrewfee, bkgfee, ref100, refjet, mxexp, eqinstl, acsold, acbought, fboref100, fborefjet, fbogndcrew, fborepinc, fborepexp, fboeqpexp, fboeqpinc, ptrentinc, ptrentexp, fbosell, fbobuy, wsbuy100, wssell100, wsbuyjet, wsselljet, wsbuybld, wssellbld, wsbuysupp, wssellsupp, grpay]
	#Category names for the different payment types, and corresponding lists
	#[1] is income, [2] is expense
	categories=[("Rental of aircraft", rentinc, rentexp),
				("Pay for assignment", assnmtinc, assnmtexp),
				("Crew fee", addcrewfee, addcrewfee),
				("FBO ground crew fee", fbogndcrew, gndcrewfee),
				("Booking Fee", bkgfee, bkgfee),
				("Refuelling with JetA", fborefjet, refjet),
				("Refuelling with 100LL", fboref100, ref100),
				("Aircraft maintenance", fborepinc, mxexp),
				("Aircraft sale", acsold, acbought),
				("Sale of wholesale JetA", wsselljet, wsbuyjet),
				("Sale of wholesale 100LL", wssell100, wsbuy100),
				("Sale of supplies", wssellsupp, wsbuysupp),
				("Sale of building materials", wssellbld, wsbuybld),
				("Group payment", grpay, grpay),
				("Pilot fee", pltfee, pltfee),
				("Installation of equipment in aircraft", fboeqpinc, eqinstl)]
	i=0
	print('Tallying daily payments from %i-%i to %i-%i...' % (fdate.year,fdate.month,tdate.year,tdate.month))
	#(date text, to text, from text, amount real, reason text, location real, aircraft real)
	while fdate <= tdate:
		#From and to dates to use in query
		fdateq=fdate.isoformat()+" 00:00:01" #To match logged format
		tdateq=fdate.isoformat()+" 23:59:59"
		if i>0:
			for var in allthat:
				#Carry over the previous totals to new date
				var.append([fdate,var[i-1][1]])
		#Get all of the payments between the from and to dates
		for payment in c.execute('SELECT payfrom, amount, reason FROM payments WHERE date BETWEEN ? AND ?',(fdateq,tdateq)):
			for cat in categories:
				if payment[2]==cat[0]: #Test if category name matches
					if payment[0]!=user: #If payment not from user, it is income
						cat[1][i][1]+=payment[1]
					else: #It is expense
						cat[2][i][1]+=payment[1]
					break
		#Next day
		fdate += delta
		i += 1
	#I guess we're just plotting these expenses for now
	fseutils.plotdates([refjet, addcrewfee, gndcrewfee],"Money","Money",['-'],None,0)

def sumpayments(conn,fdate,tdate): #Plot portion of income/expense per category
	c=getpaydbcon(conn)
	#Income
	rentinc=[0,"Rental income"]
	assnmtinc=[0,"Assignment income"]
	acsold=[0,"Aircraft sold"]
	fboref100=[0,"100LL pumped"]
	fborefjet=[0,"JetA pumped"]
	fbogndcrew=[0,"Ground crew income"]
	fborepinc=[0,"Repair income"]
	fboeqpinc=[0,"Eqp instl income"]
	ptrentinc=[0,"PT rent income"]
	fbosell=[0,"FBO sold"]
	wssell100=[0,"100LL sold"]
	wsselljet=[0,"JetA sold"]
	wssellbld=[0,"Building materials sold"]
	wssellsupp=[0,"Supplies sold"]
	grpay=[0,"Group payment"]
	#Expenses
	rentexp=[0,"Rental expense"]
	assnmtexp=[0,"Assignment expense"]
	pltfee=[0,"Pilot fees"]
	addcrewfee=[0,"Additional crew fee"]
	gndcrewfee=[0,"Ground crew fee"]
	bkgfee=[0,"Booking fee"]
	ref100=[0,"100LL pumped"]
	refjet=[0,"JetA pumped"]
	mxexp=[0,"Maintenance"]
	eqinstl=[0,"Equipment installed"]
	acbought=[0,"Aircraft bought"]
	fborepexp=[0,"FBO repair cost"]
	fboeqpexp=[0,"FBO eqp instl"]
	fbobuy=[0,"FBO bought"]
	wsbuy100=[0,"100LL bought"]
	wsbuyjet=[0,"JetA bought"]
	wsbuybld=[0,"Building materials"]
	wsbuysupp=[0,"Supplies"]
	ownership=[0,"Ownership Fee"]
	categories=[("Rental of aircraft", rentinc, rentexp), #Tag name, if to, if from
				("Pay for assignment", assnmtinc, assnmtexp),
				("Crew fee", addcrewfee, addcrewfee),
				("FBO ground crew fee", fbogndcrew, gndcrewfee),
				("Booking Fee", bkgfee, bkgfee),
				("Refuelling with JetA", fborefjet, refjet),
				("Refuelling with 100LL", fboref100, ref100),
				("Aircraft maintenance", fborepinc, mxexp),
				("Aircraft sale", acsold, acbought),
				("Sale of wholesale JetA", wsselljet, wsbuyjet),
				("Sale of wholesale 100LL", wssell100, wsbuy100),
				("Sale of supplies", wssellsupp, wsbuysupp),
				("Sale of building materials", wssellbld, wsbuybld),
				("Group payment", grpay, grpay),
				("Pilot fee", pltfee, pltfee),
				("Installation of equipment in aircraft", fboeqpinc, eqinstl),
				("Ownership Fee", ownership, ownership)]
	user=fseutils.getname()
	fromdate=fdate+" 00:01"
	todate=tdate+" 23:59"
	print("Tallying payments from "+str(fdate[0])+"-"+str(fdate[1])+" to "+str(tdate[0])+"-"+str(tdate[1])+"...")
	#(date text, to text, from text, amount real, reason text, location real, aircraft real)
	for payment in c.execute('SELECT payfrom, amount, reason FROM payments WHERE date BETWEEN ? AND ?',(fromdate,todate)):
		for cat in categories:
			if payment[2]==cat[0]:
				if payment[0]!=user:
					cat[1][0]+=payment[1]
				else:
					cat[2][0]+=payment[1]
				break
	#Income nets per category
	rent=[rentinc[0]-rentexp[0],"Rental"]
	assnmt=[assnmtinc[0]-assnmtexp[0],"Assignments"]
	ac=[acsold[0]-acbought[0],"Aircraft"]
	ws100=[fboref100[0]+wssell100[0]-wsbuy100[0],"WS 100LL"]
	wsjet=[fborefjet[0]+wsselljet[0]-wsbuyjet[0],"WS JetA"]
	fborep=[fborepinc[0]-fborepexp[0],"FBO Repairs"]
	fboeqp=[fboeqpinc[0]-fboeqpexp[0],"FBO Eqp Instl"]
	ptrent=[ptrentinc[0],"PT Rent"]
	fbo=[fbosell[0]-fbobuy[0],"FBO"]
	sup=[wssellsupp[0]-wsbuysupp[0],"Supplies"]
	bld=[wssellbld[0]-wsbuybld[0],"Building Mtrls"]
	incnets=[rent, assnmt, ac, ws100, wsjet, fborep, fboeqp, ptrent, fbo, sup, bld]
	incnet=[]
	expnet=[ref100, refjet, bkgfee, gndcrewfee, addcrewfee, pltfee, mxexp, ownership] #Always negative
	netinc=0
	netexp=ref100[0]+refjet[0]+bkgfee[0]+gndcrewfee[0]+addcrewfee[0]+pltfee[0]+mxexp[0]+ownership[0]
	for net in incnets: #Test if category represents an expense or income
		if net[0]>0: #That's based on whether it's negative, this isn't rocket science
			incnet.append(net)
			netinc+=net[0]
		else:
			expnet.append(net)
			netexp+=net[0]
	fseutils.pieplot(incnet,netinc,5,"Income sources")
	fseutils.pieplot(expnet,netexp,5,"Expense sources")
	#Totals income/expenses
	revs=[rentinc, assnmtinc, acsold, fboref100, fborefjet, fbogndcrew, fborepinc, fboeqpinc, ptrentinc, fbosell, wssell100, wsselljet, wssellbld, wssellsupp]
	exps=[rentexp, assnmtexp, pltfee, addcrewfee, gndcrewfee, bkgfee, ref100, refjet, mxexp, eqinstl, acbought, fborepexp, fboeqpexp, fbobuy, wsbuy100, wsbuyjet, wsbuybld, wsbuysupp]
	fseutils.pieplot(revs,None,5,"Revenues")
	fseutils.pieplot(exps,None,5,"Expenses")

def sumacpayments(conn,fdate,tdate): #Plot revenue portion by aircraft
	c=getpaydbcon(conn)
	d=getpaydbcon(conn)
	#Income
	rent=[[],"Rental income"]
	assnmtinc=[[],"Assignment income"]
	#Expenses
	pltfee=[[],"Pilot fees"]
	addcrewfee=[[],"Additional crew fee"]
	gndcrewfee=[[],"Ground crew fee"]
	bkgfee=[[],"Booking fee"]
	ref100=[[],"100LL pumped"]
	refjet=[[],"JetA pumped"]
	mxexp=[[],"Maintenance"]
	eqinstl=[[],"Equipment installed"]
	acbuy=[[],"Aircraft bought"]
	z=[[],""]
	items=[rent,assnmtinc,pltfee,addcrewfee,gndcrewfee,bkgfee,ref100,refjet,mxexp,eqinstl,acbuy,z]
	categories=[("Rental of aircraft", rent, rent),
				("Pay for assignment", assnmtinc, z),
				("Crew fee", addcrewfee, addcrewfee),
				("FBO ground crew fee", z, gndcrewfee),
				("Booking Fee", z, bkgfee),
				("Refuelling with JetA", z, refjet),
				("Refuelling with 100LL", z, ref100),
				("Aircraft maintenance", z, mxexp),
				("Aircraft sale", acbuy, acbuy),
				("Pilot fee", pltfee, pltfee),
				("Installation of equipment in aircraft", z, eqinstl)]
	user=fseutils.getname()
	fromdate=fdate+" 00:01"
	todate=tdate+" 23:59"
	ac=[]
	i=-1
	print("Tallying payments from"+str(fdate[0])+"-"+str(fdate[1])+" to "+str(tdate[0])+"-"+str(tdate[1])+"...")
	#(date text, payto text, payfrom text, amount real, reason text, location text, aircraft text)
	for dac in c.execute('SELECT DISTINCT aircraft FROM payments WHERE date BETWEEN ? AND ? AND payto = ? AND reason = "Pay for assignment"',(fromdate,todate,user)):
		ac.append([0,dac[0]])
		for var in items:
			var[0].append(0) # Initialize with 0 values for this aircraft
		i+=1
		for payment in d.execute('SELECT payfrom, amount, reason FROM payments WHERE date BETWEEN ? AND ? AND aircraft = ?',(fromdate,todate,dac[0])):
			for cat in categories:
				if payment[2]==cat[0]:
					if payment[0]!=user:
						cat[1][0][i]+=payment[1]
					else:
						cat[2][0][i]-=payment[1]
					break
	for i in range(len(ac)): #Sum up all categories for each aircraft
		for var in items:
			ac[i][0]+=var[0][i]
		ac[i][0]-=z[0][i] #z is for garbage, take this back out
		i+=1
	fseutils.pieplot(ac,None,5,"Aircraft Income")

def main(argv): #This is where the magic happens
	#TODO: Make sure that functions can consistently take an option to map all aircraft/dates if none is given
	syntaxstring=("pricelog.py -acdgm <aircraft> -hjknpqsuvz -e <fuel/mtrls> -ft <YYYY-MM-DD> -il <price>\n"
			" Options:\n"
			"   -a, --average     Plots average prices for a type (type required)\n"
			"   -c, --cheapest    Plots cheapest prices for a type (type required)\n"
			"   -d, --duration    Plots time for a type to sell (type required) (in work)\n"
			"   -e, --commodity   Maps locations and amounts of commodities (type required)\n"
			"   -g, --total       Plots total aircraft for sale of type (type aircraft for all)\n"
			"   -h, --help        Prints this info\n"
			"   -j                Plots fuel prices averaged for each day\n"
			"   -k                Updates aircraft configuration database\n"
			"   -m, --map         Plots location of a type for sale (no type will map all)\n"
			"   -p                Logs a month of payments (--from required)\n"
			"   -q                Plots payment totals (--from and --to, or will print all data)\n"
			"   -s                Plots payment percentages (--from and --to, or will print all data)\n"
			"   -u                Logs aircraft currently for sale\n"
			"   -v                Plots percentage of payment categories per aircraft (--from and --to, or will print all data)\n"
			"   -w                Plots prices for aircraft specified in file\n"
			"   -y, --timeforsale Plots prices for a certain aircraft over time (type required)\n"
			"   -z                Temporary function: add comments to logs\n"
			" Parameters:\n"
			"   -f, --from        From date\n"
			"   -t, --to          To date\n"
			"   -i, --high        Highest price\n"
			"   -l, --low         Lowest price\n")
	try: #_b___________no__r_____x__
		opts, args = getopt.getopt(argv,"a:c:d:e:f:g:h:i:jkl:m:pqst:uvwy:z",["duration=","map=","average=","cheapest=","from=","to=","low=","high=","total=","help=","commodity=","timeforsale="])
	except getopt.GetoptError:
		print(syntaxstring)
		sys.exit(2)
	#Initialize all options as false
	tot, avg, low, dur, pay, ppay, spay, stot, com, lowprice, fuel, domap, sale, tots, pout, tfs=(False,)*16
	getdbcon.has_been_called=False #To know when it's the first cursor initialized
	getpaydbcon.has_been_called=False
	getconfigdbcon.has_been_called=False
	#Defaults
	highprice=99999999
	#TODO: Make default date range from first data to last data instead of hardcoded range
	fromdate="2014-01-01"
	todate="2020-12-31"
	dirs=AppDirs("nattgew-xpp","Nattgew")
	for opt, arg in opts:
		if opt in ("-a", "--average"): #Plots average prices for type
			avgtype,avg=fseutils.gettype(arg)
		elif opt in ("-c", "--cheapest"): #Plots the cheapest aircraft of this type
			lowtype,low=fseutils.gettype(arg)
		elif opt in ("-d", "--duration"): #Calculates duration to sell for a type (in work)
			durtype,dur=fseutils.gettype(arg)
		elif opt in ("-e", "--commodity"): #Maps locations and amounts of commodities
			locations,cmin,cmax=getcommo(arg)
			fseutils.mapper(arg, locations, cmin, cmax, "Locations of Commodities")
		elif opt in ("-f", "--from"): #First date to be used in different functions
			fromdate=arg
		elif opt in ("-g", "--total"): #Plots total aircraft of this type for sale
			tottype,tot=fseutils.gettype(arg)
		elif opt in ("-h", "--help"): #plshelp
			print(syntaxstring)
			sys.exit() #kthxbye
		elif opt in ("-i", "--high"): #Highest price to be considered in other functions
			highprice=arg
		elif opt=="-j": #Plots fuel prices, averaged for each day
			fuel=True
		elif opt=="-k": #Updates the configuration database
			#The only function that needs this db up front, get connection
			filename=str(Path(dirs.user_data_dir).joinpath('configs.db'))
			cconn=sqlite3.connect(filename)
			logconfigs(cconn)
			cconn.close()
		elif opt in ("-l", "--low"): #Lowest price to be considered in other functions
			lowprice=arg
		elif opt in ("-m", "--map"): #Map locations of a type for sale
			maptype,domap=fseutils.gettype(arg)
		elif opt=="-p": #Log a month of payments based on the date given
			pay=True
		elif opt=="-q": #Plots payment totals over date range
			ppay=True
		elif opt=="-s": #Plots payment percentage per category
			spay=True
		elif opt in ("-t", "--to"): #Last date to be used in different functions
			todate=arg
		elif opt=='-u': #Logs the aircraft currently for sale
			sale=True
		elif opt=="-v": #Plots the percentages of payment categories per aircraft
			stot=True
		elif opt=="-w": #Saves plots for aircraft specified in a file
			#TODO: input the file name to use
			pout=True
		elif opt in ("-y", "--timeforsale"): #Plots sale prices per aircraft over time
			timetype,tfs=fseutils.gettype(arg)
		elif opt=="-z": #Temporary - Converts db to fancy new format
			com=True
	print("Running option...")
	
	#Functions using the payments db
	if True in (pay, ppay, spay, stot, fuel):
		filename=str(Path(dirs.user_data_dir).joinpath('payments.db'))
		conn=sqlite3.connect(filename)
		if pay:
			logpaymonth(conn,fromdate)
		if ppay:
			plotpayments(conn,fromdate,todate)
		if spay:
			sumpayments(conn,fromdate,todate)
		if stot:
			sumacpayments(conn,fromdate,todate)
		#if com:
			#logpaymonthcom(conn,fromdate)
		if fuel:
			prices=getfuelprices(conn)
			fseutils.plotdates([prices],"Average fuel price","Price",['o-'],None,0)
		conn.close()

	#Functions using the aircraft sale db
	if True in (tot, avg, low, dur, domap, sale, tots, pout, tfs, com):
		filename=str(Path(dirs.user_data_dir).joinpath('forsale.db'))
		conn=sqlite3.connect(filename)
		if domap:
			mapaclocations(conn,maptype)
		if sale:
			acforsale(conn)
		if tfs:
			times=gettimeforsale(conn,timetype)
			bprice=getbaseprice(timetype)
			#Add a range to plot the base price
			times.append([[fseutils.getdtime("2014-01-01 00:01"),bprice],[fseutils.getdtime("2100-12-31 23:59"),bprice]])
			fseutils.plotdates(times,"Prices of "+timetype,"Price",['o-','--'],[None,'r'],0)
		if tot:
			totals=gettotals(conn,tottype,fromdate,todate)
			fseutils.plotdates([totals],"Number of "+tottype+" for sale","Aircraft",['o-'],None,0)
		if avg:
			averages=getaverages(conn,avgtype,fromdate,todate)
			bprice=getbaseprice(avgtype)
			#Add a range to plot the base price
			baseprice=[[fseutils.getdtime("2014-01-01 00:01"),bprice],[fseutils.getdtime("2100-12-31 23:59"),bprice]]
			fseutils.plotdates([averages,baseprice],"Average price for "+avgtype,"Price",['o-','--'],['b','r'],0)
		if low:
			lows=getlows(conn,lowtype,fromdate,todate)
			bprice=getbaseprice(lowtype)
			#Add a range to plot the base price
			baseprice=[[fseutils.getdtime("2014-01-01 00:01"),bprice],[fseutils.getdtime("2100-12-31 23:59"),bprice]]
			fseutils.plotdates([lows,baseprice],"Lowest price for "+lowtype,"Price",['o-','--'],['b','r'],0)
		if dur:
			#Get a list of listing duration for type and price range
			listings=getlistings(conn,durtype,lowprice,highprice)
			durations=[]
			#Compute durations for each listing
			for listing in listings:
				duration=listings[4]-listings[3]
				durations.append((listings[2],duration))
				print(str(listings[2])+": "+str(duration))
			fseutils.plotdates([durations],"Time to sell for "+durtype,"Days",['o-'],None,0)
		if pout:
			actypes=[]
			#Open the file specifying what types to plot
			filename=Path(dirs.user_data_dir).joinpath('dailytypes.txt')
			with filename.open() as f:
				for actype in f:
					actype=actype.strip() #strip newline
					ptype,ret=fseutils.gettype(actype)
					if ret: #Test if aircraft type was recognized
						#Get low price for each type
						lows=getlows(conn,ptype,fromdate,todate)
						bprice=getbaseprice(ptype)
						#Add range to plot base price
						baseprice=[[fseutils.getdtime("2014-01-01 00:01"),bprice],[fseutils.getdtime("2100-12-31 23:59"),bprice]]
						print("Saving figure for "+actype)
						fseutils.plotdates([lows,baseprice],"Lowest price for "+ptype,"Price",['o-','--'],['b','r'],1)
		if com:
			salepickens(conn)
		conn.close()
	print("Finished!")

if __name__ == "__main__":
   main(sys.argv[1:])
