#!/usr/bin/python
import math, random, operator
import os, fileinput, csv
import sys, getopt
#import regions
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt

def builddict(): #return dictionary of airport locations, using FSE csv file
	file='/mnt/data/XPLANE10/XSDK/icaodata.csv'
	with open(file, 'r') as f:
		has_header = csv.Sniffer().has_header(f.read(1024))
		f.seek(0)  # rewind
		reader = csv.reader(f)
		if has_header:
			next(reader)  # skip header row
		loc_dict = {}
		apt_dict = {}
		for row in reader:
			if row[0]=="MN24": #Hack/correction to avoid duplicate values
				tup=(45.161, -93.1219)
			elif row[0]=="8Y4":  #WhyAreTheseTheSamePlace
				tup=(45.158, -93.1219)
			else: # Sweet now list.remove should work!
				tup=(float(row[1]),float(row[2]))
			loc_dict[row[0]]=tup
			apt_dict[tup]=row[0]
	return loc_dict,apt_dict

def builddset(airports, loc_dict): #Create dataset (list of coordinates) from airports input
	dataset=[]
	lat_tot=0
	lon_tot=0
	latmax,lonmax,latmin,lonmin=100,200,100,200 #garbage to signal init
	for apt in airports:
		tup=loc_dict[apt]
		dataset.append(tup)
		lat_tot+=tup[0]
		lon_tot+=tup[1]
		if tup[0]<latmin or abs(latmin)>90:
			latmin=tup[0]
		if tup[0]>latmax or abs(latmax)>90:
			latmax=tup[0]
		if tup[1]<lonmin or abs(lonmin)>180:
			lonmin=tup[1]
		if tup[1]>lonmax or abs(lonmax)>180:
			lonmax=tup[1]
	pts=len(dataset)
	center=(lat_tot/pts,lon_tot/pts)
	return dataset, center, latmin, latmax, lonmin, lonmax

def getNeighbors(dataset, testInstance, k): #Get k nearest neighbors
	#print("Looking for "+str(k)+" neighbors in "+str(len(dataset))+" points...")
	if len(dataset)<k+1: #If k or less options, then all are nearest neighbors!
		return dataset
	else:
		distances=[]
		for x in range(len(dataset)):
			dist=cosinedist(dataset[x][0],dataset[x][1],testInstance[0],testInstance[1])
			distances.append(dataset[x], dist)
		distances.sort(key=operator.itemgetter(1))
		neighbors=[]
		for x in range(k):
			print("Adding neighbor: "+str(distances[x][0][0])+", "+str(distances[x][0][1]))
			neighbors.append(distances[x][0])
		#neighbors.extend([distances[:k][0], distance[:k][2]])
		return neighbors
	
def draftNeighbors(dataset, testInstance, k): #Get k nearest neighbors AND remove them from dataset
	#print("Looking for "+str(k)+" neighbors in "+str(len(dataset))+" points...")
	if len(dataset)<k+1: #If k or less options, then all are nearest neighbors!
		return dataset, []
	else:
		distances=[]
		for x in range(len(dataset)):
			dist=cosinedist(dataset[x][0],dataset[x][1],testInstance[0],testInstance[1])
			distances.append([dataset[x], dist])
		distances.sort(key=operator.itemgetter(1))
		neighbors=[]
		for x in range(k):
			#print("Adding neighbor: "+str(distances[x][0][0])+", "+str(distances[x][0][1]))
			neighbors.append(distances[x][0])
			#print("Removing from dataset")
			dataset.remove(distances[x][0])
		#neighbors.extend([distances[:k][0], distance[:k][2]])
		return neighbors, dataset

def cosinedist(lat1,lon1,lat2,lon2): #Return distance between coordinates in Nm
	phi1 = math.radians(lat1)
	phi2 = math.radians(lat2)
	dellamb = math.radians(lon2-lon1)
	R = 3440.06479 # Nm
	d = math.acos( math.sin(phi1)*math.sin(phi2) + math.cos(phi1)*math.cos(phi2) * math.cos(dellamb) ) * R
	return int(round(d))

def getseeds(dataset, k): # Choose airports to use as location basis for each division
	seeds=[]
	i,j=0,-1
	while i<k: # Loop through the process multiple times for each seed
		for x in range(i,k): # Choose new seed for remaining seeds
			newseed=random.choice(dataset)
			if len(seeds)-1<x: # Building seeds list
				seeds.append(newseed)
			else: # Replacing with new seeds
				seeds[x]=newseed
		totaldist=[] # Calculate total distance to other seeds
		for x in range(k):
			totaldist.append([x,0])
			for y in range(k):
				if y!=x:
					totaldist[x][1]+=cosinedist(seeds[x][0],seeds[x][1],seeds[y][0],seeds[y][1])
		totaldist.sort(key=operator.itemgetter(1),reverse=True)
		best=[]
		for x in range(i+1):
			best.append(seeds[totaldist[x][0]])
		seeds=best
		j+=1
		if j%1000==0: # That should do it
			i+=1
	return best

def divvy(dataset, seeds): # Divide dataset into groups around the seed locations
	divs=[]
	for x in range(len(seeds)):
		divs.append([seeds[x]])
	#each=int(len(dataset)/20)
	each=5 # This is fast so probably could go down to 1
	while dataset!=[]:
		for x in range(len(seeds)):
			if dataset==[]:
				break
			else:
				#print("Adding "+str(each)+" neighbors to div "+str(x))
				neighbors,dataset=draftNeighbors(dataset, seeds[x], each)
				divs[x].extend(neighbors)
				# for i in range(len(neighbors)):
					# divs[x].append(neighbors[i][0])
				# for y in range(len(neighbors)):
					# for z in range(y+1,len(neighbors)):
						# if neighbors[z][1]>neighbors[y][1]:
							# print("Item "+str(neighbors[z][1])+" over "+str(neighbors[y][1])+", becoming "+str(neighbors[z][1]-1))
							# neighbors[z][1]-=1
					# print("Deleting dataset member "+str(neighbors[y][1])+" of "+str(len(dataset)))
					# del dataset[neighbors[y][1]]
	return divs

def mapper(divs, mincoords, maxcoords): # Put the points on a map, color by division
	if maxcoords[1]-mincoords[1]>180 or maxcoords[0]-mincoords[0]>60: # World with center aligned
		m = Basemap(projection='hammer',lon_0=(maxcoords[1]+mincoords[1])/2)
	else: # Center map on area
		width=maxcoords[1]-mincoords[1]
		height=maxcoords[0]-mincoords[0]
		m = Basemap(projection='cyl', resolution=None, llcrnrlon=mincoords[1]+0.1*width, llcrnrlat=mincoords[0]+0.1*height, urcrnrlon=maxcoords[1]+0.1*width, urcrnrlat=maxcoords[0]+0.1*height)
		# m = Basemap(width=35000000, height=22000000, projection='lcc', resolution=None, lat_0=1.0, lon_0=1.0)
	m.shadedrelief()
	# m.drawlsmask(land_color='#F5F6CE',ocean_color='#CEECF5',lakes=True)
	colors=['b','g','r','c','m','#088A29','#FF8000','#6A0888','#610B0B','#8A4B08','#A9F5A9'] # HTML dark green, orange, purple, dark red, dark orange, light green
	for i in range(len(divs)):
		print("Plotting division "+str(i))
		# x, y = m([k[1] for k in divs[i]], [k[0] for k in divs[i]])
		for j in range(len(divs[i])):
#			print("Plotting coord "+str(divs[i][j][0])+", "+str(divs[i][j][1]))
			x, y = m(divs[i][j][1],divs[i][j][0])
			if j==0:
				ptsize=10
				c='k'
			else:
				ptsize=3
				c=i if i<len(colors) else i%colors
			# m.scatter(x,y,ptsize,marker='o',color=colors[c])
			m.plot(x,y,markersize=ptsize,marker='o',markerfacecolor=c)
	plt.title('Locations of airports divided into regions',fontsize=12)
	plt.show()

maxlength=1950

print("Building airport location dictionary from csv...")
loc_dict, apt_dict=builddict()

#apts="TX03-F83-TX00-KABI-KDYS-6F4-35TX-TX14-TX02-6TE2-75TA-3TX5-76TA-67TX-43TX-T23-6F5-TX15-TX16-42XS-KALI-TX17-0T7-46TE-E38-4TE4-1E2-TX66-9TA8-TX78-9TS6-6XS2-TA01-6R5-3TS3-TE09-TE76-KAMA-1E7-7TX8-2TX0-1E4-KTDW-T00-TA49-E11-7R9-T34-TE77-81D-46TX-KLBX-TX19-TX20-XS48-5TS0-T39-TX21-TX22-85TA-KGKY-47TX-TX24-6TE8-T60-F44-5TA8-2XS3-TX25-KATA-XS60-2TE3-KAUS-3R3-6R4-TX05-4XS7-3R9-KATT-61TA-6F9-77TA-28TS-E30-20TS-TE21-TE90-TX29-TA52-TA82-7TS9-3R1-T84-TS94-KHPY-25TA-54T-TS95-3TS5-5T0-KBMT-55TX-KBPT-3R0-57TX-06R-60TX-61TX-62TX-7T3-63TX-3TX1-TE95-64TX-12TX-74XS-E41-18TE-T49-TX31-XS53-65TX-78TA-07R-66TX-3TA5-50TX-TX41-TA53-26XS-69TX-05TX-71TX-7TA8-TX32-F00-TX34-TA22-TX13-4TE1-TS78-KBGD-0F2-TX35-74TX-73TX-5XS8-2TX3-75TX-1XS8-3TA6-TA31-KBBD-12TE-94TX-2TE0-TE40-TX36-KBKD-11R-TA35-TA17-XS68-1F9-TX37-3TA7-TX23-TA27-15TA-65TE-TA51-TA03-12R-27XS-77TX-TA28-Q26-TX40-79TX-KBRO-80TX-KBWD-3TA4-8TS0-KCFD-83TX-13TE-84TX-06TA-85TX-88TX-1T8-86TX-TX42-3TX9-8TS1-87TX-89TX-KBMQ-TA63-7F3-18TX-14R-7TA5-90TX-91TX-93TX-TE26-T35-TE78-TS11-KHHF-9TA2-7F5-TA86-TX43-1TA7-1E9-34TS-95TX-1TS6-KCZT-74TA-2XS2-TA84-97TX-4F2-T89-XS86-TE13-99TX-1TE1-0XS0-TE27-0XS9-40XS-TA85-TX54-TE80-79TS-F17-TX45-TE01-24TA-KCDS-63TA-04TX-3T8-20XS-96TX-3F2-62XS-E34-7F6-4TE3-5TA4-TX46-F18-06TE-6R3-0TS5-7F7-TX47-KCOM-KCLL-TX48-2T4-T32-T88-1TS8-7TE8-1T1-TS27-66R-7F9-08TE-17TE-3TA1-9TE2-2F7-TX07-0TE0-19TE-KCXO-55TS-3TS9-22TE-NGW-KCRP-KNGP-07TE-69TA-TA43-TA05-KCRS-4XS1-6TX6-TX51-90TE-KCOT-46TA-37TA-79TA-TA58-5TS1-5TS2-TE96-E13-8TE2-TX97-TX52-22TS-81TS-T56-7XS2-1TA4-80TS-1XS1-1TE2-49TA-9TA3-8F3-TA16-TX11-8F4-XS77-3TA9-20R-TA34-8TE4-3TA8-2TE8-T71-TA36-TA06-TS07-8F5-KDHT-2E1-KADS-1F7-F69-KDAL-46TS-7TX2-KRBD-KDFW-XS21-4TA0-77XS-07TA-78XS-TX38-14XS-5TS3-3TE1-4TE6-TA07-3TS7-3TE9-21TE-TS35-04F-TS14-F66-76T-8F7-58TA-TX64-82TS-5TS4-TS57-4TS8-4TE9-23TS-KDRT-4TE7-TA29-81TE-KDLF-4TE2-TS04-8TS8-TA81-2TE7-2E5-TX12-8F8-KDTO-3XS0-2TS0-TE81-4TA1-46XS-E57-1TA5-TA55-4XS9-70XS-3TS1-4XS8-23R-Q55-7TS8-24R-5TS5-0TA3-6R6-9F0-84TE-KDUX-KELA-5TE7-5TE3-5TE2-14TX-KETN-TX68-6XS5-6TE0-TS29-25R-6TE1-6TE3-26R-6TE5-TS96-2TE4-68TE-0XS1-7TE6-8TE8-KELP-T27-5TE0-5T9-6TA4-TS80-TX61-56TS-62TA-1XS2-TX72-TX70-7XS5-27R-6TA0-6XS9-28TE-2TX1-TX27-TE29-2TX4-02XS-2TA8-F41-TE39-TX94-TX39-7TE1-4TE8-00TS-E35-TX73-7XS6-2TA6-T18-7TE2-7TS7-7TE0-6XS3-8TA5-30XS-8TS9-2TE5-XS90-0TS0-0TX5-TA08-Q41-T93-01TE-TA18-TA56-22XS-23XS-7TE9-8TE0-33XS-8TA0-1TE7-8TE1-4TS7-8TE6-2TE2-TS00-4TA2-F71-TX79-TS73-8TE3-09TA-TX75-34XS-TE97-8TE7-T82-7XS7-8XS0-XS01-44TX-TX56-28TA-T19-6TX2-7XS0-Q54-TA77-DDJ-KBIF-KGRK-KHLR-KFST-50F-KNFW-KAFW-KFTW-KFWS-T67-F04-9F9-TX09-29TA-9TE5-KGLE-TX81-KGLS-TS08-TS36-TX89-TX91-TS51-5TS7-2TX5-05F-03TA-TS55-TS67-TS01-8T6-59TS-07TS-KGTU-TX92-05TE-30TA-9TX1-62H-4F4-07F-41TA-TS61-09TE-TX93-8TS7-TE02-59TX-TX95-TX98-8TX3-T20-TX99-TE38-73XS-3T0-0TE6-F35-4TA3-E15-10F-F55-0TX0-TS89-0TX1-8TA7-KGPM-XS06-11TE-31TA-50TA-7XS3-TS53-0TX7-0TX9-31TS-0TX8-KGVT-1TX0-37TS-XS14-33R-2E3-E19-1TX1-6TE6-1TX3-1TX2-1TX5-0TA1-0TA2-34R-1TS9-KMNZ-1TX6-14F-1TX7-30TX-2TS2-KHRL-1TX8-32TE-32TA-15F-0TS2-1TX9-16TE-1TE5-T72-TS69-03TE-KHBV-TA44-2TS5-35TS-4TA4-F12-10TE-8TS2-TE10-KHRX-5XS2-63XS-TA78-2TX2-1X1-9XS1-5T5-0TE4-37TE-TX49-06TX-TA90-4TA5-14TE-KAAP-KLVJ-KEFD-39R-KIAH-KHOU-KDWH-21XS-KSPX-KAXH-T51-8TX7-KSGR-KEYQ-KIWS-O07-1TE8-1TS2-TE57-KHDO-8TA8-KUTS-2TX6-65TA-5TS9-T43-3TE0-2F0-20TE-TA59-TE55-21F-TS02-1TE3-KJSO-4TA6-49TE-KJAS-22F-TS62-24F-6F7-8TX0-40TA-40TE-TE45-8TS5-25TE-48T-2XS1-0TE7-50TE-3TX6-05TS-0TS1-3TX8-3TX2-2TX7-16XS-3TX7-3TX3-3TX4-53TE-KJCT-52TE-18TA-78TX-56TE-61T-8XS1-59TE-5TE6-55TE-9XS9-TA46-0TA4-28XS-K00-8TS6-TE04-TX67-7TX4-4TX2-6TS1-2TE6-63TE-4TX4-32TX-XS44-4TX5-06TS-5TE4-2R9-4TX6-67TE-KILE-69TS-TA73-64TE-KERV-66TE-60TE-KNQI-T80-T12-F75-4TX7-45R-29F-6TX4-4TX8-2TX8-TA47-TE58-08TS-3T5-9TE6-T41-54TX-TS18-44TE-72TE-TE83-47TE-79TE-TE12-TX82-17XS-89TE-5TX0-30F-2F5-9TE3-5TX1-TE48-5R3-T28-1TX4-KLNC-TS40-KLRD-8XS2-TE32-0TE5-8TS3-6TA3-69TE-7TE4-T13-57TE-49R-0TS4-77T-8XS3-6TS2-TE05-TE06-5TX2-6TA2-Q24-5TX4-5TX6-TA21-TA75-TE75-T78-82TE-43TS-5TX8-7T0-76TX-Q00-15XS-00R-XS12-9TX4-XS00-86T-6R9-44TS-5XS7-TS39-7TE3-4F0-4TE0-3TS0-KGGG-92TA-T26-47XS-KLBB-8XS8-F82-KLFK-2TA1-25TX-9TX2-50R-6TX5-47TS-51R-2TS4-XS55-6TX7-6TX8-TS70-TA83-3T2-92TE-5TE5-48XS-93TE-09TS-6TX9-T91-0TA7-KMRF-5TE1-XS03-86TA-1TE4-XS07-T15-TA23-KASL-5XS4-XS05-10TS-XS10-6TA9-34TE-TA26-19XS-18XS-TE59-KMFE-E48-19TA-XS57-TE84-T31-6TX3-KTKI-TS63-2E7-T92-XS08-F21-87XS-XS11-TA64-XS13-0TS8-5XS6-31XS-6XS4-KHQZ-KLXY-11TS-5TE8-TE33-7TX5-KMDD-KMAF-7TX7-7T7-2TS6-TA11-4T6-XS17-6TS3-TE50-XS18-TE34-3F9-TX62-12TS-0TS7-KMWL-7TE7-XS19-6TS4-E01-4TX0-33TA-TE85-43TA-F85-XS70-OSA-TE15-T50-XS15-KMSA-6X0-F53-XS24-1TE0-2T1-TA24-TA89-37F-TE52-KOCH-TS87-60R-87TE-XS25-87TA-XS20-XS23-XS22-TE67-TE86-TX01-XS09-61R-5TS8-77TS-48TS-9TA1-KBAZ-36XS-F48-88XS-XS27-XS28-XS29-6TS6-1TS0-89TS-71TA-KODO-00XS-13TS-7TX9-KONY-TS42-KORG-KNOG-XS33-TA97-30TS-TS71-0TS9-XS34-3F6-49XS-3XS1-KPSX-XS36-XS35-KPSN-8TX6-TA65-KPPA-3TE7-T45-3TE5-XS92-4XS2-XS30-KPRX-39TA-0TA8-65XS-TE16-6TS8-TX74-TS44-1TS1-KOZA-4TA8-XS39-T79-XS71-KPEQ-TE99-KPYX-4TX3-TS54-XS42-XS40-T30-2TA3-T24-F98-KPVW-9TX3-7TA3-6TS0-TA66-XS43-TE74-45TE-42F-7TS4-2R8-KPIL-T97-9TE4-T05-72TA-XS46-9X1-9R5-TE87-9TX6-9XS3-5F1-KPEZ-TS85-9TX7-TE68-48TE-XS91-XS50-XS51-8TX8-3TE3-TS15-T77-34TA-TS05-47TA-83TA-F01-XS47-T14-3T1-30TE-5XS0-F23-49F-XS56-92XS-XS58-14TS-XS59-KRFG-7TA7-7TS0-TA02-TS72-XS61-94XS-93XS-50XS-67R-XS64-XS63-TE47-02TX-51TE-52F-0TE3-54F-TE17-TE62-T53-XS66-KRCK-KRKP-XS67-XS62-T48-F46-XS72-58TE-XS73-T54-TS90-TE88-TA33-XS74-91TS-56F-69R-3TA0-8TX2-XS69-72XS-68TS-T33-3TE4-71TE-XS75-XS76-XS31-71TS-83TE-76TE-TS65-94TA-KSJT-73TA-86TS-78R-53XS-1TS3-XS79-5C1-XS88-9TX5-74R-1T7-KSKF-KMDA-XS80-KSAT-8T8-22TA-KSSF-75XS-T94-XS89-68TX-81R-37TX-XS94-TS75-TA25-TA87-71XS-TS74-TX33-TE24-T58-58F-TX96-6XS8-XS93-38XS-5TA5-5TA7-TA50-TA30-XS95-TE89-9TE0-8TA1-5TA9-F97-05TA-3TA2-93TS-2TA4-7TS2-KHYI-7TS3-31F-5TA0-39TE-TS20-60F-TA67-2F1-9TX9-09TX-XS99-72TS-9XS2-11TX-TA93-KSWI-F39-XS49-TE36-79XS-T69-3TE6-9XS5-F49-83R-0TX6-TE70-XS96-TE51-SEQ-TS13-84R-KSNK-TS22-53TX-TS25-E42-13TX-TE37-0XS2-E29-52TS-8TA3-0XS6-88R-0XS7-0XS8-T70-55XS-6XS7-7XS1-61TE-1XS0-F56-63F-XS78-KSEP-15TX-17TX-16TX-64F-58XS-14TA-2TS8-3E7-Q70-67XS-5XS9-9XS6-KSLR-6TE4-Q43-TS76-KSWW-86XS-TA00-2F4-2KL-1XS4-41XS-T74-68F-5TA1-KTPL-1XS6-TS92-19TX-TA70-1XS7-81TX-3TE8-KTRL-TS98-21TX-TS50-8TA4-97XS-TA13-23TX-54TE-1XS3-72F-24TX-1XS9-53TS-8XS6-94TE-23TA-7TA0-16TA-52TA-48TX-TE91-26TX-Q06-1TA2-TE63-16TS-KTYR-TA42-2XS5-KRND-2XS6-95TA-5TX9-9F1-8TX9-5XS5-51TX-KVHN-88TA-E52-70TS-75TS-28TX-29TX-53TA-F05-42TE-KVCT-3XS4-2XS7-2XS8-KUVA-54XS-70TE-KPWG-5TA2-TA57-31TX-2TS3-KCNW-KACT-TE92-73F-75TE-KZ0E-3XS8-4XS0-9TS3-3XS7-89TA-TE71-TS03-74TE-3XS5-98XS-56TX-60TA-54TA-TE72-TA60-01TX-25XS-6TE7-2TA9-08TX-6TA7-F78-54TS-KWEA-TA19-99XS-58TX-8XS9-F06-T65-40TS-45TX-66XS-41TS-94R-61XS-5R5-T59-96TS-36TX-69XS-68XS-TA80-37XS-F50-78TE-TS47-2F9-T47-KSPS-F14-4XS5-1TE6-97TS-57XS-76F-4XS6-TE08-KINK-TE73-5XS3-T90-F51-TA61-98TS-5TA6-77F-41TX-42TX-09R-9XS0-5TA3-T85-96TE-23TE-T86"
#airports=apts.split("-")
airports=[]
for apt,loc in loc_dict.items(): 
	airports.append(apt)

print("Building dataset from airport list...")
dataset, center, latmin, latmax, lonmin, lonmax=builddset(airports,loc_dict)
#width=cosinedist(center[0],lonmin,center[0],lonmax)/3.2808399 * 6076 # Nm to ft to m
#height=cosinedist(latmin,center[1],latmax,center[1])/3.2808399 * 6076
mapcenter=((latmax+latmin)/2,(lonmax+lonmin)/2)
print('Map will be centered at %f.2, %f.2 from lat %.2f to %.2f and lon %.2f to %.2f'%(mapcenter[0],mapcenter[1],latmin,latmax,lonmin,lonmax))
#print('Map width %.2f x %.2f'%(width,height))
# print("Finding max distance...")
maxdistest=cosinedist(latmin,lonmin,latmax,lonmax)

each=len(airports)*5
divs=1
while each>maxlength: #Find how many divisions need to be made
	divs+=1
	each=len(airports)*5/divs
print("Will divide airports into "+str(divs)+" groups of about "+str(each)+" each.")
print("Choosing seeds...")
seeds=getseeds(dataset, divs)
print("Seeds are: ", end="")
for seed in seeds:
	dataset.remove(seed) #delete these items from the dataset
	apt=apt_dict[seed]
	print(apt, end="")
print(" ")
print("Dividing airports...")
divlist=divvy(dataset,seeds)
print("Mapping results...")
if len(divlist)>0:
	mapper(divlist,(latmin,lonmin),(latmax,lonmax))
	
# http://machinelearningmastery.com/tutorial-to-implement-k-nearest-neighbors-in-python-from-scratch/
