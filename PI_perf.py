from XPLMProcessing import * #Flight loops
from XPLMDataAccess import * #Datarefs
from XPLMDisplay import * #Draw window
from XPLMGraphics import * #Draw things
from XPLMDefs import * #Object definitions
from XPLMUtilities import * #Commands
from XPLMNavigation import * #Nav/FMS tools
from XPLMPlugin import *
import math
import os
import fileinput

class getaircraft:
	
	def __init__(self):
		acf_desc_ref=XPLMFindDataRef("sim/aircraft/view/acf_descrip")
		acf_icao_ref=XPLMFindDataRef("sim/aircraft/view/acf_ICAO")
		num_eng_ref=XPLMFindDataRef("sim/aircraft/engine/acf_num_engines")
		eng_type_ref=XPLMFindDataRef("sim/aircraft/prop/acf_en_type")
		prop_type_ref=XPLMFindDataRef("sim/aircraft/prop/acf_prop_type")
		self.acf_EW_ref=XPLMFindDataRef("sim/aircraft/weight/acf_m_empty") #kg
		self.acf_MTOW_ref=XPLMFindDataRef("sim/aircraft/weight/acf_m_max") #kg
		
		self.eng_type=[]
		self.prop_type=[]
		self.num_eng=XPLMGetDatai(num_eng_ref) #Find number of engines
		XPLMGetDatavi(eng_type_ref, self.eng_type, 0, self.num_eng) #Find type of engines
		XPLMGetDatavi(prop_type_ref, self.prop_type, 0, self.num_eng)
		acf_descb=[]
		XPLMGetDatab(acf_desc_ref, acf_descb, 0, 500)
		desc=str(acf_descb)
		XPLMGetDatab(acf_icao_ref, acf_descb, 0, 40)
		acf_icao=str(acf_descb)
		self.flaps=(0,1)
		self.maxcabin=0
		self.agl=2000
		if desc[0:27]=="['Boeing 737-800 xversion 4" or acf_icao=="['B738']":
			self.name="B738"
			self.flaps=(0.125,0.375,0.625,0.875,1) #1 5 15 30 40
			self.ceiling=42
		elif desc[0:15]=="['Pilatus PC-12" or desc[0:14]=="['Pilatus PC12" or acf_icao=="['PC12']":
			self.name="PC12"
			self.setEW(self.name,1895)
			self.flaps=(0.3,0.7,1) #15 30 40    (0.333333,0.666667,1) Carenado
			self.ceiling=30
			self.maxcabin=10000
			self.agl=1000
		elif desc[0:9]=="['BE1900D" or desc[0:19]=="['B1900 for X-plane" or acf_icao=="['B190']":
			self.name="B190"
			self.setEW(self.name,2985)
			self.ceiling=25
			self.maxcabin=10000
			self.agl=1500
		elif desc=="['Bombardier Challenger 300']" or acf_icao=="['CL30']":
			self.name="CL30"
			self.setEW(self.name,6849)
			self.ceiling=45
		elif desc[0:21]=="['C208B Grand Caravan" or acf_icao=="['C208']":
			self.name="C208"
			self.setEW(self.name,1910)
			self.ceiling=25
			self.maxcabin=10000
			self.agl=1000
		elif desc[0:13]=="['Dash 8 Q400" or acf_icao=="['DH8D']":
			self.name="DH8D"
			self.setEW(self.name,12071)
			self.flaps=(0.25,0.5,0.75,1) #5 10 15 35
			self.ceiling=27
			self.agl=1500
		elif desc=="['L-1049G Constellation']" or acf_icao=="['CONI']":
			self.name="CONI"
			self.setEW(self.name,31421)
			self.ceiling=24
			self.agl=1500
		elif desc=="['Douglas DC-3']" or acf_icao=="['DC3']":
			self.name="DC3"
			self.setEW(self.name,4584)
			self.ceiling=23
			self.agl=1000
		elif desc=="['Cessna Citation X']" or acf_icao=="['C750']":
			self.name="C750"
			self.setEW(self.name,6714)
			self.ceiling=51
		elif desc=="['Dassault Falcon 7X']" or acf_icao=="['FA7X']":
			self.name="FA7X"
			self.setEW(self.name,16279)
			self.ceiling=51
		elif desc=="['Let L-410']" or acf_icao=="['L410']":
			self.name="L410"
			self.setEW(self.name,2650)
			self.ceiling=20
			self.agl=1500
		elif desc[0:15]=="['Ilushin IL-14" or acf_icao=="['IL14']":
			self.name="IL14"
			self.setEW(self.name,5000)
			self.ceiling=24
			self.agl=1500
		elif desc[0:15]=="['C-27J Spartan" or acf_icao=="['C27J']":
			self.name="C27J"
			self.setEW(self.name,15880)
			self.ceiling=30
			self.agl=1500
		elif desc[0:15]=="['Boeing 757-20" or acf_icao=="['B752']":
			self.name="B752"
			self.ceiling=42
			self.flaps=(0.166667,0.333333,.5,0.666667,0.833333,1) #1,5,15,20,25,30
		elif desc[0:15]=="['Bombardier Ca" or acf_icao=="['CRJ2']":
			self.name="CRJ2"
			self.ceiling=41
			self.flaps=(0.25,0.5,0.75,1) #8,20,30,45
			self.setEW(self.name,13880)
		elif desc[0:15]=="['Embraer ERJ-1" or acf_icao=="['E140']":
			self.name="E140"
			self.ceiling=37
			self.flaps=(0.25,0.5,0.75,1) #FIX ME
			self.setEW(self.name,9600) #8500 E135, 9600 E145
		elif desc[0:14]=="['Antonov AN-2" or acf_icao=="['AN2']":
			self.name="AN2"
			self.ceiling=14.75
			self.setEW(self.name,2170)
		elif desc[0:14]=="['King Air C90" or acf_icao=="['C90B']":
			self.name="C90B"
			self.ceiling=28.45
			self.setEW(self.name,1576)
		elif desc[0:15]=="['The biggest a" or acf_icao=="['B744']":
			self.name="B744"
			self.ceiling=45
		elif desc[0:15]=="['Lockheed SR-7" or acf_icao=="['SR71']":
			self.name="SR71"
			self.ceiling=85
		elif desc[0:15]=="['Lockheed F-22" or acf_icao=="['F22']":
			self.name="F22"
			self.ceiling=60
		elif desc[0:15]=="['Douglas KC-10" or acf_icao=="['DC10']":
			self.name="DC10"
			self.ceiling=42
		elif desc[0:13]=="['Douglas F-4" or acf_icao=="['F4']":
			self.name="F4"
			self.ceiling=60
		elif desc[0:14]=="['Columbia 400" or acf_icao=="['COL4']":
			self.name="COL4"
			self.ceiling=25
			self.setEW(self.name,500)
		elif desc[0:14]=="['Dornier Do 3" or acf_icao=="['D328']":
			self.name="D328"
			self.ceiling=30
			self.setEW(self.name,5070)
		elif desc[0:14]=="['T210M Centur" or acf_icao=="['T210']" or acf_icao=="['C210']":
			self.name="C210"
			self.ceiling=27
			self.setEW(self.name,777)
		else:
			if acf_icao!="": #I guess we'll trust it
				self.name=acf_icao
			else: #You're flying a what?
				self.name=desc
				print str(desc[0:8])
			self.ceiling=30
	
	def setEW(self,AC,pyld): #Set aircraft EW to match FSE payload capacity
		MTOW=XPLMGetDataf(self.acf_MTOW_ref)
		EW_now=XPLMGetDataf(self.acf_EW_ref)
		EW=MTOW-pyld
		if EW < EW_now:
			print "PERF - Setting "+AC+" EW from "+str(EW_now)+" to "+str(EW)
			XPLMSetDataf(self.acf_EW_ref,EW)
		else:
			print "PERF - Unchanged "+AC+" EW "+str(EW_now)+" is lower than FSE "+str(EW)

class PythonInterface:

	def CtoF(self, C): #Not used, but could be used to display the temps in F
		F=C*1.8+32.0
		return F

	def get_index(self, i, length): #Make sure the index is not outside the bounds of the array
		flo=int(math.floor(i))
		fhi=int(math.ceil(i))
		if fhi>length-1:
			flo=length-2
			fhi=length-1
		elif flo<0:
			flo=0
			fhi=1
		return (fhi, flo)
	
	def get_flapi(self, flaps): #Reference correct flaps setting
		flap_i=-1
		for i in range(len(self.aircraft.flaps)):
			if abs(flaps-self.aircraft.flaps[i]) <= 0.01: #Damn floating point
				flap_i=i
		return flap_i
	
	def get_topwr(self, init): #Iterate countdown timer for takeoff power
		flightTimer=XPLMGetDataf(self.flighttime_ref)
		if self.TO_pwr==init or self.flightTimerLast==-1: #Haven't started counting yet
			self.flightTimerLast=flightTimer-1 #Assume 1 second elapsed
		elapsed=flightTimer-self.flightTimerLast
		self.flightTimerLast=flightTimer
		self.TO_pwr-=elapsed
		counter_m=int(self.TO_pwr/60)
		counter_s=int(self.TO_pwr%60)
		counter_str='  %d:%02d TO pwr remain' % (counter_m, counter_s)
		return counter_str
	
	def interp(self, y2, y1, x2, x1, xi): #Interpolate between two values
		if y2==y1:
			result=y1
		elif x2==x1:
			print "UH OH Interpolating the same point?"
			result=y1
		elif y2==0:
			print "UH OH Interpolating with 0 y2"
			result=y1
		elif y1==0:
			print "UH OH Interpolating with 0 y1"
			result=y2
		else:
			result=(y2-y1)/(x2-x1)*(xi-x1)+y1
		print "Interp "+str(y2)+", "+str(y1)+", "+str(x2)+", "+str(x1)+", "+str(round(xi))+" = "+str(round(result))
		print "Interp result: "+str(result)
		return result
	
	def interp2(self, y1, y2, y3, y4, x1, x2, x3, x4, xi1, xi2): #Interpolate between two interpolations
		res_l=self.interp(y1, y2, x1, x2, xi1)
		res_h=self.interp(y3, y4, x1, x2, xi1)
		result=self.interp(res_h, res_l, x3, x4, xi2)
		return result

	def getDA(self, P, T): #Use pressure and temperature to find density altitude
		T+=273.15
		PT=(P/self.P_SL)/(T/self.T_SL)
		if PT < 0:
			print "PERF - DA from "+str(int(round(P)))+" and "+str(int(round(T)))+" gives number "+str(int(round(PT)))
		density_alt=self.DA_pre*(1-PT**self.DA_exp)
		return density_alt
	
	def getdelISA(self, alt, T): #Find degrees C difference from ISA
		T_ISA=15.0-self.gamma_l*alt
		delISA=T-T_ISA
		return delISA
	
	def getPress(self, alt, SL): #Get pressure from altitude and SL pressure (like a reverse altimeter)
		P=-0.000000000000071173*alt**3+0.000000014417*alt**2*-0.0010722*alt+SL
		return P
	
	def getHwind(self): #Get headwind based on wind speed, wind direction, and aircraft heading
		wdir=XPLMGetDataf(self.wind_dir_ref)
		wspd=XPLMGetDataf(self.wind_spd_ref)
		tpsi=XPLMGetDataf(self.tpsi_ref)
		theta=math.radians(wdir-tpsi)
		hwind=wspd*math.cos(theta)
		return hwind
	
	def XPluginStart(self):
		self.Name="Performance Calculator"
		self.Sig= "natt.python.perf"
		self.Desc="Calculates the current performance info based on POH"
		self.VERSION="1.0"
		
		#Constants
		self.P_SL=29.92126 # std SL press 1013.25 hPa ISA or 29.92126 inHg US
		self.T_SL=288.15 # ISA std SL air temp in K
		self.gamma_l=0.0019812 # lapse rate K/ft
		gamma_u=0.0065 # lapse rate K/m
		R=8.31432 # gas constant J/mol K
		g=9.80665 # gravity m/s^2
		M=0.0289644 # molar mass of dry air kg/mol
		self.DA_pre=self.T_SL/self.gamma_l # Numbers for calculating DA
		self.DA_exp=gamma_u*R/(g*M-gamma_u*R)
		self.kglb=2.20462262 # kg to lb
		self.mft=3.2808399 # m to ft
		self.mkt=1.94384 # m/s to kt
		self.Nlb=0.22481 # N to lbf
		self.Npsi=0.0088168441 #Best fit for torque Nm -> psi on PC12
		#self.d=chr(0x2103)  u'\xb0'.encode('cp1252')
		self.d="" #In case I ever figure out how to print degree symbol
		
		self.N1_ref=XPLMFindDataRef("sim/flightmodel/engine/ENGN_N1_")
		self.EGT_ref=XPLMFindDataRef("sim/flightmodel/engine/ENGN_EGT_c")
		self.TRQ_ref=XPLMFindDataRef("sim/flightmodel/engine/ENGN_TRQ") #NewtonMeters
		self.RPM_ref=XPLMFindDataRef("sim/flightmodel/engine/POINT_tacrad") #prop speed, rad/sec?
		self.ITT_ref=XPLMFindDataRef("sim/flightmodel/engine/ENGN_ITT_c")
		self.FF_ref=XPLMFindDataRef("sim/flightmodel/engine/ENGN_FF_")
		self.TH_ref=XPLMFindDataRef("sim/flightmodel/engine/POINT_thrust")
		self.PWR_ref=XPLMFindDataRef("sim/flightmodel/engine/ENGN_power")
		self.alt_ref=XPLMFindDataRef("sim/flightmodel/position/elevation")
		self.agl_ref=XPLMFindDataRef("sim/flightmodel/position/y_agl")
		self.ias_ref=XPLMFindDataRef("sim/flightmodel/position/indicated_airspeed")
		self.gs_ref=XPLMFindDataRef("sim/flightmodel/position/groundspeed")
		self.tpsi_ref=XPLMFindDataRef("sim/flightmodel/position/true_psi")
		self.vvi_ref=XPLMFindDataRef("sim/flightmodel/position/vh_ind_fpm")
		self.mpsi_ref=XPLMFindDataRef("sim/flightmodel/position/mag_psi")
		self.f_norm_ref=XPLMFindDataRef("sim/flightmodel/forces/fnrml_gear")
		self.mach_ref=XPLMFindDataRef("sim/flightmodel/misc/machno")
		self.alt_ind_ref=XPLMFindDataRef("sim/flightmodel/misc/h_ind")
		self.geardep_ref=XPLMFindDataRef("sim/aircraft/parts/acf_gear_deploy")
		self.wgt_ref=XPLMFindDataRef("sim/flightmodel/weight/m_total")
		self.flap_h_pos_ref=XPLMFindDataRef("sim/cockpit2/controls/flap_ratio") # handle position
		self.gear_h_pos_ref=XPLMFindDataRef("sim/cockpit2/controls/gear_handle_down")
		self.throt_pos_ref=XPLMFindDataRef("sim/cockpit2/engine/actuators/throttle_ratio_all") # throttle position
		self.gps_degm_ref=XPLMFindDataRef("sim/cockpit2/radios/indicators/gps_bearing_deg_mag")
		self.gps_dist_ref=XPLMFindDataRef("sim/cockpit/radios/gps_dme_dist_m")
		self.baro_ref=XPLMFindDataRef("sim/weather/barometer_current_inhg")
		self.temp_ref=XPLMFindDataRef("sim/weather/temperature_ambient_c")
		self.wind_dir_ref=XPLMFindDataRef("sim/weather/wind_direction_degt")
		self.wind_spd_ref=XPLMFindDataRef("sim/weather/wind_speed_kt")
		self.baro_act_ref=XPLMFindDataRef("sim/weather/barometer_sealevel_inhg")
		self.sim_spd_ref=XPLMFindDataRef("sim/time/sim_speed_actual")
		self.ap_alt_ref=XPLMFindDataRef("sim/cockpit/autopilot/altitude")
		self.ap_hdg_ref=XPLMFindDataRef("sim/cockpit/autopilot/heading_mag")
		self.ap_vvi_ref=XPLMFindDataRef("sim/cockpit/autopilot/vertical_velocity")
		self.ap_spd_ref=XPLMFindDataRef("sim/cockpit/autopilot/airspeed")
		self.cab_alt_ref=XPLMFindDataRef("sim/cockpit/pressure/cabin_altitude_set_m_msl")
		self.cab_max_ref=XPLMFindDataRef("sim/cockpit/pressure/max_allowable_altitude")
		self.flighttime_ref=XPLMFindDataRef("sim/time/total_flight_time_sec")
		
		winPosX=20
		winPosY=700
		win_w=270
		win_h=90
		self.init_variables()
		self.alt_dict=self.build_dict()
		
		self.gameLoopCB=self.gameLoopCallback
		self.DrawWindowCB=self.DrawWindowCallback
		self.KeyCB=self.KeyCallback
		self.MouseClickCB=self.MouseClickCallback
		self.gWindow=XPLMCreateWindow(self, winPosX, winPosY, winPosX + win_w, winPosY - win_h, 1, self.DrawWindowCB, self.KeyCB, self.MouseClickCB, 0)
		
		self.CmdSHConn = XPLMCreateCommand("fsei/flight/perfinfo","Shows or hides performance info")
		self.CmdSHConnCB  = self.CmdSHConnCallback
		XPLMRegisterCommandHandler(self, self.CmdSHConn,  self.CmdSHConnCB, 0, 0)
		
		self.CmdSDConn = XPLMCreateCommand("fsei/flight/descinfo","Shows or hides descent/landing info")
		self.CmdSDConnCB  = self.CmdSDConnCallback
		XPLMRegisterCommandHandler(self, self.CmdSDConn,  self.CmdSDConnCB, 0, 0)
		
		self.CmdAPsetConn = XPLMCreateCommand("fsei/flight/apsetup","Shows or hides descent/landing info")
		self.CmdAPsetConnCB  = self.CmdAPsetConnCallback
		XPLMRegisterCommandHandler(self, self.CmdAPsetConn,  self.CmdAPsetConnCB, 0, 0)
		
		return self.Name, self.Sig, self.Desc
	
	def init_variables(self):
		self.started=0
		self.Dstarted=0
		self.msg=[""]*5
		self.TO_pwr=0
		self.aircraft=[]
		self.current_dest=""
		self.elevate_dest=0
		self.flightTimerLast=-1
		pass

	def build_dict(self): #return dictionary of airport altitudes
		alt_dict = {}
		dir2=os.path.join('Resources','default scenery','default apt dat','Earth nav data','apt.dat')
		dir1=os.path.join('Custom Scenery','x_Prefab_FSE_Airports','Earth nav data','apt.dat')
		for line in fileinput.input([dir1,dir2]): # I am forever indebted to Padraic Cunningham for this code
			params=line.split()
			try:
				header=params[0]
				if header=="1" or header=="16" or header=="17":
					alt_dict[params[4]]=int(params[1])
			except (KeyError,IndexError) as e:
				pass
		fileinput.close()
		return alt_dict

	def MouseClickCallback(self, inWindowID, x, y, inMouse, inRefcon):
		return 0

	def KeyCallback(self, inWindowID, inKey, inFlags, inVirtualKey, inRefcon, losingFocus):
		pass 

	def CmdSHConnCallback(self, cmd, phase, refcon):
		if(phase==0): #KeyDown event
			print "PERF = CMD perf info"
			self.toggleInfo()
		return 0

	def CmdSDConnCallback(self, cmd, phase, refcon):
		if(phase==0): #KeyDown event
			print "PERF = CMD desc info"
			self.toggleDInfo()
		return 0
	
	def CmdAPsetConnCallback(self, cmd, phase, refcon):
		if(phase==0): #KeyDown event
			print "PERF = Set AP settings"
			self.APset()
		return 0
	
	def APset(self): #Sets cruise altitude and heading based on destination, sets VS
		if self.aircraft==[]:
			self.aircraft=getaircraft()	
		gear=XPLMGetDatai(self.gear_h_pos_ref) #Landing gear position
		alt_ind=XPLMGetDataf(self.alt_ind_ref) #Indicated altitude
		aphdg=XPLMGetDataf(self.gps_degm_ref) #Heading to destination
		dalt=math.ceil(self.get_dest_info()/100)*100 #Destination altitude, round up to nearest 100 ft
		if gear==1: #If gear down, set AP for climb to destination
			alt,climb=self.getFL(dalt,alt_ind,aphdg)
			hdginit=self.getHDG(aphdg)
			if self.aircraft.name=="C27J":
				XPLMSetDataf(self.ap_spd_ref, 130)
		else: #If gear up, set AP for descent to destination
			alt=dalt
			hdginit=aphdg
			if self.aircraft.name=="PC12":
				climb=-1300 if alt_ind>22000 else -1200 if alt_ind>15000 else -1000
			elif self.aircraft.name=="B190":
				climb=-1500
			elif self.aircraft.name=="CL30":
				climb=-2000
			elif self.aircraft.name=="CONI":
				climb=-1500
			elif self.aircraft.name=="C208":
				climb=-1500
			else:
				climb=-1000
			alt+=self.aircraft.agl
			if self.aircraft.name=="C27J":
				XPLMSetDataf(self.ap_spd_ref, 200)
		#Set autopilot values
		XPLMSetDataf(self.ap_hdg_ref, hdginit)
		XPLMSetDataf(self.ap_alt_ref, alt)
		XPLMSetDataf(self.ap_vvi_ref, climb)
		
		# if self.maxcabin>0: #Attempt to set cabin altitude
			# if alt>10000:
				# cabalt=alt/ceiling*3048 #Approximate rule for PC-12 cabin altitude
			# if cabalt<dalt: #Pressurize to destination altitude
				# cabalt=dalt
			# if cabalt>self.maxcabin: #Max cabin altitude
				# cabalt=self.maxcabin
			# print "AP Changing cabin altitude from "+str(int(round(XPLMGetDataf(self.cab_alt_ref))))+" to "+str(int(round(cabalt)))+"m"
			# XPLMSetDataf(self.cab_alt_ref, cabalt)
			# print "AP Cabin altitude now set to "+str(int(round(XPLMGetDataf(self.cab_alt_ref))))+"m"
	
	def getFL(self,dalt,alt_ind,aphdg):
		dist=XPLMGetDataf(self.gps_dist_ref) #Distance to destination
		T=XPLMGetDataf(self.temp_ref) #deg C
		delISA=self.getdelISA(alt_ind, T)
		wgt=XPLMGetDataf(self.wgt_ref)*self.kglb
		if self.aircraft.name=="PC12":
			general_fl=int(dist/10+2) #General rule for PC-12 cruise altitude
			if wgt>9800 and delISA>10 and general_fl>28:
				general_fl=28
			climb=1000 if alt_ind<10000 else 750
			speed=200
			gph=50 if wgt<9750 else 60
		elif self.aircraft.name=="B190":
			general_fl=int(dist/10+4) #Faster climb rate at slower speed than PC-12
			climb=2000 if alt_ind<8000 else 1300
			speed=200
			gph=110
		elif self.aircraft.name=="CL30":
			factor=1.25 if delISA>15 or wgt>35000 or dist<375 else 1.5 #Slower climb at higher temps/weights
			general_fl=int(dist/10*factor) #Approximate rule
			climb=3500 if alt_ind<8000 else 2500
			if dist<200:
				speed=300
			elif dist<350:
				speed=350
			else:
				speed=400
			gph=330
		elif self.aircraft.name=="C208":
			general_fl=int(dist/10)+2
			if (wgt>8000 or delISA>10) and general_fl>15:
				general_fl=15
			climb=750 if alt<10000 else 500
			speed=150
			gph=60
		elif self.aircraft.name=="B738":
			factor=1.0 if delISA > 15 or wgt > 145000 else 1.25 #Slower climb at higher temps/weights
			general_fl=int(dist/10*factor)
			climb=2000
			speed=380 if dist<450 else 420
			gph=900
		elif self.aircraft.name=="FA7X":
			general_fl=int(dist/10*1.5)
			climb=3000
			speed=420
			gph=600
		elif self.aircraft.name=="C750":
			general_fl=int(dist/10*1.5)
			climb=4000
			speed=420
			gph=330
		elif self.aircraft.name=="DH8D":
			general_fl=int(dist/10+4) #Approximate rule
			climb=1500 if alt_ind<8000 else 1000
			speed=300
			gph=250
		elif self.aircraft.name=="CONI":
			general_fl=int(dist/10+2)
			climb=2000 if alt_ind<8000 else 1000
			speed=300
			gph=800
		elif self.aircraft.name=="DC3":
			general_fl=int(dist/5)
			climb=1000 if alt_ind<6000 else 750
			speed=180
			gph=95
		elif self.aircraft.name=="IL14":
			general_fl=int(dist/5)
			climb=1000 if alt_ind<6000 else 750
			speed=180
			gph=75
		elif self.aircraft.name=="C27J":
			general_fl=int(dist/8+2)
			climb=3000
			speed=275
			gph=400
		elif self.aircraft.name=="CRJ2": #MTOW 24,041 kg
			flimit=math.pow(0.74,(wgt/1000-20))+25.75 #Just a swag
			general_fl=int(dist/10)
			if general_fl>flimit:
				general_fl=flimit
			climb=2500
			speed=400
			gph=350
		elif self.aircraft.name=="D328": #MTOW 24,041 kg
			flimit=math.pow(0.74,(wgt/1000-20))+25.75 #Just a swag
			general_fl=int(dist/10)
			if general_fl>flimit:
				general_fl=flimit
			climb=1500
			speed=260
			gph=200
		else:
			general_fl=int(dist/10+2) #General rule for PC-12 cruise altitude
			climb=1000
			speed=0
			gph=0
		if speed>0:
			fuel=dist/speed*gph
			XPLMSpeakString("AP fuel estimate: "+str(int(round(fuel)))+" gal")
		general_fl+=int(dalt+alt_ind)/2000 #Account for departure/arrival altitudes
		if general_fl>self.aircraft.ceiling:
				general_fl=self.aircraft.ceiling
		if aphdg<180: #NEodd
			if general_fl<41:
				if general_fl%2==0:
					general_fl-=1
			else:
				while (general_fl-41)%4!=0:
					general_fl-=1
		else: #SWeven
			if general_fl<41:
				if general_fl%2==1:
					general_fl-=1
			else:
				while (general_fl-41)%4!=2:
					general_fl-=1
		alt=float(general_fl*1000)
		if alt<dalt+2000:
			alt=dalt+2000
		print "AP - Cruise at "+str(int(round(alt)))+" for "+str(int(round(alt_ind)))+"ft "+str(int(round(dist)))+"nm to "+str(int(round(dalt)))+"ft"
		return alt, climb
	
	def getHDG(self, aphdg):
		hdg=XPLMGetDataf(self.mpsi_ref) #Get current heading, attempt to adjust towards GPS course
		turn=hdg-aphdg
		if turn<0:
			turn+=360
		if turn>180: # right turn
			offset=(aphdg-hdg)/5 if aphdg>hdg else (360-hdg+aphdg)/5
		else: # left turn
			offset=(aphdg-hdg)/5 if aphdg<hdg else -(360-aphdg+hdg)/5
		hdginit=aphdg+offset
		if hdginit>360:
			hdginit-=360
		elif hdginit<0:
			hdginit+=360
		return hdginit
	
	def toggleInfo(self): #Toggle whether any info is computed/shown
		if self.started==0:
			self.aircraft=getaircraft()
			XPLMRegisterFlightLoopCallback(self, self.gameLoopCB, 0.25, 0)
			self.started=1
		else:
			XPLMUnregisterFlightLoopCallback(self, self.gameLoopCB, 0)
			self.init_variables()
	
	def toggleDInfo(self): #Toggles descent mode
		if self.Dstarted==0:
			if self.started==0:
				self.toggleInfo() #Start main loop if we haven't
			self.Dstarted=1
		else:
			self.Dstarted=0

	def DrawWindowCallback(self, inWindowID, inRefcon):
		if self.started==1:
			lLeft=[];	lTop=[]; lRight=[];	lBottom=[]
			XPLMGetWindowGeometry(inWindowID, lLeft, lTop, lRight, lBottom)
			left=int(lLeft[0]); top=int(lTop[0]); right=int(lRight[0]); bottom=int(lBottom[0])
			XPLMDrawTranslucentDarkBox(left,top,right,bottom)
			color=1, 1, 1.0
			for i in range(0,5):
				XPLMDrawString(color, left+5, top-(20+15*i), self.msg[i], 0, xplmFont_Basic)

	def XPluginStop(self):
		if self.Dstarted==1:
			self.toggleDInfo() 
		if self.started==1:
			self.toggleInfo()
		XPLMUnregisterCommandHandler(self, self.CmdAPsetConn,  self.CmdAPsetConnCB, 0, 0)
		XPLMUnregisterCommandHandler(self, self.CmdSHConn, self.CmdSHConnCB, 0, 0)
		XPLMUnregisterCommandHandler(self, self.CmdSDConn, self.CmdSDConnCB, 0, 0)
		XPLMDestroyWindow(self, self.gWindow)
		pass

	def XPluginEnable(self):
		return 1

	def XPluginDisable(self):
		pass

	def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
		if (inFromWho == XPLM_PLUGIN_XPLANE):
			if (inMessage == XPLM_MSG_PLANE_LOADED):
				if (inParam == XPLM_PLUGIN_XPLANE):
					if self.Dstarted==1:
						self.toggleDInfo() 
					if self.started==1:
						self.toggleInfo()
		pass

	def gameLoopCallback(self, inElapsedSinceLastCall, elapsedSim, counter, refcon):
		#Get current conditions
		P=XPLMGetDataf(self.baro_ref) #inHg
		T=XPLMGetDataf(self.temp_ref) #deg C
		alt=XPLMGetDataf(self.alt_ref)*self.mft
		wgt=XPLMGetDataf(self.wgt_ref)*self.kglb
		mach=XPLMGetDataf(self.mach_ref)
		DenAlt=self.getDA(P,T) #ft
		delISA=self.getdelISA(alt, T)
		dalt=None
		pwr, TOP_str = self.getPower()
		gears=[]
		XPLMGetDatavf(self.geardep_ref, gears, 0, 10)
		if gears[0]==1: #Landing or taking off
			flaps=XPLMGetDataf(self.flap_h_pos_ref)
			if XPLMGetDataf(self.f_norm_ref) != 0: #Weight on wheels
				Vspeed=self.getV1(flaps, wgt, DenAlt, T, self.aircraft.name)
				hwind=self.getHwind()
				runway=self.getTOD(flaps, wgt, DenAlt, T, delISA, hwind, self.aircraft.name)
			else:
				Vspeed=self.getVref(flaps, wgt, DenAlt, T, self.aircraft.name)
				dalt=self.get_dest_info()
				hwind=self.getHwind()
				SL=XPLMGetDataf(self.baro_act_ref)
				runway=self.getLDR(wgt, dalt, delISA, SL, hwind, self.aircraft.name)
		else:
			Vspeed=""
			runway=""
		dIstr=str(int(round(delISA)))+" "+self.d+"C"
		if delISA>0:
			dIstr="+"+dIstr
		dist=XPLMGetDataf(self.gps_dist_ref)
		machstr="  M"+str(round(mach,2))
		self.msg[0]=self.aircraft.name+"  DA: "+str(int(round(DenAlt)))+" ft  GW: "+str(int(round(wgt)))+" lb  "+str(int(round(dist)))+"nm"
		self.msg[1]="T: "+str(int(round(T)))+" "+self.d+"C  ISA +/-: "+dIstr+TOP_str+machstr
		vvi=XPLMGetDataf(self.vvi_ref)
		if self.Dstarted==0:
			gs=XPLMGetDataf(self.gs_ref)*self.mkt
			alt_ind=XPLMGetDataf(self.alt_ind_ref)
			kias=XPLMGetDataf(self.ias_ref)
			maxPwr=self.getMaxPwr(DenAlt, delISA, self.aircraft.name)
			cruiseclb=self.getCC(DenAlt, alt, delISA, wgt, self.aircraft.name)
			cruise=self.getCruise(DenAlt, wgt, alt_ind, delISA, self.aircraft.name)
			maxcruise=self.getMaxCruise(DenAlt, wgt, alt, delISA, self.aircraft.name)
			optFL=self.getOptFL(wgt, self.aircraft.name)
			maxFL=self.getMaxFL(wgt, delISA, self.aircraft.name)
			twospeed=str(int(round(kias)))+"/"+str(int(round(gs)))
			#Assemble the messengers
			self.msg[2]="Pwr: "+maxPwr+"  CC: "+cruiseclb+"  Thr: "+pwr
			self.msg[3]="Crs: "+maxcruise+"  LR: "+cruise+"  AS: "+twospeed
			self.msg[4]="FL: "+maxFL+"  FL: "+optFL+runway+Vspeed#+" Flaps: "+str(flaps)
		else:
			if dalt is None:
				dalt=self.get_dest_info()
			hwind=self.getHwind()
			SL==XPLMGetDataf(self.baro_act_ref)
			ldr=self.getLDR(wgt, dalt, delISA, SL, hwind, self.aircraft.name)
			ddist=self.getDesc(dist, alt, dalt, DenAlt, delISA, self.aircraft.name)
			dprof=self.getDpro(self.aircraft.name, alt)
			#Assemble the message
			self.msg[2]="Descend at: "+ddist
			self.msg[3]=dprof
			self.msg[4]=Vspeed+ldr
		#Compute good delay before running again, based on climb rate and time accel
		if XPLMGetDataf(self.agl_ref)<762: #If under 2500 feet, update more frequently
			delay=3
		else:
			if abs(vvi)<1:			
				vvi=1.0
			delay=60.0/abs(vvi/500.0*XPLMGetDataf(self.sim_spd_ref))
			if delay>60:
				delay=60
		
		return delay

	def getPower(self): #Return power level, determine takeoff power
		if self.aircraft.eng_type[0]==2 or self.aircraft.eng_type[0]==8: #Turboprop
			TRQ=[]
			XPLMGetDatavf(self.TRQ_ref, TRQ, 0, self.aircraft.num_eng)
			pwr=str(round(TRQ[0],1))+" Nm"
			if self.aircraft.name=="B190":
				torque_ftlb1=self.Nlb*self.mft*TRQ[0]
				torque_ftlb2=self.Nlb*self.mft*TRQ[1]
				pwr=str(int(round(torque_ftlb1)))+"|"+str(int(round(torque_ftlb2)))+" ftlb"
				if torque_ftlb1>3750.0 or torque_ftlb2>3750.0: #Takeoff power
					TOP_str=self.get_topwr(300)
				else:
					self.TO_pwr=300
					TOP_str=""
			elif self.aircraft.name=="PC12":
				torque_psi=self.Npsi*TRQ[0]
				pwr=str(round(torque_psi,1))+" psi"
				ITT=[]
				XPLMGetDatavf(self.ITT_ref, ITT, 0, self.aircraft.num_eng)
				if torque_psi>37.0 or ITT[0]>760: #Takeoff power
					TOP_str=self.get_topwr(300)
				else:
					self.TO_pwr=300
					TOP_str=""
			elif self.aircraft.name=="C27J":
				FF=[]
				TH=[]
				PW=[]
				XPLMGetDatavf(self.FF_ref, FF, 0, self.aircraft.num_eng)
				XPLMGetDatavf(self.TH_ref, TH, 0, self.aircraft.num_eng)
				XPLMGetDatavf(self.PWR_ref, PW, 0, self.aircraft.num_eng)
				tsfc=3600*FF[0]/(TH[0]/self.Nlb)
				bsfc=3600*FF[0]/(PW[0])
				pwr=" T: "+str(round(tsfc,2))+"  B: "+str(round(bsfc,2))
				TOP_str=""
			else:
				torque_ftlb=self.Nlb*self.mft*TRQ[0]
				pwr=str(round(torque_ftlb,1))+" ftlb"
				TOP_str=""
		elif self.aircraft.eng_type[0]==4 or self.aircraft.eng_type[0]==5: #Jet
			N1=[]
			XPLMGetDatavf(self.N1_ref, N1, 0, self.aircraft.num_eng)
			if self.aircraft.name=="B738":
				pwr=str(round(N1[0],1))+"|"+str(round(N1[1],1))+" %N1"
				TOP_str=""
			elif self.aircraft.name=="CL30":
				pwr=str(round(N1[0],1))+"|"+str(round(N1[1],1))+" %N1"
				throt=XPLMGetDataf(self.throt_pos_ref)
				if throt>0.93: #Takeoff power FIX ME
					TOP_str=self.get_topwr(300)
				else:
					self.TO_pwr=300
					TOP_str=""
			else:
				pwr=str(round(N1[0],1))+" %N1"
				TOP_str=""
		else: #Piston
			if self.aircraft.prop_type[0]==0: #Fixed pitch
				RPM=[]
				XPLMGetDatavf(self.RPM_ref, RPM, 0, self.aircraft.num_eng)
				pwr=str(int(round(RPM[0]*60/math.pi)))+" rpm"
				TOP_str=""
			else: #Variable pitch?
				EGT=[]
				XPLMGetDatavf(self.EGT_ref, EGT, 0, self.aircraft.num_eng)
				pwr=str(int(round(EGT[0])))+"C EGT"
				TOP_str=""
		
		return pwr, TOP_str
		
	def get_dest_info(self): #Get info about destination
		destindex=XPLMGetDisplayedFMSEntry()
		destid=[]
		XPLMGetFMSEntryInfo(destindex, None, destid, None, None, None, None)
		dest=str(destid[0])
		try:
			dalt=self.alt_dict[dest]
		except (KeyError,IndexError) as e:
			XPLMSpeakString("ERROR: "+dest+" not found")
			dalt=0
		return dalt
	
	def getDpro(self, AC, alt): #Show applicable descent profile
		if AC=="B738":
			profile="M.78 to FL350, M.75 to 280kt"
		elif AC=="PC12":
			profile="2000 fpm at lower of M.48/236 kias"
		elif AC=="CL30":
			profile="M.78 to FL350, M.75 to 270kt"
		elif AC=="DH8D":
			profs=((238,0),
				(250,10000),
				(277,11000),
				(260,20000),
				(250,21000),
				(240,24000),
				(233,27000))
			for i in range(6,-1,-1):
				if alt>profs[i][1]:
					profile=str(profs[i][0])+" kias to "+str(profs[i][1])
					break
		else:
			profile="Have fun"
		return profile
	
	def getDesc(self, dist, alt, dalt, DA, delISA, AC): #Get distance from destination of top of descent
		if AC=="B738" or AC=="CL30":
			ddist_nm=(alt-dalt)/3000 #General rule for jet descents
			ddist=str(int(round(ddist_nm)))+"nm"
		elif AC=="PC12":
			alts=tuple(range(5000,30001,5000))
			isas=tuple(range(-40,31,10))
			dnms=((9.6,20,31,0,0,0), 			# -40
				(9.9,20.2,31.8,43.3,0,0),			# -30
				(10,20.7,32.2,44.1,55.8,0),		# -20
				(10.1,21.1,32.8,45,56.8,68.4),	# -10
				(10.3,21.6,33.8,46,58,70),	# 0
				(10.5,21.9,34.2,46.8,59.2,71.3),	# 10
				(10.8,22.2,34.8,47.8,60.2,72.4),	# 20
				(11,22.5,35.5,48.3,61.4,73.9))	# 30
			alt_i=alt/5000-1 #exact index of where actual values are in table
			isa_i=delISA/10+4
			alt_ih, alt_il = self.get_index(alt_i, len(alts)) #get upper and lower indexes to look up in table
			isa_ih, isa_il = self.get_index(isa_i, len(isas))
			while dnms[isa_ih][alt_il]==0 or dnms[isa_il][alt_il]==0 or dnms[isa_ih][alt_ih]==0 or dnms[isa_il][alt_ih]==0: #Avoid zero values in table
				alt_il-=1
				alt_ih-=1
			ddist_nm=self.interp2(dnms[isa_ih][alt_il], dnms[isa_il][alt_il], dnms[isa_ih][alt_ih], dnms[isa_il][alt_ih], isas[isa_ih], isas[isa_il], alts[alt_ih], alts[alt_il], delISA, DA) #Interpolate table to find value\
			ddist=str(int(round(ddist_nm)))+"nm"
		elif AC=="DH8D":
			alts=tuple(range(2000,24001,2000),25000,27000)
			dnms=(4,7,12,18,23,28,34,40,62,85,105,125,132,155)
			alt_i=(alt-2000)/2000 if alt<24000 else (alt-24000)/1000+11 if alt<25000 else (alt-25000)/1000+12
			alt_ih, alt_il = self.get_index(alt_i, len(alts))
			ddist_nm=self.interp(dnms[alt_ih], dnms[alt_il], alts[alt_ih], alts[alt_il], alt_i)
			ddist=str(int(round(ddist_nm)))+"nm"
		else:
			ddist="N/A"
		return ddist
	
	def getLDR(self, wgt, elev, delISA, SL, hwind, AC): #Get landing distance
		if AC=="PC12":
			Tgd=-self.getdelISA(elev, -delISA) #Assume ISA difference is same at ground, find T
			P=self.getPress(elev, SL)
			DA=self.getDA(P,Tgd)
			dis=tuple(range(-40,31,10))
			alts=tuple(range(0,10001,2000))
			GW=(6400,7000,8000,9000,9900)
			tod1=((1940,2000,2050,2110,2160,2220,2280,2340),	# SL
				(2020,2080,2140,2200,2260,2330,2390,2450),	# 2k
				(2110,2170,2240,2310,2370,2440,2510,2570),	# 4k
				(2200,2270,2350,2420,2490,2560,2630,2700),	# 6k
				(2330,2400,2480,2580,2640,2710,2790,2870),	# 8k
				(2540,2620,2700,2790,2880,2970,3050,3150))	# 10k
			dist1=tuple(range(1800,3401,200))
			tod2=(1180,1420,1660,1800,1940,2080,2200,2340,2480)
			dist2=dist1
			if hwind>=0: #Use headwind trend
				tod3=(1250,1430,1610,1790,1960,2140,2320,2490,2660)
				wind_i=hwind/30
			else:
				tod3=(2460,2680,2900,3140,3360,3580,3800,4020,4240)
				wind_i=abs(hwind/10)
			alt_i=DA/2000
			di_i=(delISA+40)/10
			GW_i=(wgt-6400)/600 if wgt<=7000 else (wgt-6300)/900 if wgt>=9000 else (wgt-6000)/1000
			alt_ih, alt_il = self.get_index(alt_i, len(alts))
			di_ih, di_il = self.get_index(di_i, len(dis))
			GW_ih, GW_il = self.get_index(GW_i, len(GW))
			wind_ih, wind_il = self.get_index(wind_i, 2)
			#Basic altitude/temperature distance
			basic_dist=self.interp2(tod1[alt_ih][di_il], tod1[alt_il][di_il], tod1[alt_ih][di_ih], tod1[alt_il][di_ih], alts[alt_ih], alts[alt_il], dis[di_ih], dis[di_il], DA, delISA)
			#Weight factor
			dist1_i=(basic_dist-2000)/1000
			dist1_ih, dist1_il = self.get_index(dist1_i, len(dist1))
			wgt_dist=self.interp2(dist1[dist1_ih], dist1[dist1_il], tod2[dist1_ih], tod2[dist1_il], dist1[dist1_ih], dist1[dist1_il], GW[GW_ih], GW[GW_il], basic_dist, wgt)
			#Wind factor
			dist2_i=(wgt_dist-1200)/1000
			dist2_ih, dist2_il = self.get_index(dist2_i, len(dist2))
			wnd_dist=self.interp2(dist2[dist2_ih], dist2[dist2_il], tod3[dist2_ih], tod3[dist2_il], dist2[dist2_ih], dist2[dist2_il], 30, 0, wgt_dist, hwind)
			ldr="  LDR: "+str((int(wnd_dist)/100)*100)+" ft"
		elif AC=="B752":
			Tgd=-self.getdelISA(elev, -delISA) #Assume ISA difference is same at ground, find T
			P=self.getPress(elev, SL)
			DA=self.getDA(P,Tgd)
			wgts=tuple(range(155,210,5))
			PA=tuple(range(0,8000,2000))
			ldrs=((3800,4100,4300,4400,4700), #flaps 30
				(4000,4200,4400,4600,4800),  #160k
				(4100,4300,4500,4600,4900),
				(4200,4400,4600,4750,5200),  #170k
				(4300,4500,4750,4900,5200),
				(4400,4700,4850,5100,5400),  #180k
				(4500,4700,5000,5250,5500),
				(4700,4850,5200,5300,5600),  #190k
				(4750,5000,5250,5450,5750),
				(4800,5100,5400,5600,5800),  #200k
				(4950,5200,5500,5700,6000),
				(5150,5750,5600,5800,6300))  #210k
			wgt_i=(wgt-155000)/2000
			wgt_ih, wgt_il = self.get_index(wgt_i, len(wgts))
			PA_i=DA/2000
			PA_ih, PA_il = self.get_index(PA_i, len(PA))
			ldist=self.interp2(ldrs[wgt_ih][PA_il], ldrs[wgt_il][PA_il], ldrs[wgt_ih][PA_ih], ldrs[wgt_il][PA_ih], wgts[wgt_ih], wgts[wgt_il], PA[PA_ih], PA[PA_il], wgt/1000, DA)
			ldr="  LDR: "+str(int(round(ldist)))+" ft"
		elif AC=="CRJ2":
			Tgd=-self.getdelISA(elev, -delISA) #Assume ISA difference is same at ground, find T
			P=self.getPress(elev, SL)
			DA=self.getDA(P,Tgd)
			wgts=(34,36,38,40,42,44,46,48,50,52,53)
			PA=tuple(range(0,10000,2000))
			ldrs=((3856,4013,4182,4372,4578,4807), #34k  0 - 10k PA
				(4010,4176,4353,4553,4770,5012),
				(4163,4338,4524,4734,4963,5219),
				(4316,4499,4695,4915,5157,5428), #40k
				(4468,4660,4865,5098,5353,5640),
				(4620,4820,5037,5282,5552,5854),
				(4771,4981,5210,5468,5752,6076),
				(4923,5144,5384,5656,5956,6331),
				(5077,5312,5569,5860,6188,6614), #50k
				(5247,5500,5775,6085,6469,6930), #52k
				(5340,5600,5885,6206,6620,7101)) #53k
			if wgt<52000:
				wgt_i=(wgt-34000)/2000
			else:
				wgt_i=9+(wgt-52000)/1000
			wgt_ih, wgt_il = self.get_index(wgt_i, len(wgts))
			PA_i=DA/2000
			PA_ih, PA_il = self.get_index(PA_i, len(PA))
			print("wgt_l/h="+str(wgt_il)+"/"+str(wgt_ih)+"  PA_l/h="+str(PA_il)+"/"+str(PA_ih))
			ldist=self.interp2(ldrs[wgt_ih][PA_il], ldrs[wgt_il][PA_il], ldrs[wgt_ih][PA_ih], ldrs[wgt_il][PA_ih], wgts[wgt_ih], wgts[wgt_il], PA[PA_ih], PA[PA_il], wgt/1000, DA)
			ldr="  LDR: "+str(int(round(ldist)))+" ft"
		else:
			ldr=""
		return ldr
	
	def getTOD(self, flaps, wgt, DA, T, delISA, hwind, AC): #Get takeoff distance
		if AC=="B190":
			alts=tuple(range(0,10001,2000))
			oats=tuple(range(-34,53,2))
			tod1=((0,0,0,0,0,0,0,0,0,1890,1900,1920,1930,1950,1980,1990,2010,2050,2080,2100,2120,2140,2170,2200,2230,2260,2290,2310,2340,2360,2400,2420,2470,2490,2510,2530,2570,2600,2630,2660,2700,2730,2760,2800),	#SL
				(0,0,0,0,0,0,0,0,2030,2060,2100,2120,2140,2180,2200,2220,2260,2280,2310,2340,2380,2400,2430,2460,2490,2530,2550,2590,2610,2640,2680,2710,2750,2790,2820,2860,2900,2940,2990,3010,3090,3140,0,0),	#2k
				(0,0,0,0,0,0,2290,2310,2330,2360,2390,2420,2460,2490,2510,2530,2580,2600,2630,2680,2710,2730,2790,2810,2850,2900,2940,2990,3010,3060,3110,3160,3200,3270,3310,3370,3430,3500,3560,3660,0,0,0,0,0),	#4k
				(0,0,0,0,0,2500,2540,2580,2600,2630,2680,2710,2750,2790,2820,2880,2910,2970,3000,3040,3090,3130,3200,3240,3300,3350,3400,3460,3510,3570,3620,3680,3750,3800,3890,3940,4010,4100,4150,0,0,0,0,0,0),	#6k
				(0,0,2780,2820,2850,2890,2930,2980,3000,3050,3100,3130,3190,3220,3280,3320,3380,3410,3480,3510,3580,3630,3690,3750,3820,3890,3950,4020,4100,4190,4270,4370,4470,4570,4680,4820,0,0,0,0,0,0,0),	#8k
				(3100,3130,3180,3230,3280,3330,3380,3430,3480,3530,3580,3630,3690,3730,3790,3850,3910,3980,4050,4150,4240,4330,4450,5040,5150,5250,5350,5460,5550,5650,5780,5900,6020,6170,0,0,0,0,0,0,0,0,0,0))	#10k
			GW=(10000,14200,16600)
			dist1=tuple(range(1900,5901,500))
			tod2=((1010,1420,1900),
				(1210,1700,2400),
				(1460,2020,2900),
				(1680,2380,3400),
				(1900,2780,3900),
				(2100,3100,4400),
				(2380,3380,4900),
				(2600,3800,5400),
				(2800,4150,5900))
			dist2=tuple(range(1500,6001,500))
			if hwind>=0: #Choose headwind trend
				tod3=tuple(range(1250,4896,405))
				wind_i=hwind/30
			else:
				tod3=(1900,2500,3000,3700,4200,4800,5300,5900,6500,7100)
				wind_i=abs(hwind/10)
			alt_i=DA/2000
			oat_i=(T+34)/2
			GW_i=(wgt-10000)/4200 if wgt<=14200 else (wgt-11800)/2400
			alt_ih, alt_il = self.get_index(alt_i, len(alts))
			oat_ih, oat_il = self.get_index(oat_i, len(oats))
			GW_ih, GW_il = self.get_index(GW_i, len(GW))
			wind_ih, wind_il = self.get_index(wind_i, 2)
			while tod1[alt_ih][oat_il]==0 or tod1[alt_il][oat_il]==0 or tod1[alt_ih][oat_ih]==0 or tod1[alt_il][oat_ih]==0: #Don't use a zero value from table
				if oat_il<=len(tod1[0])/2:
					oat_il+=1
					oat_ih+=1
				else:
					oat_il-=1
					oat_ih-=1
			#Basic altitude/temperature distance
			basic_dist=self.interp2(tod1[alt_ih][oat_il], tod1[alt_il][oat_il], tod1[alt_ih][oat_ih], tod1[alt_il][oat_ih], alts[alt_ih], alts[alt_il], oats[oat_ih], oats[oat_il], DA, T)
			#Weight factor
			dist1_i=(basic_dist-1900)/500
			dist1_ih, dist1_il = self.get_index(dist1_i, len(dist1))
			wgt_dist=self.interp2(tod2[dist1_ih][GW_il], tod2[dist1_il][GW_il], tod2[dist1_ih][GW_ih], tod2[dist1_il][GW_ih], dist1[dist1_ih], dist1[dist1_il], GW[GW_ih], GW[GW_il], basic_dist, wgt)
			#Wind factor
			dist2_i=(wgt_dist-1500)/500
			dist2_ih, dist2_il = self.get_index(dist2_i, len(dist2))
			wnd_dist=self.interp2(dist2[dist2_ih], dist2[dist2_il], tod3[dist2_ih], tod3[dist2_il], dist2[dist2_ih], dist2[dist2_il], 30, 0, wgt_dist, hwind)
			TOD="  TOD: "+str((int(wnd_dist)/100)*100)+" ft"
		elif AC=="PC12":
			dis=tuple(range(-40,31,10))
			alts=tuple(range(0,10001,2000))
			GW=(6400,7000,8000,9000,10000,10450)
			tod1=((2000,2150,2300,2500,2700,2800,3000,3300),	# SL
				(2250,2400,2650,2800,3000,3200,3400,3800),		# 2k
				(2500,2750,2900,3150,3350,3700,3900,4350),		# 4k
				(2800,3050,3300,3600,3850,1200,4500,5000),		# 6k
				(3250,3500,3800,4150,4500,4800,5300,6000),		# 8k
				(3800,4150,4500,4900,5400,5800,6600,7600))		# 10k
			dist1=tuple(range(2000,9001,1000))
			tod2=((800,1000,1300,1600,2000,2200),
				(1200,1400,1800,2400,3000,3400),
				(1500,1800,2300,3100,4000,4600),
				(1800,2100,2900,3900,5000,5700),
				(2000,2500,3400,4700,6000,6900),
				(2300,2900,4000,5300,7000,8000),
				(2600,3300,4500,6100,8000,9100),
				(2900,3700,5000,7800,9000,9300))
			dist2=dist1
			if hwind>=0: #Use headwind trend
				tod3=(1550,2400,3200,4000,4800,5600,6400,7200)
				wind_i=hwind/30
			else:
				tod3=(2600,3800,5000,6200,7400,8700,9900,11100)
				wind_i=abs(hwind/10)
			di_i=(delISA+40)/10
			alt_i=DA/2000
			GW_i=(wgt-6400)/600 if wgt<7000 else (wgt-6000)/1000 if wgt<10000 else (wgt-8200)/450
			di_ih, di_il = self.get_index(di_i, len(dis))
			alt_ih, alt_il = self.get_index(alt_i, len(alts))
			GW_ih, GW_il = self.get_index(GW_i, len(GW))
			#Basic altitude/temperature distance
			basic_dist=self.interp2(tod1[alt_ih][di_il], tod1[alt_il][di_il], tod1[alt_ih][di_ih], tod1[alt_il][di_ih], alts[alt_ih], alts[alt_il], dis[di_ih], dis[di_il], DA, delISA)
			#Weight factor
			dist1_i=(basic_dist-2000)/1000
			dist1_ih, dist1_il = self.get_index(dist1_i, len(dist1))
			wgt_dist=self.interp2(tod2[dist1_ih][GW_il], tod2[dist1_il][GW_il], tod2[dist1_ih][GW_ih], tod2[dist1_il][GW_ih], dist1[dist1_ih], dist1[dist1_il], GW[GW_ih], GW[GW_il], basic_dist, wgt)
			#Wind factor
			dist2_i=(wgt_dist-1200)/1000
			dist2_ih, dist2_il = self.get_index(dist2_i, len(dist2))
			wnd_dist=self.interp2(dist2[dist2_ih], dist2[dist2_il], tod3[dist2_ih], tod3[dist2_il], dist2[dist2_ih], dist2[dist2_il], 30, 0, wgt_dist, hwind)
			TOD="  TOD: "+str((int(wnd_dist)/100)*100)+" ft"
		elif AC=="DH8D":
			TOD=""
		else:
			TOD=""
		return TOD
	
	def getVref(self, flaps, wgt, DA, T, AC): #Get Vref landing speed
		if AC=="B738":
			flap_i=self.get_flapi(flaps)-2
			if flap_i<0 or flap_i>3:
				Vref="LAND CONFIG"
			else:
				GW=tuple(range(90,181,10))
				vrs=((122,129,135,142,148,154,159,164,169,174),		# flaps 15
					(116,123,129,135,141,146,151,156,160,165),		# flaps 30
					(109,116,122,128,133,139,144,148,153,157))		# flaps 40
				wgt_i=wgt/10000-9
				wgt_ih, wgt_il = self.get_index(wgt_i, len(GW))
				vri=self.interp(vrs[flap_i][wgt_ih], vrs[flap_i][wgt_il], GW[wgt_ih], GW[wgt_il], wgt/1000)
				Vref="  Vref: "+str(int(round(vri)))+" kias"
		elif AC=="PC12": #Assume flaps 40
			GW=tuple(range(6400,10001,900))
			vapps=(67,72,76,80,84)
			wgt_i=wgt/900-64/9
			wgt_ih, wgt_il = self.get_index(wgt_i, len(GW))
			vapp=self.interp(vapps[wgt_ih], vapps[wgt_il], GW[wgt_ih], GW[wgt_il], wgt)
			#print 'Vref %.0f %.0f %.0f %.0f %.0f = %.0f' % (vapps[wgt_ih], vapps[wgt_il], GW[wgt_ih], GW[wgt_il], wgt, vapp)
			Vref="  Vref: "+str(int(round(vapp)))+" kias"
		elif AC=="DH8D":
			flap_i=self.get_flapi(flaps)+1
			wgts=tuple(range(39600,63801,1100),64500)
			ias=((124,127,128,129,131,133,134,135,137,139,140,142,143,145,146,147,149,150,152,153,155,155,157,158),	#0 deg
				(114,115,117,118,120,122,124,125,126,127,129,130,132,133,134,136,137,138,139,141,142,143,145,145),	#5
				(108,108,109,110,112,113,115,116,117,118,120,121,122,124,125,126,127,129,130,131,132,134,136,136),	#10
				(105,105,105,105,107,108,109,110,112,113,114,115,117,118,119,120,121,123,124,125,126,128,130,129),	#15
				(101,101,101,101,102,103,104,106,107,108,109,110,112,113,114,115,116,117,118,119,120,122,122,123))	#35
			wgt_i=(wgt-39600)/1100 if wgt<63800 else (wgt-63800)/700
			wgt_ih, wgt_il = self.get_index(wgt_i, len(wgts))
			vr=self.interp(ias[flap_i][wgt_ih], ias[flap_i][wgt_il], wgts[wgt_ih], wgts[wgt_il], wgt)
			Vref="  Vref: "+str(int(round(vr)))+" kias"
		elif AC=="IL14":
			wgts=(27558,38581)
			vapps=(73,76)
			vapp=self.interp(vapps[1], vapps[0], wgts[1], wgts[0], wgt)
			Vref="  Vref: "+str(int(round(vapp)))+" kias"
		elif AC=="B752":
			flap_i=self.get_flapi(flaps)+1
			wgts=tuple(range(160,230,2))
			#flaps 0,1,5,15,20,25,30
			ias=((227,188,178,171,165,147,144), #230k
				(227,186,176,171,164,146,144),
				(225,185,176,169,164,146,143),
				(224,185,175,168,162,144,143),
				(223,183,174,168,162,143,142),
				(223,183,174,167,161,143,140),  #220k
				(221,182,172,167,161,142,140),
				(220,182,172,165,160,142,139),
				(218,181,171,165,158,140,139),
				(218,181,171,164,158,140,138),
				(217,179,169,162,157,139,137),  #210k
				(216,178,169,162,157,138,137),
				(214,178,168,161,155,138,135),
				(214,176,167,161,155,137,135),
				(213,175,167,160,154,137,134),
				(211,175,165,158,153,135,134),  #200k
				(210,174,165,158,153,135,133),
				(209,174,164,157,151,134,131),
				(207,172,162,157,151,133,131),
				(206,171,162,155,151,133,130),
				(206,171,161,154,150,131,129),  #190k
				(204,169,160,154,150,131,129),
				(203,168,160,153,148,130,127),
				(202,168,158,153,147,129,127),
				(200,167,157,165,147,129,126),
				(199,165,157,150,146,127,126),  #180k
				(199,165,155,150,146,127,125),
				(197,164,154,148,143,126,124),
				(196,162,154,147,143,125,124),
				(195,162,153,147,141,125,122),
				(193,161,151,146,140,124,121),  #170k
				(192,160,151,144,140,124,121),
				(192,158,150,144,139,122,120),
				(190,158,148,143,137,121,118),
				(189,157,148,141,137,121,118),
				(188,157,147,141,136,120,117))  #160k
			wgt_i=35-(wgt-160000)/2000
			wgt_il, wgt_ih = self.get_index(wgt_i, len(wgts))
			vr=self.interp(ias[wgt_ih][flap_i], ias[wgt_il][flap_i], wgts[wgt_ih], wgts[wgt_il], wgt/1000)
			Vref="  Vref: "+str(int(round(vr)))+" kias"
		elif AC=="CRJ2": #Vapp = Vref + 15 kias
			flap_i=self.get_flapi(flaps)+1
			wgts=(34,37,40,44,47,51)
			#Flaps 0 8 20 30 45
			ias=((151,137,133,129,121), #34k
				(157,144,139,135,127), #37k
				(162,149,144,140,132), #40k
				(168,156,150,146,138), #44k
				(173,160,155,151,143), #47k
				(179,167,161,157,149)) #51k
			if wgt<40000:
				wgt_i=(wgt-34000)/3000
			elif wgt<44000:
				wgt_i=2+(wgt-40000)/4000
			elif wgt<47000:
				wgt_i=3+(wgt-44000)/3000
			else:
				wgt_i=4+(wgt-47000)/4000
			wgt_ih, wgt_il = self.get_index(wgt_i, len(wgts))
			vr=self.interp(ias[wgt_ih][flap_i], ias[wgt_il][flap_i], wgts[wgt_ih], wgts[wgt_il], wgt/1000)
			Vref="  Vref: "+str(int(round(vr)))+" kias"
		else:
			Vref=""
		return Vref

	def getV1(self, flaps, wgt, DA, T, AC): #Get V1 speed
		if AC=="B738":
			flap_i=self.get_flapi(flaps)
			if flap_i<0 or flap_i>2:
				V1=""
			else:
				GW=tuple(range(90,181,10))
				alts=tuple(range(0,8001,2000))
				#Determine conditions class
				if T < 27 and DA < alts[1] or T < 38 and DA < alts[1] and (-T+38)/5.5 <= DA/1000: # A cyan
					v1s=((107,114,121,127,133,139,145,150,155,160),	# flaps 1
						(103,109,116,122,128,134,139,144,149,153),	# flaps 5
						(99,106,112,118,124,130,135,140,145,150))	# flaps 15
				elif T < 27 and DA < alts[2] or T < 38 and DA < alts[2] and (-T+38)/11 <= DA/1000-3 or T < 43 and DA < (alts[2]+alts[1])/2 and (-T+43)/(5/3) <= DA/1000: #B yellow
					v1s=((108,115,122,128,134,140,146,151,156,161),	# flaps 1
						(104,110,117,123,129,135,140,145,150,154),	# flaps 5
						(100,107,113,119,125,131,136,141,146,0))	# flaps 15
				elif T < 27 and DA < alts[3] or T < 38 and DA < alts[3] and (-T+38)/5.5 <= DA/1000-4 or T < 49 and DA < (alts[3]+alts[2])/2 and (-T+49)/2.75 <= DA/1000: #C pink
					v1s=((109,116,123,129,135,141,147,152,157,162),	# flaps 1
						(105,111,118,124,130,136,141,146,151,0),	# flaps 5
						(101,108,114,120,126,132,137,142,0,0))		# flaps 15
				elif T < 60 and DA/1000 < 160/11 and (-T+60)/4.125 <= DA/1000: #D green
					v1s=((110,117,124,130,136,142,148,153,158,0),	# flaps 1
						(106,112,119,125,131,137,142,147,0,0),		# flaps 5
						(102,109,115,121,127,133,138,0,0,0))		# flaps 15
				else: #E blue uh oh
					v1s=((112,119,126,132,138,144,150,155,0,0),		# flaps 1
						(108,114,121,127,133,139,0,0,0,0),			# flaps 5
						(104,111,117,123,129,0,0,0,0,0))			# flaps 15
				wgt_i=wgt/10000-9
				wgt_ih, wgt_il = self.get_index(wgt_i, len(GW))
				if v1s[flap_i][wgt_ih]==0:
					if v1s[flap_i][wgt_il]!=0:
						v1f=v1s[flap_i][wgt_il]
						V1="  V1: "+str(int(round(v1f)))+" kias"
					else: #Zero value means V1 is too high
						V1="  V1 > V1max"
				else:
					while v1s[flap_i][wgt_ih]==0 or v1s[flap_i][wgt_il]==0:
						wgt_il-=1
						wgt_ih-=1
					v1f=self.interp(v1s[flap_i][wgt_ih], v1s[flap_i][wgt_il], GW[wgt_ih], GW[wgt_il], wgt/1000)
					V1="  V1: "+str(int(round(v1f)))+" kias"
		elif AC=="PC12":
			flap_i=self.get_flapi(flaps)
			if flap_i<0 or flap_i>1:
				V1=""
			else:
				GW=(6400,7300,8200,9100,10000,10450)
				vrs=((63,67,71,75,79,81),	# flaps 15
					(58,62,66,70,73,75))	# flaps 30
				#vas=((65,70,74,78,82,84), # flaps 15, Accelerate-stop, not used right now
				#(59,63,67,71,74,76)) # flaps 30
				wgt_i=wgt/900-64/9 if wgt<10000 else wgt/450-164/9
				wgt_ih, wgt_il = self.get_index(wgt_i, len(GW))
				#print 'Interp: %.0f %.0f %.0f %.0f %.0f' % (vrs[flap_i][wgt_ih], vrs[flap_i][wgt_il], GW[wgt_ih], GW[wgt_il], wgt)
				vr=self.interp(vrs[flap_i][wgt_ih], vrs[flap_i][wgt_il], GW[wgt_ih], GW[wgt_il], wgt)
				V1="  V1: "+str(int(round(vr)))+" kias"
		elif AC=="DH8D":
			flap_i=self.get_flapi(flaps)
			if flap_i<0 or flap_i>2:
				V1=""
			else:
				wgts=tuple(range(39600,63801,1100),64500)
				ias=((108,108,108,108,108,108,109,111,113,114,116,117,119,120,122,123,125,126,128,129,131,132,134,134),	#5 deg
				(104,104,104,104,104,104,104,104,104,106,107,109,110,112,113,114,116,117,119,120,121,123,124,125),	#10
				(100,100,100,100,100,100,100,100,101,102,104,105,107,108,109,111,112,113,114,116,117,118,119,120))	#15
				wgt_i=(wgt-39600)/1100 if wgt<63800 else (wgt-63800)/700
				wgt_ih, wgt_il = self.get_index(wgt_i, len(wgts))
				vr=self.interp(ias[flap_i][wgt_ih], ias[flap_i][wgt_il], wgts[wgt_ih], wgts[wgt_il], wgt)
				V1="  V1: "+str(int(round(vr)))+" kias"
		elif AC=="IL14":
			wgts=(27558,38581)
			ias=(78,81)
			vr=self.interp(ias[1], ias[0], wgts[1], wgts[0], wgt)
			V1="  V1: "+str(int(round(vr)))+" kias"
		elif AC=="CRJ2":
			flap_i=self.get_flapi(flaps)
			if flap_i<0 or flap_i>1:
				V1=""
			else:
				wgts=(34,37,40,44,47,51)
				temps=(10,20,30,40,50)
				if wgt<40000:
					wgt_i=(wgt-34000)/3000
				elif wgt<44000:
					wgt_i=2+(wgt-40000)/4000
				elif wgt<47000:
					wgt_i=3+(wgt-44000)/3000
				else:
					wgt_i=4+(wgt-47000)/4000
				wgt_ih, wgt_il = self.get_index(wgt_i, len(wgts))
				if T<0:
					temp_i=0
				elif T>40:
					temp_i=4
				else:
					temp_i=int(math.ceil(T/10-1))
				if flaps==0: #Flaps 8  V2,Vr,V1
					speed=(((155,148,148),(150,143,140),(144,136,135),(138,127,125),(133,122,120),(127,115,111)), #-40 to 10
					((155,149,149),(150,143,141),(144,137,135),(138,128,126),(133,122,121),(127,115,112)), #11-20
					((155,150,150),(150,144,143),(144,138,137),(138,129,128),(133,123,122),(127,116,114)), #21-30
					((155,151,151),(150,145,144),(144,139,139),(138,130,130),(133,125,125),(127,118,116)), #31-40
					((155,151,151),(150,145,144),(144,139,139),(138,130,130),(133,125,125),(127,118,116))) #41-50
				else: #Flaps 20  V2,Vr,V1
					speed=(((143,137,138),(138,132,130),(133,127,125),(127,119,115),(122,113,109),(117,107,102)),
					((143,140,138),(138,132,131),(133,128,124),(127,120,116),(112,114,110),(117,108,103)),
					((143,141,141),(138,133,133),(133,129,127),(127,121,117),(122,115,111),(117,109,105)),
					((143,142,142),(138,134,134),(133,130,128),(127,123,119),(122,116,113),(117,111,107)),
					((143,142,142),(138,134,134),(133,130,128),(127,123,119),(122,116,113),(117,111,107)))
				vr=self.interp(speed[temp_i][wgt_ih][2], speed[temp_i][wgt_il][2], wgts[wgt_ih], wgts[wgt_il], wgt/1000)
				V1="  V1: "+str(int(round(vr)))+" kias"
		elif AC=="B752":
			flap_i=self.get_flapi(flaps)
			if flap_i<0 or flap_i>3:
				V1=""
			else:
				wgts=tuple(range(160,260,20))
				if DA<2100 and (T<25 or 7914-228.6*T<DA and 25<T): #A   V1,VR,V2, wgts 160k-260k
					speed=(((126,132,141),(137,143,152),(147,153,161),(157,162,169),(167,171,176),(176,179,184)), #1
						((117,123,132),(125,132,140),(135,141,148),(144,149,155),(153,157,162),(161,165,169)), #5
						((108,116,125),(118,125,132),(128,134,140),(136,141,147),(145,149,153),(154,157,160)), #15
						((103,111,119),(111,118,126),(120,126,133),(129,134,139),(137,141,146),(145,148,152))) #20
				elif DA<6700 and (T<15 or 15<T<20 and 10200-200*T<DA or 20<T<40 and 10600-220*T<DA or 40<T and 11982-255*T<DA): #B
					speed=(((129,134,144),(139,144,152),(150,154,161),(160,164,169),(169,173,176),(178,181,184)),
						((118,124,132),(128,133,140),(138,142,148),(147,151,155),(156,159,162),(164,167,169)),
						((111,118,125),(121,126,132),(130,135,140),(139,143,147),(148,151,153),(156,159,160)),
						((105,112,119),(114,120,126),(123,128,133),(132,136,140),(139,143,146),(147,149,152)))
				elif DA<9700 and (T<10 or 10<T<20 and 11100-140*T<DA or 20<T<30 and 11300-150*T<DA or 30<T<40 and 14000-240*T<DA or T>40 and 15768-284.2*T<DA): #C
					speed=(((131,136,144),(142,146,152),(153,156,161),(163,166,169),(172,175,177),(181,183,184)),
						((120,125,132),(131,135,140),(141,144,148),(150,153,155),(158,161,162),(166,169,169)),
						((114,119,125),(124,128,133),(133,137,140),(142,145,147),(150,153,153),(158,160,160)),
						((108,113,119),(117,121,126),(126,129,133),(135,137,140),(142,144,146),(0,0,0)))
				elif DA<11000 and (T<5 or 5<T<30 and 13025-137.5*T<DA or 30<T<40 and 14900-200*T<DA or 40<T<50 and 17700-270*T<DA or 50<T<60 and 19700-310*T<DA or T>60 and 22100-350*T<DA): #D
					speed=(((134,138,144),(145,148,152),(156,158,161),(165,167,169),(175,176,177),(0,0,0)),
						((123,127,132),(134,137,140),(143,146,148),(152,154,156),(161,162,163),(0,0,0)),
						((116,121,125),(126,130,133),(136,138,140),(144,146,147),(153,154,154),(0,0,0)),
						((110,114,119),(120,123,126),(128,131,133),(136,138,140),(0,0,0),(0,0,0)))
				elif 33989-452.6*T<DA: #E
					speed=(((138,141,144),(149,151,153),(159,160,161),(168,169,170),(177,177,177),(0,0,0)),
						((126,129,132),(137,139,141),(146,148,149),(155,156,156),(163,163,163),(0,0,0)),
						((120,123,125),(130,132,133),(139,140,141),(147,147,147),(0,0,0),(0,0,0)),
						((113,117,119),(122,125,127),(131,132,134),(0,0,0),(0,0,0),(0,0,0)))
				else:
					return "Excds Lmts"
				wgt_i=(wgt-160000)/2000
				wgt_ih, wgt_il = self.get_index(wgt_i, len(wgts))
				if speed[flaps_i][wgt_ih][0]==0 or speed[flaps_i][wgt_il][0]==0:
					return "Excds Lmts"
				else:
					vr=self.interp(speed[flaps_i][wgt_ih][0], speed[flaps_i][wgt_il][0], wgts[wgt_ih], wgts[wgt_il], wgt/1000)
					V1="  V1: "+str(int(round(vr)))+" kias"
		else:
			V1=""
		return V1
	
	def getCC(self, DA, alt, delISA, wgt, AC): #Get cruise-climb speed
		if AC=="B190":
			wgts=(10,12,14,16,16.6)
			spds=(121,125,130,134,135)
			wgt_i=(wgt-16000)/600 if wgt>16000 else (wgt-10000)/2000
			wgt_ih, wgt_il = self.get_index(wgt_i, len(wgts))
			cc=self.interp(spds[wgt_ih], spds[wgt_il], wgts[wgt_ih], wgts[wgt_il], wgt/1000)
			bestCC=str(int(round(cc)))+" kias"
		elif AC=="PC12":
			alts=tuple(range(0,30001,5000))
			ias=((160,160,160,160,160,150,125),	# -40
				(160,160,160,160,160,150,125),	# -30
				(160,160,160,160,155,142,125),	# -20
				(160,160,160,160,148,135,120),	# -10
				(160,160,160,150,140,130,115),	# +0
				(160,160,155,140,130,120,110),	# +10
				(160,155,140,130,120,110,110),	# +20
				(150,140,130,120,110,110,110))	# +30
			dis=tuple(range(-40,31,10))
			alt_i=alt/5000
			dis_i=delISA/10+4
			alt_ih, alt_il = self.get_index(alt_i, len(alts))
			dis_ih, dis_il = self.get_index(dis_i, len(dis))
			cc=self.interp2(ias[dis_ih][alt_il], ias[dis_il][alt_il], ias[dis_ih][alt_ih], ias[dis_il][alt_ih], dis[dis_ih], dis[dis_il], alts[alt_ih], alts[alt_il], delISA, alt)
			bestCC=str(int(round(cc)))+" kias"
		elif AC=="DH8D":
			wgts=tuple(range(39600,63801,1100),64500)
			ias=(130,130,130,130,131,133,134,135,137,139,140,141,143,144,146,147,148,150,151,153,154,155,157,158)
			wgt_i=(wgt-39600)/1100 if wgt<63800 else (wgt-63800)/700
			wgt_ih, wgt_il = self.get_index(wgt_i, len(wgts))
			cc=self.interp(ias[wgt_ih], ias[wgt_il], wgts[wgt_ih], wgts[wgt_il], wgt)
			bestCC=str(int(round(cc)))+" kias"
		elif AC=="IL14":
			bestCC="119 kias 2400/1050"
		elif AC=="B752":
			#M0.43-M0.47 to 16k, <M0.82 (?)
			#300 kias to FL180, M0.68 to FL240, M0.80 above (Atlantic Sun)
			#290 kias to FL180, 300 kias to FL270 or 500-1000 fpm (DALVA)
			if alt<10000:
				CC="250 kias"
			elif DA<18000:
				CC="300 kias"
			elif DA<24000:
				CC="M0.68"
			else:
				CC="M0.80"
			bestCC=CC
		elif AC=="CRJ2":
			if alt<10000:
				CC="250 kias"
			else:
				CC="280 kias"
			bestCC=CC
		else:
			bestCC="N/A"
		return bestCC
	
	def getOptFL(self, wgt, AC): #Get optimum FL
		if AC=="B738":
			wts=tuple(range(120,181,5))
			alts=(39700, 38800, 38000, 37200, 36500, 35700, 35000, 34300, 33700, 33000, 32400, 31700, 31100)
			wt_i=wgt/5000-24
			wt_ih, wt_il = self.get_index(wt_i, len(wts))
			oa=self.interp(alts[wt_ih], alts[wt_il], wts[wt_ih], wts[wt_il], wgt/1000)
			FLalt=str(round(oa,-2))
			optFL="FL"+FLalt[0:3]
		else:
			optFL="N/A"
		return optFL
	
	def getMaxFL(self, wgt, delISA, AC): #Get max FL
		if AC=="B738":
			GW=tuple(range(120,181,5))
			alts=((41000,41000,40500,39800,39100,38500,37800,37200,36600,36000,35300,34600,33800),	# +10C,below
				(40900,40200,39500,38800,38200,37500,36900,36200,35600,34900,34000,33100,32100),	# +15C
				(39700,39000,38300,37600,37000,36200,35500,34700,33800,32800,31500,30300,29100))	# +20C,above
			temps=(10,15,20)
			wt_i=wgt/5000-24
			dI_i=delISA/5-2
			if dI_i<0: #+10 and +20 are to be used for temps below/above those as well
				dI_i=0
			elif dI_i>2:
				dI_i=2
			wt_ih, wt_il = self.get_index(wt_i, len(GW))
			dI_ih, dI_il = self.get_index(dI_i, len(temps))
			ma=self.interp2(alts[dI_ih][wt_il], alts[dI_il][wt_il], alts[dI_ih][wt_ih], alts[dI_il][wt_ih], temps[dI_ih], temps[dI_il], GW[wt_ih], GW[wt_il], delISA, wgt/1000)
			FLalt=str(round(ma,-2))
			maxFL="FL"+FLalt[0:3]
		else:
			maxFL="N/A"
		return maxFL
	
	def getCruise(self, DA, wgt, alt, delISA, AC): #Get cruise speed
		if AC=="B738":
			if DA>42000: #Over service ceiling
				bestCruise="Descend"
			elif alt<10000: #Follow speed limit
				bestCruise="250 kts"
			elif DA<24000: #No data provided
				bestCruise="280 kts"
			else: # Use LR cruise table from manual
				machs=((.601,.61,.619,.627,.636,.643,.652,.661,.671,.683,.695,.706,.718,.729),	# FL250
					(.683,.647,.658,.690,.684,.698,.711,.725,.738,.749,.757,.764,.769,.773),	# FL290
					(.690,.706,.723,.738,.751,.760,.768,.773,.777,.781,.785,.788,.791,.794),	# FL330
					(.726,.742,.754,.764,.771,.776,.780,.784,.788,.792,.794,.795,.795,0),		# FL350
					(.756,.766,.773,.778,.783,.787,.791,.794,.765,.794,0,0,0,0),				# FL370
					(.774,.780,.785,.789,.793,.795,.795,0,0,0,0,0,0,0),							# FL390
					(.786,.791,.794,.795,0,0,0,0,0,0,0,0,0,0))									# FL410
				GW=tuple(range(110,176,5))
				alts=(25,29,33,35,37,39,41)
				if DA<33000:
					wt_i=wgt/5000-22
					fl_i=alt/4000-6.25
				else: #33000 to ceiling
					wt_i=wgt/5000-22
					fl_i=alt/2000-14.5
				fl_ih, fl_il = self.get_index(fl_i, len(alts))
				wt_ih, wt_il = self.get_index(wt_i, len(GW))
				while machs[fl_ih][wt_il]==0 or machs[fl_il][wt_il]==0 or machs[fl_ih][wt_ih]==0 or machs[fl_il][wt_ih]==0:
					wt_il-=1
					wt_ih-=1
				bc=self.interp2(machs[fl_ih][wt_il], machs[fl_il][wt_il], machs[fl_ih][wt_ih], machs[fl_il][wt_ih], alts[fl_ih], alts[fl_il], GW[wt_ih], GW[wt_il], DA/1000, wgt/1000)
				bestCruise="M"+str(round(bc,2))
		elif AC=="PC12": # PIM Section 5
			GW=(7000,8000,9000,10000,10400)
			alts=tuple(range(0,30001,2000))
			ias=(((218,212,207,202,196,191,185,179,173,167,160,154,147,139,132,123),	# 7000lb	-40C
				(217,212,207,202,196,191,186,180,175,169,163,156,150,143,136,129),		# 8000lb
				(216,211,206,201,196,191,186,181,176,170,164,159,153,147,140,133),		# 9000lb
				(214,210,205,201,196,191,186,181,176,171,166,160,155,149,143,137),		# 10000lb
				(214,209,205,200,196,191,186,181,176,171,166,161,155,150,144,138)),		# 10400lb
				((216,211,205,200,194,189,183,177,171,165,159,152,145,137,130,121),		# 7000lb	-30C
				(215,210,205,200,194,189,184,178,173,167,161,154,148,141,134,126),		# 8000lb
				(214,209,204,199,194,189,184,179,174,168,162,157,151,144,138,131),		# 9000lb
				(212,208,203,199,194,189,184,179,174,169,163,158,152,146,140,134),		# 10000lb
				(212,207,203,198,194,189,184,179,174,169,164,158,153,147,141,135)),		# 10400lb
				((214,209,204,198,193,187,181,175,169,163,157,150,143,135,128,119),		# 7000lb	-20C
				(213,208,203,198,193,187,182,176,171,165,159,152,146,139,132,124),		# 8000lb
				(212,207,202,197,193,188,182,177,172,166,160,155,148,142,135,128),		# 9000lb
				(211,206,201,197,192,187,182,177,172,167,161,156,150,144,138,131),		# 10000lb
				(210,206,201,197,192,187,182,177,172,167,161,156,151,145,139,132)),		# 10400lb
				((212,207,202,197,191,185,179,174,168,162,155,148,141,134,126,117),		# 7000lb	-10C
				(212,206,201,196,191,185,180,175,169,163,157,150,144,137,130,122),		# 8000lb
				(210,205,201,196,191,186,181,175,170,164,158,152,146,140,133,126),		# 9000lb
				(209,204,200,195,190,185,180,175,170,164,159,154,148,142,136,129),		# 10000lb
				(208,204,199,195,190,185,180,175,170,165,159,154,148,142,136,130)),		# 10400lb
				((211,206,200,195,189,184,178,172,166,160,153,146,139,132,124,116),		# 7000lb	+0C
				(210,205,200,194,189,184,178,173,167,161,155,149,142,135,128,120),		# 8000lb
				(209,204,199,194,189,184,179,173,168,162,156,150,144,138,131,124),		# 9000lb
				(207,203,198,193,188,183,178,173,168,162,157,151,146,139,133,126),		# 10000lb
				(207,202,198,193,188,183,178,173,168,163,157,152,147,140,134,127)),		# 10400lb
				((209,204,199,193,188,182,176,170,164,158,151,145,138,130,123,114),		# 7000lb	+10C
				(208,203,198,193,187,182,177,171,165,159,153,147,140,134,126,118),		# 8000lb
				(207,202,197,192,187,182,177,171,166,160,154,148,142,136,129,122),		# 9000lb
				(205,201,196,192,187,181,176,171,166,161,155,150,143,137,131,123),		# 10000lb
				(205,200,196,191,186,181,176,171,166,161,155,150,144,138,132,124)),		# 10400lb
				((208,203,197,192,186,180,175,169,163,156,150,143,136,129,121,112),		# 7000lb	+20C
				(207,202,196,191,186,181,175,170,163,157,151,145,138,132,124,116),		# 8000lb
				(205,200,196,191,186,181,175,170,164,158,153,147,141,134,127,119),		# 9000lb
				(204,199,195,190,185,180,175,169,164,159,153,148,141,135,128,120),		# 10000lb
				(203,199,194,189,184,179,174,169,164,159,154,148,142,136,129,121)),		# 10400lb
				((206,201,196,190,185,179,173,167,161,155,148,142,135,127,119,110),		# 7000lb	+30C
				(205,200,195,190,184,179,174,168,162,156,150,143,137,130,122,114),		# 8000lb
				(204,199,194,189,184,179,173,168,162,157,151,145,139,132,125,116),		# 9000lb
				(202,198,193,188,183,178,173,168,162,157,151,146,140,133,126,117),		# 10000lb
				(202,197,193,188,183,178,173,168,162,157,152,146,140,134,127,118)))		# 10400lb
			dis=tuple(range(-40,31,10))
			wgt_i=wgt/400-22 if wgt>10000 else wgt/1000-7
			alt_i=alt/2000
			dis_i=delISA/10+4
			wgt_ih, wgt_il = self.get_index(wgt_i, len(GW))
			alt_ih, alt_il = self.get_index(alt_i, len(alts))
			dis_ih, dis_il = self.get_index(dis_i, len(dis))
			#print "al: "+str(round(alt))+" wt: "+str(round(wgt))+" di: "+str(round(delISA))
			#print "index: "+str(alt_il)+" "+str(alt_ih)+" "+str(wgt_il)+" "+str(wgt_ih)+" "+str(dis_il)+" "+str(dis_ih)
			bc_l=self.interp2(ias[dis_ih][wgt_il][alt_il], ias[dis_il][wgt_il][alt_il], ias[dis_ih][wgt_il][alt_ih], ias[dis_il][wgt_il][alt_ih], dis[dis_ih], dis[dis_il], alts[alt_ih], alts[alt_il], delISA, alt)
			bc_h=self.interp2(ias[dis_ih][wgt_ih][alt_il], ias[dis_il][wgt_ih][alt_il], ias[dis_ih][wgt_ih][alt_ih], ias[dis_il][wgt_ih][alt_ih], dis[dis_ih], dis[dis_il], alts[alt_ih], alts[alt_il], delISA, alt)
			bc=self.interp(bc_h, bc_l, GW[wgt_ih], GW[wgt_il], wgt)
			bestCruise=str(int(round(bc)))+" kias"
		elif AC=="DH8D":
			bestCruise="360 ktas"
		elif AC=="B190": #LR - 1400 RPM  Else - 1550 RPM
			wgts=(10000,12000,13000,14000,15000,16500)
			dalts=tuple(range(0,25001,1000))
			spds=((180,178,176,174,172,170,168,167,165,163,161,159,157,156,154,153,151,150,148,147,146,145,143,142,140,139),	#10000lb
				(183,181,179,177,176,174,172,171,169,167,165,164,162,161,160,159,158,156,155,154,152,151,150,149,148,146),	#12000lb
				(184,183,181,179,178,176,174,173,171,170,168,167,166,165,164,162,161,160,158,157,156,154,153,152,151,148),	#13000lb
				(186,184,183,181,180,178,177,176,174,173,172,171,169,168,167,165,164,163,162,160,159,158,156,154,152,150),	#14000lb
				(188,186,185,184,183,182,181,180,178,177,175,174,172,171,170,169,167,166,165,164,162,159,157,155,153,152),	#15000lb
				(195,194,193,191,190,188,187,185,184,182,180,179,177,176,174,173,172,170,167,165,163,161,160,160,159,158))	#16500lb
			wgt_i=(wgt-16000)/500 if wgt>16000 else (wgt-11000)/1000 if wgt>12000 else (wgt-10000)/2000
			alt_i=DA/1000
			wgt_ih, wgt_il = self.get_index(wgt_i, len(wgts))
			alt_ih, alt_il = self.get_index(alt_i, len(dalts))
			bc=self.interp2(spds[wgt_ih][alt_il], spds[wgt_il][alt_il], spds[wgt_ih][alt_ih], spds[wgt_il][alt_ih], wgts[wgt_ih], wgts[wgt_il], dalts[alt_ih], dalts[alt_il], wgt, DA)
			bestCruise=str(int(round(bc)))+" kias"
		elif AC=="IL14":
			bestCruise="135-184 kias"
		elif AC=="B752":
			bestCruise="M0.80"
		elif AC=="CRJ2":
			bestCruise="M0.74"
		else:
			bestCruise="N/A"
		return bestCruise
	
	def getMaxCruise(self, DA, wgt, alt, delISA, AC): #Get max cruise speed
		if AC=="IL14":
			maxCruise="208 kias"
		elif AC=="B752":
			maxCruise="M0.82"
		else:
			maxCruise="N/A"
		return maxCruise
	
	def getMaxPwr(self, DA, delISA, AC): #Get max power setting
		if AC=="PC12":
			dis=tuple(range(-40,31,10))
			alts=tuple(range(0,30001,5000))
			trqs=((37,37,37,37,37,37,36.75,32.5),	# SL
				(37,37,37,37,37,37,34.5,30.8),	# 5k
				(37,37,37,37,37,34.5,31.3,28.2),	# 10k
				(37,37,37,35.75,33.25,30.7,27.7,24.7),	# 15k
				(37,35.7,33.8,31.75,29.3,26.75,24,21),	# 20k
				(0,0,28.6,27.2,25.25,23.2,21,18.7),	# 25k
				(0,0,0,22.5,21.4,19.8,18.8,16.5))	# 30k
			dis_i=(delISA+40)/40
			alt_i=(DA/5000)
			alt_ih, alt_il = self.get_index(alt_i, len(alts))
			dis_ih, dis_il = self.get_index(dis_i, len(dis))
			while trqs[alt_ih][dis_il]==0 or trqs[alt_il][dis_il]==0 or trqs[alt_ih][dis_ih]==0 or trqs[alt_il][dis_ih]==0:
				dis_il+=1
				dis_ih+=1
			maxtrq=self.interp2(trqs[alt_ih][dis_il], trqs[alt_il][dis_il], trqs[alt_ih][dis_ih], trqs[alt_il][dis_ih], alts[alt_ih], alts[alt_il], dis[dis_ih], dis[dis_il], DA, delISA)
			
			maxpwr=str(round(maxtrq,1))+" psi"
		elif AC=="IL14":
			maxpwr="2600 RPM 1250 MP"
		else:
			maxpwr="N/A"
		return maxpwr
