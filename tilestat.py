import math, sys, getopt
from mpl_toolkits.basemap import Basemap
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

#Define bounds for getting info
latmin=0
latmax=50
lonmin=-140
lonmax=-100
#http://www.x-plane.com/desktop/meet_x-plane/	
#74° north to 60° south

gridlats=latmax-latmin #135 for global scenery
gridlons=lonmax-lonmin #360 for global scenery
thegrid=[] #2x2 list of lists with tile settings
for i in range(gridlats): #0 to 74 then -1 to -60
	if i>latmax:
		i=latmax-i
	thegrid.append([])
	for j in range(gridlons): #0 to 180 then -1 to -179
		if j>lonmax:
			j=lonmax-j
		settings=0 #look for scenery folder and settings file
		if settings: #if it exists
			src="" #read imagery source
			zlv=0 #read zoom level
			cto=0 #read curve tolerance
		else:
			src=""
			zlv=0
			cto=0
		thegrid[i].append(src,zlv,cto)

#http://stackoverflow.com/a/12336694/3511560
def draw_screen_poly( lats, lons, m, params):
	if params[0]=="GO2": #Attempt to color based on imagery source
		col='green'
	elif params[0]=="USA2":
		col='red'
	elif params[0]=="BI":
		col='blue'
	else:
		col='grey'
	#Draw box in that color
    x, y = m( lons, lats )
    xy = zip(x,y)
    poly = Polygon( xy, facecolor=col, alpha=0.4 )
    plt.gca().add_patch(poly)
	#Add text for zoom level
	lon = lons[0]+0.5
	lat = lats[0]+0.5
	x, y = m(lon, lat)
	plt.text(x, y, str(params[1]),fontsize=12,ha='left',va='bottom',color='k')

#example values
lats = [ -30, 30, 30, -30 ]
lons = [ -50, -50, 50, 50 ]

#Something about map vs. plot coordinates...
#lats = np.linspace( lat0, lat1, resolution )
#lons = np.linspace( lon0, lon1, resolution )

m = Basemap(projection='cyl',llcrnrlat=latmin,urcrnrlat=latmax,llcrnrlon=lonmin,urcrnrlon=lonmax,resolution='c')
m.drawcoastlines()
m.drawmapboundary()
for i in range(135):
	lats = [i, i+1, i+1, i]
	for j in range(360):
		lons = [j, j, j+1, j+1]
		draw_screen_poly( lats, lons, m, thegrid[i][j])

plt.show()
