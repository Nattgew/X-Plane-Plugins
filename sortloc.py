#!/usr/bin/python
import math, random, operator
import os, fileinput, csv
import sys, getopt
import regions

def build_csv(): #return dictionary of airport locations, using FSE csv file
	loc_dict = {}
	file='/mnt/data/XPLANE10/XSDK/icaodata.csv'
	with open(file, 'r') as f:
		has_header = csv.Sniffer().has_header(f.read(1024))
		f.seek(0)  # rewind
		reader = csv.reader(f)
		if has_header:
			next(reader)  # skip header row
		for row in reader:
			loc_dict[row[0]]=(float(row[1]),float(row[2]))
	return loc_dict

def buildkdata(): #i don't even know
	file='/mnt/data/XPLANE10/XSDK/icaodata.csv'
	with open(file, 'r') as f:
		has_header = csv.Sniffer().has_header(f.read(1024))
		f.seek(0)  # rewind
		reader = csv.reader(f)
		if has_header:
			next(reader)  # skip header row
		lat_tot=0
		lon_tot=0
		latmax,lonmax,latmin,lonmin=100,200,100,200 #garbage to signal init
		loc_dict = {}
		apt_dict = {}
		dataset=[]
		for row in reader:
			tup=(float(row[1]),float(row[2]))
			dataset.append(tup)
			loc_dict[row[0]]=tup
			apt_dict[tup]=row[0]
			lat_tot+=tup[0]
			lon_tot+=tup[1]
			if tup[0]<latmin or latmin>90:
				latmin=tup[0]
			elif tup[0]>latmax or latmax>90:
				latmax=tup[0]
			if tup[1]<lonmin or lonmin>180:
				lonmin=tup[1]
			elif tup[1]>lonmax or lonmin>180:
				lonmax=tup[1]
	pts=len(lat_tot)
	center=(lat_tot/pts,lon_tot/pts)
	return loc_dict, apt_dict, dataset, center, latmin, latmax, lonmin, lonmax

def getNeighbors(dataset, testInstance, k): #Get k nearest neighbors
	distances=[]
	for x in range(len(dataset)):
		dist=cosinedist(*dataset[x],*testinstance)
		distances.append((dataset[x], dist, x))
	distances.sort(key=operator.itemgetter(1))
	neighbors=[]
	for x in range(k):
		neighbors.append((distances[x][0], distances[x][2]))
	return neighbors

def cosinedist(lat1,lon1,lat2,lon2):
	phi1 = math.radians(lat1)
	phi2 = math.radians(lat2)
	dellamb = math.radians(lon2-lon1)
	R = 6371000
	d = math.acos( math.sin(phi1)*math.sin(phi2) + math.cos(phi1)*math.cos(phi2) * math.cos(dellamb) ) * R * 3.2808399 / 6076 # m to ft to Nm
	return int(round(d))

def getseeds(dataset, seeds, i, k):
	# if i==k:
		# return seeds
	# else:
	for i in range(k):
		points=len(dataset)
		for x in range(i,k):
			seeds[x]=dataset[int(random.random()*points)]
		totaldist=[]
		for x in range(k):
			totaldist[x]=(x,0)
			for y in range(k):
				if y!=x:
					totaldist[x][1]+=cosinedist(*seed[x],*seed[y])
		totaldist.sort(key=operator.itemgetter(1),reverse=True)
		best=[]
		for x in range(i+1):
			best.append(seed[totaldist[x][0]])
		seeds=best
		#return getseeds(dataset, best, i+1, k)

def divvy(dataset, seeds):
	divs=[]
	for x in range(len(seeds)):
		divs[x]=[]
	while dataset!=[]:
		for x in range(len(seeds)):
			neighbors=getNeighbors(dataset, seeds[x], 25)
			for i in range(len(neighbors)):
				divs[x].append(neighbors[i][0])
			for y in range(len(neighbors)):
				del dataset[neighbors[y][1]]
				for z in range(y+1,len(neighbors)):
					if neighbors[z][1]>neighbors[y][1]:
						neighbors[z][1]-=1
	return divs

maxlength=1950

print("Building airport location dictionary from csv...")
#loc_dict=build_csv()
loc_dict, apt_dict, dataset, center, latmin, latmax, lonmin, lonmax=buildkdata()

maxdistest=cosinedist(latmin,lonmin,latmax,lonmax)

input=""
airports=input.split("-")

each=len(airports)*5
divs=1
while each>maxlength:
	divs+=1
	each=len(airports)*5/divs

seeds=getseeds(dataset, [], x, divs)

	
# http://machinelearningmastery.com/tutorial-to-implement-k-nearest-neighbors-in-python-from-scratch/
