#!/usr/bin/python
import sys, getopt, sqlite3
import fseutils # My custom FSE functions
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt

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

def getcountries(conn): #Return list of countries?
	cdict=fseutils.build_csv("country")
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
			conn=sqlite3.connect('/mnt/data/XPLANE10/XSDK/flightlogs.db')
			countries=getcountries(conn)
			print(countries)
			mapcountries(countries)
	print("Finished!")

if __name__ == "__main__":
   main(sys.argv[1:])
  
