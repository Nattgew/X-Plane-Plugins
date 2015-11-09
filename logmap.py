#!/usr/bin/python
import math, sys, getopt, csv, sqlite3
import dicts # My script for custom dictionaries
from datetime import timedelta, date, datetime
from mpl_toolkits.basemap import Basemap
from matplotlib.dates import DateFormatter, date2num
import matplotlib.pyplot as plt

def readcsv(data): #Eats Gary's lunch
	print("Parsing CSV data...")
	has_header = csv.Sniffer().has_header(data.read(1024))
	data.seek(0) # rewind
	reader = csv.reader(data)
	if has_header:
		next(reader) # skip header row
	return reader

def getlogdbcon(conn): #Get cursor for log database
	#print("Initializing log database cursor...")
	c = conn.cursor()
	if not getlogdbcon.has_been_called:
		c.execute("SELECT COUNT(*) FROM sqlite_master WHERE type = 'table'")
		exist=c.fetchone()
		if exist[0]==0: #Table does not exist, create table
			print("Creating log database tables...")
			c.execute('''CREATE TABLE logs
				 (fid real, type text, date text, dist real, sn real, ac text, model text, dep text, arr text, fltime text, income real, pfee real, crew real, bkfee real, bonus real, fuel real, gndfee real, rprice real, rtype text, runits text, rcost real)''')
			c.execute('''CREATE INDEX idx1 ON logs(date)''')
			c.execute('''CREATE INDEX idx2 ON logs(type)''')
			c.execute('''CREATE INDEX idx3 ON logs(dist)''')
			c.execute('''CREATE INDEX idx4 ON logs(model)''')
			c.execute('''CREATE INDEX idx5 ON logs(ac)''')
		else:
			c.execute('SELECT date FROM logs ORDER BY date DESC')
			dtime=c.fetchone()
			print("Last log data recorded: "+dtime[0])
		getlogdbcon.has_been_called=True
	return c

def cosinedist(lat1,lon1,lat2,lon2): #Use cosine to find distance between coordinates
	phi1 = math.radians(lat1)
	phi2 = math.radians(lat2)
	dellamb = math.radians(lon2-lon1)
	R = 3440.06479 # Nmi
	# gives d in Nmi
	d = math.acos( math.sin(phi1)*math.sin(phi2) + math.cos(phi1)*math.cos(phi2) * math.cos(dellamb) ) * R
	return int(round(d))

def inithdg(lat1,lon1,lat2,lon2): #Find heading between coordinates
	phi1 = math.radians(lat1)
	phi2 = math.radians(lat2)
	lamb1 = math.radians(lon1)
	lamb2 = math.radians(lon2)
	y = math.sin(lamb2-lamb1) * math.cos(phi2)
	x = math.cos(phi1)*math.sin(phi2) - math.sin(phi1)*math.cos(phi2)*math.cos(lamb2-lamb1)
	brng = math.degrees(math.atan2(y, x))
	if brng<0:
		brng+=360
	return brng

def dirbwt(icaofrom,icaoto): #Find bearing from one airport to another
	lat1,lon1=loc_dict[icaofrom]
	lat2,lon2=loc_dict[icaoto]
	hdg=inithdg(lat1,lon1,lat2,lon2)
	return hdg

def distbwt(icaofrom,icaoto): #Find distance from one airport to another
	lat1,lon1=loc_dict[icaofrom]
	lat2,lon2=loc_dict[icaoto]
	dist=cosinedist(lat1,lon1,lat2,lon2)
	return dist

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

def mapper(what, points, mincoords, maxcoords, title): # Put the points on a map
	print("Mapping "+str(len(points))+" points...") #points is list of lists containing lat,lon, then possibly addtional data
	print("min: "+str(mincoords[0])+","+str(mincoords[1])+"  max: "+str(maxcoords[0])+","+str(maxcoords[1]))
	if maxcoords[1]-mincoords[1]>180 or maxcoords[0]-mincoords[0]>60: # Big spread, world with center aligned
		#print("Using world map")
		m = Basemap(projection='hammer', resolution=None, lon_0=(maxcoords[1]+mincoords[1])/2)
	else: # Center map on area
		#print("Using regional map")
		if len(points)>1:
			width=maxcoords[1]-mincoords[1]
			height=maxcoords[0]-mincoords[0]
		else: # Provide good window for plotting one point
			width=100
			height=100
		#print("Width: "+str(width)+"  Height: "+str(height))
		llclo=dcoord(mincoords[1],-0.25*width,'lon')
		llcla=dcoord(mincoords[0],-0.25*height,'lat')
		urclo=dcoord(maxcoords[1],0.25*width,'lon')
		urcla=dcoord(maxcoords[0],0.25*height,'lat')
		#print("ll="+str(llclo)+","+str(llcla)+"  ur="+str(urclo)+","+str(urcla))
		m = Basemap(projection='cyl', resolution=None, llcrnrlon=llclo, llcrnrlat=llcla, urcrnrlon=urclo, urcrnrlat=urcla)
	if what=="ac":
		if len(points) < 30: #Use awesome airplane symbol
			verts = list(zip([0.,1.,1.,10.,10.,9.,6.,1.,1.,4.,1.,0.,-1.,-4.,-1.,-1.,-5.,-9.,-10.,-10.,-1.,-1.,0.],[9.,8.,3.,-1.,-2.,-2.,0.,0.,-5.,-8.,-8.,-9.,-8.,-8.,-5.,0.,0.,-2.,-2.,-1.,3.,8.,9.])) #Supposed to be an airplane
			mk=(verts,0)
			ptsize=50
		else: #Use boring but more compact dots
			mk='o'
			ptsize=2
		print(points)
		m.shadedrelief(scale=0.2)
		x, y = m([i[1] for i in points], [i[0] for i in points])
		c='b'
		m.scatter(x,y,s=ptsize,marker=mk,c=c)
	elif what=="fuel" or what=="mtrl":
		maxsz=0
		for loc in points:
			thous=int(round(loc[2])) #Size of point will be based on fuel amount
			if thous>maxsz:
				maxsz=thous
			loc[2]=thous
		pts=[] #rows=thous, columns=colors, contents=list of points
		for i in range(maxsz+1):
			pts.append([[],[],[]]) #Add a new empty row
			for loc in points:
				if loc[2]==i+1: #If size matches, add the point
					pts[i][loc[3]].append((loc[0],loc[1]))
		for i in range(maxsz+1): #Set size/color of points
			sz=(i+1)/6 #Size based on amount
			if pts[i]!=[[],[],[]]: #Check if any list has points
				for j in range(3):
					if pts[i][j]!=[]: #Check if this list has any points
						print(pts[i][j])
						x, y = m([k[1] for k in pts[i][j]], [k[0] for k in pts[i][j]]) #Populate points
						if j==0: #Set color
							c='#cc9900'
						elif j==1:
							c='b'
						else:
							c='k'
						print(sz)
						m.scatter(x,y,s=sz,marker='o',c=c) #Plot the points with these properties
						for l in range(len(x)):
							gals=int(round(i/2.65))
							plt.text(x[l]-math.sqrt(sz/100),y[l],"~"+str(gals)+" gal",fontsize=7)
						m.shadedrelief(scale=0.2)
	plt.title(title,fontsize=12)
	plt.show()

def getcoords(data): #Get coordinates for a list of airports
	print("Building airport location dictionary from csv...")
	loc_dict=build_csv("latlon")
	print("Creating locations list...")
	locations=[]
	#lat_tot=0
	#lon_tot=0
	latmax,lonmax,latmin,lonmin=100,200,100,200 #garbage to signal init
	for row in data:
		try:
			print(row)
			lat,lon=loc_dict[row]
		except KeyError: #Probably "Airborne"
			print("Key error on: "+str(row))
			continue
		locations.append([lat,lon])
		#lat_tot+=lat
		#lon_tot+=lon
		if lat<latmin: #or abs(latmin)>90: #Look for min/max of coordinates
			latmin=lat
		if lat>latmax: #or abs(latmax)>90: #WTF was this abs() crap about?
			latmax=lat
		if lon<lonmin: #or abs(lonmin)>180:
			lonmin=lon
		if lon>lonmax: #or abs(lonmax)>180:
			lonmax=lon
	pts=len(locations)
	if pts==0:
		print("No locations found!")
	#else:
		#center=(lat_tot/pts,lon_tot/pts) # Not currently used, also needs the totals above
	return locations,(latmin,lonmin),(latmax,lonmax)

def gettype(icao): #Return name of aircraft type or error if not found
	icaodict=dicts.getactypedict()
	actype="aircraft"
	try:
		if icao!="":
			actype=icaodict[icao]
		success=True
	except (KeyError,IndexError):
		print("Name for code "+icao+" not found!")
		success=False
	return actype, success

def getcountries(conn): #Return list of countries?
	cdict=build_csv("country")
	c=getlogdbcon(conn)
	countries=[] #List of countries found
	#(fid real, type text, date text, dist real, sn real, ac text, model text, dep text, arr text, fltime text, income real, pfee real, crew real, bkfee real, bonus real, fuel real, gndfee real, rprice real, rtype text, runits text, rcost real)
	for log in c.execute('SELECT dep, arr FROM logs'):
		logc=(cdict[log[0]],cdict[log[1]]) #Look up countries of these airports
		match=[0,0] #Track if each has been matched
		for visited in countries: #Check current list
			for i in range(2):
				if logc[i]==visited: #Already in the list
					match[i]=1
					if match[i-1]==1: #Other one too, stop looking
						break
	for i in range(2):
		if match[i]==0: #Add to list if not already there
			countries.append(logc[i])
	return countries

def mapcountries(countries): #Map list of countries?
	fig = plt.figure(figsize=(11.7,8.3))
	plt.subplots_adjust()
	m = Basemap(projection='hammer', resolution=None, lon_0=0)
	m.drawcountries(linewidth=0.5)
	m.drawcoastlines(linewidth=0.5)
	
	from shapelib import ShapeFile
	import dbflib
	from matplotlib.collections import LineCollection
	from matplotlib import cm
	
	#for ctry in countries:
	shp = ShapeFile(r"borders/world_adm1")
	dbf = dbflib.open(r"borders/world_adm1")
	
	for npoly in range(shp.info()[0]):
		shpsegs = []
		shpinfo = []
		shp_object = shp.read_obj(npoly)
		verts = shp_object.vertices()
		rings = len(verts)
		for ring in range(rings):
			lons, lats = zip(*verts[ring])
			if max(lons)>721. or min(lons)<-721. or max(lats) >91. or min(lats) < -91.:
				raise ValueError,msg
			x, y = m(lons, lats)
			shpsegs.append(zip(x,y))
			if ring == 0:
				shapedict = dbf.read_record(npoly)
			name = shapedict["NAME_1"]
			
			shapedict['RINGNUM'] = ring+1
			shapedict['SHAPENUM'] = npoly+1
			shpinfo.append(shapedict)
		print(name)
		lines = LineCollection(shpsegs,antialiaseds=(1,))
		lines.set_facecolors(cm.jet(0.5))
		lines.set_edgecolors('k')
		lines.set_linewidth(0.3)
		ax.add_collection(lines)
	
	plt.show()

def main(argv): #This is where the magic happens
	syntaxstring='logmap.py -c'
	try: #ab_defghijklmnopqrstuvwxyz
		opts, args = getopt.getopt(argv,"c",[])
	except getopt.GetoptError:
		print(syntaxstring)
		sys.exit(2)
	#avg=(False,)*2
	getlogdbcon.has_been_called=False
	highprice=99999999
	fromdate="2014-01-01"
	todate="2020-12-31"
	for opt, arg in opts:
		if opt=="-c": #Maps countries visited
			countries=getcountries()
			print(countries)
			mapcountries(countries)
	print("Finished!")

if __name__ == "__main__":
   main(sys.argv[1:])
  
