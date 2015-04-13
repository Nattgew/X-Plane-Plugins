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
	loc_dict = {}
	file='/mnt/data/XPLANE10/XSDK/icaodata.csv'
	with open(file, 'r') as f:
		has_header = csv.Sniffer().has_header(f.read(1024))
		f.seek(0)  # rewind
		reader = csv.reader(f)
		if has_header:
			next(reader)  # skip header row
		dataset=[]
		trainingSet=[]
		testSet=[]
		for row in reader:
			tup=(float(row[1]),float(row[2]))
			dataset.append(tup)
			loc_dict[row[0]]=tup
			if random.random() < 0.66:
				trainingSet.append(tup)
			else:
				testSet.append(tup)

def getNeighbors(trainingSet, testInstance, k):
	distances=[]
	length=len(testInstance)-1
	for x in range(len(trainingSet)):
		dist=cosinedist(trainingSet[x][0],trainingSet[x][1],testinstance[0],testInstance[1])
		distances.append((trainingSet[x], dist))
	distances.sort(key=operator.itemgetter(1))
	neighbors=[]
	for x in range(k)
		neighbors.append(distances[x][0])
	return neighbors

def cosinedist(lat1,lon1,lat2,lon2):
	phi1 = math.radians(lat1)
	phi2 = math.radians(lat2)
	dellamb = math.radians(lon2-lon1)
	R = 6371000
	# gives d in metres
	d = math.acos( math.sin(phi1)*math.sin(phi2) + math.cos(phi1)*math.cos(phi2) * math.cos(dellamb) ) * R * 3.2808399 / 6076 # m to ft to Nm
	return int(round(d))

def getResponse(neighbors):
	classVotes={}
	for x in range(len(neighbors)):
		response=neighbors[x][-1]
		if response in classVotes:
			classVotes[response]+=1
		else
			classVotes[response]=1
	sortedVotes=sorted(classVotes.iteritems(),key=operator.itemgetter(1),reverse=True
	return sortedVotes[0][0]

maxlength=1950

print("Building airport location dictionary from csv...")
loc_dict=build_csv()

input""
airports=input.split("-")

each=length(airports)*5
divs=1
while each>maxlength:
	divs+=1
	each=length(airports)*5/divs

latmin,lonmin=loc_dict[airports[0]] #Initialize min,max from within set
latmax,lonmax=latmin,lonmin
	
for airport in apts:
	lat,lon=loc_dict[airport]
	if lat<latmin:
		latmin=lat
	elif lat>latmax:
		latmax=lat
	if lon<lonmin:
		lonmin=lon
	elif lon>lonmax:
		lonmax=lon

for airport in apts:
	
	for airport2 in apts:
	
	
# http://machinelearningmastery.com/tutorial-to-implement-k-nearest-neighbors-in-python-from-scratch/
