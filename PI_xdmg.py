from XPLMProcessing import *
from XPLMDataAccess import *
from XPLMDisplay import *
from XPLMGraphics import *
from XPLMDefs import *
from XPLMUtilities import *

class PythonInterface:

	def XPluginStart(self):
		self.Name="XFSE Info"
		self.Sig= "natt.python.fsei"
		self.Desc="Shows info for FSE"
		self.VERSION="1.4"
		
		self.OAT_ref=XPLMFindDataRef("sim/weather/temperature_ambient_c")
		self.RPM_ref=XPLMFindDataRef("sim/flightmodel/engine/ENGN_N2_")
		self.CHT_ref=XPLMFindDataRef("sim/flightmodel/engine/ENGN_CHT_c")
		self.ITT_ref=XPLMFindDataRef("sim/flightmodel/engine/ENGN_ITT_c")
		#self.EGT_ref=XPLMFindDataRef("sim/flightmodel/engine/ENGN_EGT_c")
		self.mix_ref=XPLMFindDataRef("sim/flightmodel/engine/ENGN_mixt")
		#self.flightTime_ref=XPLMFindDataRef("sim/time/total_flight_time_sec")
		self.num_eng_ref=XPLMFindDataRef("sim/aircraft/engine/acf_num_engines")
		self.alt_ref=XPLMFindDataRef("sim/flightmodel/position/y_agl")
		self.eng_type_ref=XPLMFindDataRef("sim/aircraft/prop/acf_en_type")
		self.prop_type_ref=XPLMFindDataRef("sim/aircraft/prop/acf_prop_type")
		
		#self.r_ITT_ref=XPLMFindDataRef("sim/aircraft/limits/red_lo_ITT")
		#self.rh_ITT_ref=XPLMFindDataRef("sim/aircraft/limits/red_hi_ITT")
		#self.g_ITT_ref=XPLMFindDataRef("sim/aircraft/limits/green_lo_ITT")
		#self.gh_ITT_ref=XPLMFindDataRef("sim/aircraft/limits/green_hi_ITT")
		#self.r_EGT_ref=XPLMFindDataRef("sim/aircraft/limits/red_lo_EGT")
		#self.rh_EGT_ref=XPLMFindDataRef("sim/aircraft/limits/red_hi_EGT")
		#self.g_EGT_ref=XPLMFindDataRef("sim/aircraft/limits/green_lo_EGT")
		#self.gh_EGT_ref=XPLMFindDataRef("sim/aircraft/limits/green_hi_EGT")
		#self.r_CHT_ref=XPLMFindDataRef("sim/aircraft/limits/red_lo_CHT")
		#self.rh_CHT_ref=XPLMFindDataRef("sim/aircraft/limits/red_hi_CHT")
		#self.g_CHT_ref=XPLMFindDataRef("sim/aircraft/limits/green_lo_CHT")
		#self.gh_CHT_ref=XPLMFindDataRef("sim/aircraft/limits/green_hi_CHT")
		#self.gs_ref=XPLMFindDataRef("sim/flightmodel/position/groundspeed")
		self.m_EGT_ref=XPLMFindDataRef("sim/aircraft/engine/acf_max_EGT")
		self.m_ITT_ref=XPLMFindDataRef("sim/aircraft/engine/acf_max_ITT")
		self.m_CHT_ref=XPLMFindDataRef("sim/aircraft/engine/acf_max_CHT")
		self.ias_ref=XPLMFindDataRef("sim/flightmodel/position/indicated_airspeed")
		self.fly_ref=XPLMFindDataRef("fse/status/flying")
		self.acf_desc_ref=XPLMFindDataRef("sim/aircraft/view/acf_descrip")
		self.pbrake_ref=XPLMFindDataRef("sim/flightmodel/controls/parkbrake")	#float	660+	yes	[0..1]	Parking Brake, 1 = max
		self.flap_h_pos_ref=XPLMFindDataRef("sim/cockpit2/controls/flap_ratio")

		self.started=0
		self.err=0
		self.msg=[]
		for i in range(0,5):
			self.msg.append("")
		self.e1=""
		winPosX=20
		winPosY=300
		ePosX=20
		ePosY=400
		win_w=230
		win_h=80
		self.end_flight=0
		self.num_eng=0
		self.runtime=0
		self.chtDamage=0
		self.mixtureDamage=0
		self.eng_type=[]
		self.prop_type=[]

		self.gameLoopCB=self.gameLoopCallback
		self.DrawWindowCB=self.DrawWindowCallback
		self.DrawWarnCB=self.DrawWarnCallback
		self.KeyCB=self.KeyCallback
		self.MouseClickCB=self.MouseClickCallback
		self.gWindow=XPLMCreateWindow(self, winPosX, winPosY, winPosX + win_w, winPosY - win_h, 1, self.DrawWindowCB, self.KeyCB, self.MouseClickCB, 0)
		self.eWindow=XPLMCreateWindow(self, ePosX, ePosY, ePosX + win_w, ePosY - win_h, 1, self.DrawWarnCB, self.KeyCB, self.MouseClickCB, 0)

		self.CmdSHConn = XPLMCreateCommand("fsei/flight/showhide","Shows or hides FSE damage info")
		self.CmdSHConnCB  = self.CmdSHConnCallback
		XPLMRegisterCommandHandler(self, self.CmdSHConn,  self.CmdSHConnCB, 0, 0)
		
		self.CmdMxConn = XPLMCreateCommand("fsei/flight/mixture","Sets mixture to ground idle")
		self.CmdMxConnCB  = self.CmdMxConnCallback
		XPLMRegisterCommandHandler(self, self.CmdMxConn,  self.CmdMxConnCB, 0, 0)
		
		self.CmdFSEendConn = XPLMCreateCommand("fsei/flight/finish","Runs steps to finish flight")
		self.CmdFSEendConnCB  = self.CmdFSEendConnCallback
		XPLMRegisterCommandHandler(self, self.CmdFSEendConn,  self.CmdFSEendConnCB, 0, 0)
		
		return self.Name, self.Sig, self.Desc

	def MouseClickCallback(self, inWindowID, x, y, inMouse, inRefcon):
		return 0

	def KeyCallback(self, inWindowID, inKey, inFlags, inVirtualKey, inRefcon, losingFocus):
		pass 

	def CmdSHConnCallback(self, cmd, phase, refcon):
		if(phase==0): #KeyDown event
			print "XDMG = CMD show or hide"
			self.showhide()
		return 0
	
	def CmdMxConnCallback(self, cmd, phase, refcon):
		if(phase==0): #KeyDown event
			print "XDMG = CMD mix set"
			if self.eng_type[0]==2 or self.eng_type[0]==8: #Turboprop
				self.MixTape(0.45)
			elif self.eng_type[0]==4 or self.eng_type[0]==5: #Jet
				self.MixTape(0.949)
			else:
				self.MixTape(0.949)
		return 0
	
	def CmdFSEendConnCallback(self, cmd, phase, refcon):
		if(phase==0): #KeyDown event
			print "XDMG = Finish FSE flight..."
			self.end_flight=5
		return 0
		
	def showhide(self):
		if self.started == 0:
			self.num_eng=XPLMGetDatai(self.num_eng_ref)
			XPLMGetDatavi(self.eng_type_ref, self.eng_type, 0, self.num_eng)
			XPLMGetDatavi(self.prop_type_ref, self.prop_type, 0, self.num_eng)
			self.m_EGT=XPLMGetDataf(self.m_EGT_ref)
			self.m_ITT=XPLMGetDataf(self.m_ITT_ref)
			self.m_CHT=XPLMGetDataf(self.m_CHT_ref)
			self.defaultcht=XPLMGetDataf(self.OAT_ref)
			XPLMRegisterFlightLoopCallback(self, self.gameLoopCB, 0.25, 0)
			self.started=1
		else:
			self.started=0
			self.err=0
			XPLMUnregisterFlightLoopCallback(self, self.gameLoopCB, 0)
			self.prop_type=[]
			self.eng_type=[]
			self.runtime=0
			self.chtDamage=0
			self.mixtureDamage=0
			
	def DrawWindowCallback(self, inWindowID, inRefcon):
		if self.started==1:
			lLeft=[]; lTop=[]; lRight=[]; lBottom=[]
			XPLMGetWindowGeometry(inWindowID, lLeft, lTop, lRight, lBottom)
			left=int(lLeft[0]); top=int(lTop[0]); right=int(lRight[0]); bottom=int(lBottom[0])
			XPLMDrawTranslucentDarkBox(left,top,right,bottom)
			color=1.0, 1.0, 1.0
			for i in range(0,5):
				XPLMDrawString(color, left+5, top-(20+15*i), self.msg[i], 0, xplmFont_Basic)

	def DrawWarnCallback(self, inWindowID, inRefcon):
		if self.err==1:
			lLeft=[]; lTop=[]; lRight=[]; lBottom=[]
			XPLMGetWindowGeometry(inWindowID, lLeft, lTop, lRight, lBottom)
			left=int(lLeft[0]); top=int(lTop[0]); right=int(lRight[0]); bottom=int(lBottom[0])
			XPLMDrawTranslucentDarkBox(left,top,right,bottom)
			color=1.0, 0.0, 0.0
			XPLMDrawString(color, left+5, top-20, self.e1, 0, xplmFont_Basic)
	
	def XPluginStop(self):
		if self.started==1:
			self.showhide()
		XPLMUnregisterCommandHandler(self, self.CmdFSEendConn,  self.CmdFSEendConnCB, 0, 0)
		XPLMUnregisterCommandHandler(self, self.CmdSHConn, self.CmdSHConnCB, 0, 0)
		XPLMUnregisterCommandHandler(self, self.CmdMxConn, self.CmdMxConnCB, 0, 0)
		XPLMDestroyWindow(self, self.gWindow)
		XPLMDestroyWindow(self, self.eWindow)
		pass

	def XPluginEnable(self):
		return 1

	def XPluginDisable(self):
		pass

	def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
		pass

	def MixTape(self, m):
		#print "XDMG = Setting mixture "+str(round(m,2))
		XPLMSetDatavf(self.mix_ref, [m, m, m, m, m, m, m, m], 0, self.num_eng)
		return 0 #Maybe?
	
	def CPtoggle(self):
		print "XDMG = Running cutoff toggle function..."
		cutoff_toggle_cmd=XPLMFindCommand("pc12/engine/cutoff_protection_toggle")
		if cutoff_toggle_cmd is not None:
			print "XDMG = Found command, toggling switch"
			XPLMCommandOnce(cutoff_toggle_cmd)
			# XPLMCommandBegin(cutoff_toggle_cmd)
			# XPLMCommandEnd(cutoff_toggle_cmd)
		return 0 #Maybe?

	def gameLoopCallback(self, inElapsedSinceLastCall, elapsedSim, counter, refcon):
		newdmg=1 #Whether to try new damage calculating method
		rpms=[]
		XPLMGetDatavf(self.RPM_ref, rpms, 0, self.num_eng)
		if rpms[0]>0:
			self.runtime+=1
		altitude=XPLMGetDataf(self.alt_ref)*3.33
		ias=XPLMGetDataf(self.ias_ref)
		flying=XPLMGetDatai(self.fly_ref)
		if flying==0 and ias>60 and (altitude<20 or altitude>10000 and altitude<11000):
			self.e1="FSE FLIGHT NOT STARTED"
			self.err=1
			return 1
		else:
			self.err=0
		mixes=[]
		XPLMGetDatavf(self.mix_ref, mixes, 0, self.num_eng)
		if (mixes[0] > 0.95 and altitude > 900):
			self.MixTape(0.949)	
			
		#FSE flight end stuff
		if self.end_flight==5:
			print "XDMG - Parking brake set, toggle cutoff protection, flaps up"
			XPLMSetDataf(self.pbrake_ref, 1.0)
			if self.eng_type[0]==2 or self.eng_type[0]==8: #Turboprop
				self.CPtoggle() #Toggle the cutoff protection on PC-12
			XPLMSetDataf(self.flap_h_pos_ref, 0.0) #Retract flaps full
			self.end_flight=4
		elif self.end_flight==4:
			print "XDMG - Mixture cutoff"
			self.MixTape(0.0)
			self.end_flight=3
		elif self.end_flight==3:
			print "XDMG - Mixture restore"
			if self.eng_type[0]==2 or self.eng_type[0]==8: #Turboprop
				self.MixTape(0.45)
			else:
				self.MixTape(1.0)
			self.end_flight=2
		elif self.end_flight==2:
			if self.eng_type[0]==2 or self.eng_type[0]==8: #Turboprop
				print "XDMG - Toggle cutoff protection"
				self.CPtoggle()
			self.end_flight=0
		
		if newdmg==0: #Use standard FSE damage calcs
			#Let's do some damage
			chts=[]
			XPLMGetDatavf(self.CHT_ref, chts, 0, self.num_eng)
			if self.defaultcht>0:
				_diff=abs(chts[0]-self.defaultcht)
				if _diff>0:
					self.chtDamage+=_diff
			self.defaultcht=chts[0]
			if (mixes[0] > 0.95 and XPLMGetDataf(self.alt_ref) > 1000): #SMOKIN'
				self.mixtureDamage += 1
			self.msg[1]="CHT: "+str(round(chts[0],2))+" dmg: "+str(round(self.chtDamage,2))
		else: #Use a new way to calculate damage
			if self.eng_type[0]==2 or self.eng_type[0]==8: #Turboprop
				itts=[]
				XPLMGetDatavf(self.ITT_ref, itts, 0, self.num_eng)
				if itts[0]>self.m_ITT:
					_diff=itts[0]-self.m_ITT
					self.chtDamage += _diff * 0.25
				if mixes[0]>0.5 and altitude < 1000:
					self.mixtureDamage += 0.25
				self.msg[1]="ITT: "+str(round(itts[0]))+"/"+str(round(self.m_ITT))+" dmg: "+str(round(self.chtDamage,2))
			elif self.eng_type[0]==4 or self.eng_type[0]==5: #Jet
				itts=[]
				XPLMGetDatavf(self.ITT_ref, itts, 0, self.num_eng)
				if itts[0]>self.m_ITT:	#IF WE DON'T COOL THIS FIRE DOWN WE'RE NOT GONNA LAST
					_diff=itts[0]-self.m_ITT	#COOL THE ENGINES
					self.chtDamage += _diff * 0.25
				if mixes[0]>0.5 and altitude < 1000:
					self.mixtureDamage += 0.25
				self.msg[1]="ITT: "+str(round(itts[0]))+"/"+str(round(self.m_ITT))+" dmg: "+str(round(self.chtDamage,2))
			else: #Reciprocating or other gets default
				if self.defaultcht>0:
					chts=[]
					XPLMGetDatavf(self.CHT_ref, chts, 0, self.num_eng)
					_diff=abs(chts[0]-self.defaultcht)
					if _diff>0:
						self.chtDamage+=_diff
				self.defaultcht=chts[0]
				if (mixes[0] > 0.95 and altitude > 1000):
					self.mixtureDamage += 1
				self.msg[1]="CHT: "+str(round(chts[0],2))+" dmg: "+str(round(self.chtDamage,2))

		self.msg[0]="Run: "+str(self.runtime)+" RPM: "+str(round(rpms[0]))
		self.msg[2]="Mix: "+str(round(mixes[0],2))+" dmg: "+str(round(self.mixtureDamage,2))
		self.msg[3]="En: "+str(self.eng_type[0])+" Prop: "+str(self.prop_type[0])

		if self.end_flight>0:
			return 5
		else:
			return 1
