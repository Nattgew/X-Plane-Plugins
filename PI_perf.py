from XPLMProcessing import * #Flight loops
from XPLMDataAccess import * #Datarefs
from XPLMDisplay import * #Draw window
from XPLMGraphics import * #Draw things
from XPLMDefs import * #Object definitions
from XPLMUtilities import * #Commands
from XPLMNavigation import * #Nav/FMS tools
from XPLMPlugin import *
import math
import re
import os
import fileinput

class getaircraft:
	
	def __init__(self):
		acf_desc_ref=XPLMFindDataRef("sim/aircraft/view/acf_descrip")
		acf_icao_ref=XPLMFindDataRef("sim/aircraft/view/acf_ICAO")
		num_eng_ref=XPLMFindDataRef("sim/aircraft/engine/acf_num_engines")
		eng_type_ref=XPLMFindDataRef("sim/aircraft/prop/acf_en_type")
		prop_type_ref=XPLMFindDataRef("sim/aircraft/prop/acf_prop_type")
		self.acf_EW_ref=XPLMFindDataRef("sim/aircraft/weight/acf_m_empty")
		self.acf_MTOW_ref=XPLMFindDataRef("sim/aircraft/weight/acf_m_max")
		
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
		if desc[0:27]=="['Boeing 737-800 xversion 4" or acf_icao=="B738":
			self.name="B738"
			self.flaps=(0.125,0.375,0.625,0.875,1.0) #1 5 15 30 40
			self.ceiling=42
		elif desc=="['Pilatus PC-12']" or acf_icao=="PC12":
			#XPLMSetDataf(self.acf_EW_ref,2605)
			self.name="PC12"
			self.setEW(self.name,1895)
			self.flaps=(0.3,0.7,1.0) #15 30 40
			self.ceiling=30
			self.maxcabin=10000
			self.agl=1000
		elif desc[0:9]=="['BE1900D" or desc[0:19]=="['B1900 for X-plane" or acf_icao=="B190":
			self.name="B190"
			self.setEW(self.name,2985)
			self.ceiling=25
			self.maxcabin=10000
			self.agl=1500
		elif desc=="['Bombardier Challenger 300']" or acf_icao=="CL30":
			self.name="CL30"
			self.setEW(self.name,6849)
			self.ceiling=45
		elif desc[0:21]=="['C208B Grand Caravan" or acf_icao=="C208":
			self.name="C208"
			self.setEW(self.name,1910)
			self.ceiling=25
			self.maxcabin=10000
			self.agl=1000
		elif desc=="['DeHavilland Dash 8 Q400']" or acf_icao=="DH8D":
			self.name="DH8D"
			self.setEW(self.name,12071)
			self.flaps=(0.25,0.5,0.75,1.0) #FIX ME 5 10 15 35
			self.ceiling=27
			self.agl=1500
		elif desc=="['L-1049G Constellation']" or acf_icao=="CONI":
			self.name="CONI"
			self.setEW(self.name,31421)
			self.ceiling=24
			self.agl=1500
		elif desc=="['Douglas DC-3']" or acf_icao=="DC3":
			self.name="DC3"
			self.setEW(self.name,4584)
			self.ceiling=23
			self.agl=1000
		elif desc=="['Cessna Citation X']" or acf_icao=="C750":
			self.name="C750"
			self.setEW(self.name,6714)
			self.ceiling=51
		elif desc=="['Dassault Falcon 7X']" or acf_icao=="FA7X":
			self.name="FA7X"
			self.setEW(self.name,16279)
			self.ceiling=51
		elif desc=="['Let L-410']" or acf_icao=="L410":
			self.name="L410"
			self.setEW(self.name,2650)
			self.ceiling=20
			self.agl=1500
		else:
			if acf_icao!="": #I guess we'll trust it
				self.name=acf_icao
			else: #You're flying a what?
				self.name=desc
				print str(desc[0:8])
			self.ceiling=30
	
	def setEW(self,AC,pyld): #Set aircraft EW to match FSE
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
		#print "Interp "+str(y2)+", "+str(y1)+", "+str(x2)+", "+str(x1)+", "+str(round(xi))+" = "+str(round(result))
		#print "Interp result: "+str(result)
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
		# self.num_eng=0
		self.TO_pwr=0
		# self.eng_type=[]
		# self.prop_type=[]
		# self.flaps=(0,1)
		# self.acf_short=""
		self.aircraft=[]
		self.current_dest=""
		self.elevate_dest=0
		self.flightTimerLast=-1
		pass

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
			speed=380 if dist<450 else 420
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
			general_fl=int(dist/10)
			climb=1000 if alt_ind<6000 else 750
			speed=180
			gph=95
		else:
			general_fl=int(dist/10+2) #General rule for PC-12 cruise altitude
			climb=1000
			speed=0
			gph=0
		if speed>0:
			fuel=dist/speed*gph
			XPLMSpeakString("AP fuel estimate: "+str(int(round(fuel)))+" gal")
			#XPLMSetDataf(self.ap_spd_ref, fuel) #Other plugin will show speed change, speed setting not important
		general_fl+=int(dalt/1000+alt_ind/1000)/2 #Account for departure/arrival altitudes
		if aphdg<180: #NEodd
			if general_fl%2==0:
				general_fl-=1
			if general_fl>self.aircraft.ceiling:
				general_fl=self.aircraft.ceiling-1 if self.aircraft.ceiling%2==0 else self.aircraft.ceiling
		else: #SWeven
			if general_fl%2==1:
				general_fl-=1
			if general_fl>self.aircraft.ceiling:
				general_fl=self.aircraft.ceiling-1 if self.aircraft.ceiling%2==1 else self.aircraft.ceiling
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
			# self.aircraft.name=self.getacfshort() #Find name of aircraft
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
			color=1.0, 1.0, 1.0
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
				if torque_psi>37.0: #Takeoff power
					TOP_str=self.get_topwr(300)
				else:
					self.TO_pwr=300
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
			if self.prop_type[0]==0: #Fixed pitch
				RPM=[]
				XPLMGetDatavf(self.RPM_ref, RPM, 0, self.aircraft.num_eng)
				pwr=str(int(round(RPM[0]*60/pi)))+" rpm"
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
		if dest != self.current_dest:
			# r'\b[01] [01] '+dest+r'\b'
			# r'^1(6?|7?)\s+\d{1,5}\s+[01]\s+[01]\s+'+dest+r'\b'
			regex=re.compile(r'^1(6?|7?)\s.*?'+dest+r'\b').search
			dir1=os.path.join('Resources','default scenery','default apt dat','Earth nav data','apt.dat')
			dir2=os.path.join('Custom Scenery','zzzz_FSE_Airports','Earth nav data','apt.dat')
			for line in fileinput.input([dir1,dir2]): # I am forever indebted to Padraic Cunningham for this code
				if regex(line):
					params=line.split()
					dalt=float(params[1])
					break
			else:
				print "AP - "+dest+" not found, giving up"
				dalt=0.0
			fileinput.close()
			self.current_dest=dest
			self.elevate_dest=dalt
		else:
			#print "AP - Reusing elevation value for "+dest
			dalt=self.elevate_dest
		
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
			dnms=((9.6,20.0,31.0,0,0,0), 			# -40
				(9.9,20.2,31.8,43.3,0,0),			# -30
				(10.0,20.7,32.2,44.1,55.8,0),		# -20
				(10.1,21.1,32.8,45.0,56.8,68.4),	# -10
				(10.3,21.6,33.8,46.0,58.0,70.0),	# 0
				(10.5,21.9,34.2,46.8,59.2,71.3),	# 10
				(10.8,22.2,34.8,47.8,60.2,72.4),	# 20
				(11.0,22.5,35.5,48.3,61.4,73.9))	# 30
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
			alts=tuple(range(2000,24001,2000))
			alts.append(25000)
			alts.append(27000)
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
			#TOD=""
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
			GW=tuple(range(90,181,10))
			vrs=((122.0,129.0,135.0,142.0,148.0,154.0,159.0,164.0,169.0,174.0),		# flaps 15
				(116.0,123.0,129.0,135.0,141.0,146.0,151.0,156.0,160.0,165.0),		# flaps 30
				(109.0,116.0,122.0,128.0,133.0,139.0,144.0,148.0,153.0,157.0))		# flaps 40
			flap_i=-1
			for i in range(2,5): #Reference correct flap setting
				if flaps == self.aircraft.flaps[i]:
					flap_i=i-2
			if flap_i==-1:
				Vref="LAND CONFIG"
			else:
				wgt_i=wgt/10000-9
				wgt_ih, wgt_il = self.get_index(wgt_i, len(GW))
				vri=self.interp(vrs[flap_i][wgt_ih], vrs[flap_i][wgt_il], GW[wgt_ih], GW[wgt_il], wgt/1000)
				Vref="  Vref: "+str(int(round(vri)))+" kias"
		elif AC=="PC12": #Assume flaps 40
			GW=tuple(range(6400,10001,900))
			vapps=(67.0,72.0,76.0,80.0,84.0)
			wgt_i=wgt/900-64/9
			wgt_ih, wgt_il = self.get_index(wgt_i, len(GW))
			vapp=self.interp(vapps[wgt_ih], vapps[wgt_il], GW[wgt_ih], GW[wgt_il], wgt)
			#print 'Vref %.0f %.0f %.0f %.0f %.0f = %.0f' % (vapps[wgt_ih], vapps[wgt_il], GW[wgt_ih], GW[wgt_il], wgt, vapp)
			Vref="  Vref: "+str(int(round(vapp)))+" kias"
		elif AC=="DH8D":
			wgts=tuple(range(39600,63801,1100))
			wgts.append(64500)
			ias=((124,127,128,129,131,133,134,135,137,139,140,142,143,145,146,147,149,150,152,153,155,155,157,158),	#0 deg
				(114,115,117,118,120,122,124,125,126,127,129,130,132,133,134,136,137,138,139,141,142,143,145,145),	#5
				(108,108,109,110,112,113,115,116,117,118,120,121,122,124,125,126,127,129,130,131,132,134,136,136),	#10
				(105,105,105,105,107,108,109,110,112,113,114,115,117,118,119,120,121,123,124,125,126,128,130,129),	#15
				(101,101,101,101,102,103,104,106,107,108,109,110,112,113,114,115,116,117,118,119,120,122,122,123))	#35
			flap_i=-1
			if flaps==0:
				flap_i=0
			else:
				for i in range(5): #Reference correct flaps setting
					if flaps == self.aircraft.flaps[i]:
						flap_i=i
			if flap_i==-1:
				V1=""
			else:
				wgt_i=(wgt-39600)/1100 if wgt<63800 else (wgt-63800)/700
				wgt_ih, wgt_il = self.get_index(wgt_i, len(wgts))
				vr=self.interp(ias[flap_i][wgt_ih], ias[flap_i][wgt_il], wgts[wgt_ih], wgts[wgt_il], wgt)
				Vref="  Vref: "+str(int(round(vr)))+" kias"
		else:
			Vref=""
		return Vref

	def getV1(self, flaps, wgt, DA, T, AC): #Get V1 speed
		if AC=="B738":
			GW=tuple(range(90,181,10))
			alts=tuple(range(0,8001,2000))
			#Determine conditions class
			if T < 27 and DA < alts[1] or T < 38 and DA < alts[1] and (-T+38)/5.5 <= DA/1000: # A cyan
				v1s=((107.0,114.0,121.0,127.0,133.0,139.0,145.0,150.0,155.0,160.0),	# flaps 1
					(103.0,109.0,116.0,122.0,128.0,134.0,139.0,144.0,149.0,153.0),	# flaps 5
					(99.0,106.0,112.0,118.0,124.0,130.0,135.0,140.0,145.0,150.0))	# flaps 15
			elif T < 27 and DA < alts[2] or T < 38 and DA < alts[2] and (-T+38)/11 <= DA/1000-3 or T < 43 and DA < (alts[2]+alts[1])/2 and (-T+43)/(5/3) <= DA/1000: #B yellow
				v1s=((108.0,115,122.0,128.0,134.0,140.0,146.0,151.0,156.0,161.0),	# flaps 1
					(104.0,110.0,117.0,123.0,129.0,135.0,140.0,145.0,150.0,154.0),	# flaps 5
					(100.0,107.0,113.0,119.0,125.0,131.0,136.0,141.0,146.0,0))	# flaps 15
			elif T < 27 and DA < alts[3] or T < 38 and DA < alts[3] and (-T+38)/5.5 <= DA/1000-4 or T < 49 and DA < (alts[3]+alts[2])/2 and (-T+49)/2.75 <= DA/1000: #C pink
				v1s=((109.0,116.0,123.0,129.0,135.0,141.0,147.0,152.0,157.0,162.0),	# flaps 1
					(105.0,111.0,118.0,124.0,130.0,136.0,141.0,146.0,151.0,0),	# flaps 5
					(101.0,108.0,114.0,120.0,126.0,132.0,137.0,142.0,0,0))		# flaps 15
			elif T < 60 and DA/1000 < 160/11 and (-T+60)/4.125 <= DA/1000: #D green
				v1s=((110.0,117.0,124.0,130.0,136.0,142.0,148.0,153.0,158.0,0),	# flaps 1
					(106.0,112.0,119.0,125.0,131.0,137.0,142.0,147.0,0,0),		# flaps 5
					(102.0,109.0,115.0,121.0,127.0,133.0,138.0,0,0,0))		# flaps 15
			else: #E blue uh oh
				v1s=((112.0,119.0,126.0,132.0,138.0,144.0,150.0,155.0,0,0),		# flaps 1
					(108.0,114.0,121.0,127.0,133.0,139.0,0,0,0,0),			# flaps 5
					(104.0,111.0,117.0,123.0,129.0,0,0,0,0,0))			# flaps 15
			flap_i=-1
			for i in range(3): #Reference correct flaps setting
				if flaps == self.aircraft.flaps[i]:
					flap_i=i
			if flap_i==-1:
				V1=""
			else:
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
			GW=(6400,7300,8200,9100,10000,10450)
			vrs=((63,67,71,75,79,81),	# flaps 15
				(58,62,66,70,73,75))	# flaps 30
			#vas=((65,70,74,78,82,84), # flaps 15, Accelerate-stop, not used right now
			#(59,63,67,71,74,76)) # flaps 30
			flap_i=-1
			for i in range(0,2):
				if round(flaps,1) == self.aircraft.flaps[i]:
					flap_i=i
			if flap_i==-1:
				V1="  V1: Check Flaps"
			else:
				wgt_i=wgt/900-64/9 if wgt<10000 else wgt/450-164/9
				wgt_ih, wgt_il = self.get_index(wgt_i, len(GW))
				#print 'Interp: %.0f %.0f %.0f %.0f %.0f' % (vrs[flap_i][wgt_ih], vrs[flap_i][wgt_il], GW[wgt_ih], GW[wgt_il], wgt)
				vr=self.interp(vrs[flap_i][wgt_ih], vrs[flap_i][wgt_il], GW[wgt_ih], GW[wgt_il], wgt)
				V1="  V1: "+str(int(round(vr)))+" kias"
		elif AC=="DH8D":
			wgts=tuple(range(39600,63801,1100))
			wgts.append(64500)
			ias=((108,108,108,108,108,108,109,111,113,114,116,117,119,120,122,123,125,126,128,129,131,132,134,134),	#5 deg
				(104,104,104,104,104,104,104,104,104,106,107,109,110,112,113,114,116,117,119,120,121,123,124,125),	#10
				(100,100,100,100,100,100,100,100,101,102,104,105,107,108,109,111,112,113,114,116,117,118,119,120))	#15
			flap_i=-1
			for i in range(3): #Reference correct flaps setting
				if flaps == self.aircraft.flaps[i]:
					flap_i=i 
			if flap_i==-1:
				V1=""
			else:
				wgt_i=(wgt-39600)/1100 if wgt<63800 else (wgt-63800)/700
				wgt_ih, wgt_il = self.get_index(wgt_i, len(wgts))
				vr=self.interp(ias[flap_i][wgt_ih], ias[flap_i][wgt_il], wgts[wgt_ih], wgts[wgt_il], wgt)
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
			ias=((160.0,160.0,160.0,160.0,160.0,150.0,125.0),	# -40
				(160.0,160.0,160.0,160.0,160.0,150.0,125.0),	# -30
				(160.0,160.0,160.0,160.0,155.0,142.0,125.0),	# -20
				(160.0,160.0,160.0,160.0,148.0,135.0,120.0),	# -10
				(160.0,160.0,160.0,150.0,140.0,130.0,115.0),	# +0
				(160.0,160.0,155.0,140.0,130.0,120.0,110.0),	# +10
				(160.0,155.0,140.0,130.0,120.0,110.0,110.0),	# +20
				(150.0,140.0,130.0,120.0,110.0,110.0,110.0))	# +30
			dis=tuple(range(-40,31,10))
			alt_i=alt/5000
			dis_i=delISA/10+4
			alt_ih, alt_il = self.get_index(alt_i, len(alts))
			dis_ih, dis_il = self.get_index(dis_i, len(dis))
			cc=self.interp2(ias[dis_ih][alt_il], ias[dis_il][alt_il], ias[dis_ih][alt_ih], ias[dis_il][alt_ih], dis[dis_ih], dis[dis_il], alts[alt_ih], alts[alt_il], delISA, alt)
			bestCC=str(int(round(cc)))+" kias"
		elif AC=="DH8D":
			wgts=tuple(range(39600,63801,1100))
			wgts.append(64500)
			ias=(130,130,130,130,131,133,134,135,137,139,140,141,143,144,146,147,148,150,151,153,154,155,157,158)
			wgt_i=(wgt-39600)/1100 if wgt<63800 else (wgt-63800)/700
			wgt_ih, wgt_il = self.get_index(wgt_i, len(wgts))
			cc=self.interp(ias[wgt_ih], ias[wgt_il], wgts[wgt_ih], wgts[wgt_il], wgt)
			bestCC=str(int(round(cc)))+" kias"
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
			alts=((41000, 41000, 40500, 39800, 39100, 38500, 37800, 37200, 36600, 36000, 35300, 34600, 33800),	# +10C, below
				(40900, 40200, 39500, 38800, 38200, 37500, 36900, 36200, 35600, 34900, 34000, 33100, 32100),	# +15C
				(39700, 39000, 38300, 37600, 37000, 36200, 35500, 34700, 33800, 32800, 31500, 30300, 29100))	# +20C, above
			temps=(10,15,20)
			wt_i=wgt/5000-24
			dI_i=delISA/5-2
			if dI_i < 0: #+10 and +20 are to be used for temps below/above those as well
				dI_i=0
			elif dI_i > 2:
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
			bc=self.interp2(spds[wgt_ih][alt_il], spds[wgt_il][alt_il], spds[wgt_ih][alt_ih], spds[wgt_il][alt_ih], wgts[wgt_ih], wgts[wgt_il], dalts[alts_ih], dalts[alts_il], wgt, DA)
			bestCruise=str(int(round(bc)))+" kias"
		else:
			bestCruise="N/A"
		return bestCruise
	
	def getMaxCruise(self, DA, wgt, alt, delISA, AC): #Get max cruise speed
		maxCruise="N/A"
		return maxCruise
	
	def getMaxPwr(self, DA, delISA, AC): #Get max power setting
		if AC=="PC12":
			dis=tuple(range(-40,31,10))
			alts=tuple(range(0,30001,5000))
			trqs=((37.0,37.0,37.0,37.0,37.0,37.0,36.75,32.5),	# SL
				(37.0,37.0,37.0,37.0,37.0,37.0,34.5,30.8),	# 5k
				(37.0,37.0,37.0,37.0,37.0,34.5,31.3,28.2),	# 10k
				(37.0,37.0,37.0,35.75,33.25,30.7,27.7,24.7),	# 15k
				(37.0,35.7,33.8,31.75,29.3,26.75,24.0,21.0),	# 20k
				(0,0,28.6,27.2,25.25,23.2,21.0,18.7),	# 25k
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
		else:
			maxpwr="N/A"
		return maxpwr
