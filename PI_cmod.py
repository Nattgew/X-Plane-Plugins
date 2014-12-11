from XPLMDataAccess import *
from XPLMDefs import *
from XPLMUtilities import *

class PythonInterface:

	def XPluginStart(self):
		self.Name="Controller Mods"
		self.Sig= "natt.python.cmod"
		self.Desc="Modifications for using controllers"
		self.VERSION="0.1"
		
		self.acf_desc_ref=XPLMFindDataRef("sim/aircraft/view/acf_descrip") #string array
		self.speed_brake_ref=XPLMFindDataRef("sim/flightmodel/controls/sbrkrqst") #float -0.5=armed 0=off 1=max
		self.landing_lights_ref=XPLMFindDataRef("sim/cockpit/electrical/landing_lights_on") #int
		self.geardep_ref=XPLMFindDataRef("sim/aircraft/parts/acf_gear_deploy") #float array
		self.gearhand_ref=XPLMFindDataRef("sim/cockpit/switches/gear_handle_status") #int
		self.flap_h_pos_ref=XPLMFindDataRef("sim/cockpit2/controls/flap_ratio") #float handle position 0->1
		self.ap_vvi_ref=XPLMFindDataRef("sim/cockpit/autopilot/vertical_velocity") #float fpm
		self.ap_hdg_ref=XPLMFindDataRef("sim/cockpit/autopilot/heading_mag") #float degm
		self.ap_ref=XPLMFindDataRef("sim/cockpit/autopilot/autopilot_mode") #int 0=off 1=FD 2=ON
		self.trim_ail_ref=XPLMFindDataRef("sim/flightmodel/controls/ail_trim") #float -1=left ... 1=right
		self.trim_elv_ref=XPLMFindDataRef("sim/flightmodel/controls/elv_trim") #float -1=down ... 1=up
		self.view_ref=XPLMFindDataRef("sim/graphics/view/view_type") #int see docs
		
		self.CmdSTConn = XPLMCreateCommand("cmod/toggle/speedbrake","Toggles speed brakes")
		self.CmdSTConnCB = self.CmdSTConnCallback
		XPLMRegisterCommandHandler(self, self.CmdSTConn, self.CmdSTConnCB, 0, 0)
		
		self.CmdLTConn = XPLMCreateCommand("cmod/toggle/landinggearlights","Toggles landing gear and lights")
		self.CmdLTConnCB = self.CmdLTConnCallback
		XPLMRegisterCommandHandler(self, self.CmdLTConn, self.CmdLTConnCB, 0, 0)
		
		self.CmdFTConn = XPLMCreateCommand("cmod/toggle/flaps","Toggles through flaps settings")
		self.CmdFTConnCB = self.CmdFTConnCallback
		XPLMRegisterCommandHandler(self, self.CmdFTConn, self.CmdFTConnCB, 0, 0)
		
		self.CmdVSupConn = XPLMCreateCommand("cmod/custom/vspeed_up","AP vertical speed set +100 fpm")
		self.CmdVSupConnCB = self.CmdVSupConnCallback
		XPLMRegisterCommandHandler(self, self.CmdVSupConn, self.CmdVSupConnCB, 0, 0)
		
		self.CmdVSdnConn = XPLMCreateCommand("cmod/custom/vspeed_down","AP vertical speed set -100 fpm")
		self.CmdVSdnConnCB = self.CmdVSdnConnCallback
		XPLMRegisterCommandHandler(self, self.CmdVSdnConn, self.CmdVSdnConnCB, 0, 0)
		
		self.CmdLCConn = XPLMCreateCommand("cmod/custom/left_cond","If AP: HDG left 1 degree, else: Aileron trim left")
		self.CmdLCConnCB = self.CmdLCConnCallback
		XPLMRegisterCommandHandler(self, self.CmdLCConn, self.CmdLCConnCB, 0, 0)
		
		self.CmdRCConn = XPLMCreateCommand("cmod/custom/right_cond","If AP: HDG right 1 degree, else: Aileron trim right")
		self.CmdRCConnCB = self.CmdRCConnCallback
		XPLMRegisterCommandHandler(self, self.CmdRCConn, self.CmdRCConnCB, 0, 0)
		
		self.CmdUCConn = XPLMCreateCommand("cmod/custom/up_cond","If AP: VS +100 fpm, else: Elevator trim up")
		self.CmdUCConnCB = self.CmdUCConnCallback
		XPLMRegisterCommandHandler(self, self.CmdUCConn, self.CmdUCConnCB, 0, 0)
		
		self.CmdDCConn = XPLMCreateCommand("cmod/custom/down_cond","If AP: VS -100fpm, else: Elevator trim down")
		self.CmdDCConnCB = self.CmdDCConnCallback
		XPLMRegisterCommandHandler(self, self.CmdDCConn, self.CmdDCConnCB, 0, 0)
		
		self.CmdRUCConn = XPLMCreateCommand("cmod/custom/right_up_cond","If 3D/ ")
		self.CmdRUCConnCB = self.CmdRUCConnCallback
		XPLMRegisterCommandHandler(self, self.CmdRUCConn, self.CmdRUCConnCB, 0, 0)

		return self.Name, self.Sig, self.Desc
		
	def CmdSTConnCallback(self, cmd, phase, refcon): #Toggle speedbrakes
		if(phase==0): #KeyDown event
			position=XPLMGetDataf(self.speed_brake_ref)
			if position<1: #armed, stowed, or not fully deployed
				XPLMSetDataf(self.speed_brake_ref, 1.0)
			else: #fully deployed
				XPLMSetDataf(self.speed_brake_ref, 0.0)
		return 0
	
	def CmdLTConnCallback(self, cmd, phase, refcon): #Toggle landing gear and lights together
		if(phase==0): #KeyDown event
			gear=XPLMGetDatai(self.gearhand_ref)
			light=XPLMGetDatai(self.landing_lights_ref)
			if gear==0 or light==0: #Gear handle up->down, may need second go at landing light
				XPLMSetDatai(self.gearhand_ref, 1)
				XPLMSetDatai(self.landing_lights_ref, 1)
			else: #Gear handle down->up
				XPLMSetDatai(self.landing_lights_ref, 0)
				XPLMSetDatai(self.gearhand_ref, 0)
		return 0
	
	def CmdFTConnCallback(self, cmd, phase, refcon): #Flaps +1, retract if fully deployed
		if(phase==0): #KeyDown event
			handle=XPLMGetDataf(self.flap_h_pos_ref)
			if handle==1: #Fully deployed
				XPLMSetDataf(self.flap_h_pos_ref, 0.0) #Retract full
			else:
				flap_down_cmd=XPLMFindCommand("sim/flight_controls/flaps_down")
				if flap_down_cmd is not None:
					print "XDMG = Found command, flaps down"
					XPLMCommandOnce(flap_down_cmd)
			# acf_descb=[]
			# XPLMGetDatab(self.acf_desc_ref, acf_descb, 0, 500)
			# self.ac=self.getshortac(str(acf_descb))
			# handle=XPLMGetDataf(self.flap_h_pos_ref)
			# if handle==1: #Fully deployed
				# XPLMSetDataf(self.flap_h_pos_ref, 0.0) #Retract full
			# else: #Set next detent
				# if ac=="PC12":
					# flaps=(0.3,0.7,1.0) #15 30 40
					# self.nextflaps(handle, flaps)
				# elif ac=="B738":
					# flaps=(0.125,0.375,0.625,0.875,1.0) #1 5 15 30 40
					# self.nextflaps(handle, flaps)
				# else: #Fully deploy
					# XPLMSetDataf(self.flap_h_pos_ref, 1.0)
		return 0
	
	def CmdVSupConnCallback(self, cmd, phase, refcon): #AP vertical speed +100 fpm
		if(phase==0): #KeyDown event
			vvi=XPLMGetDataf(self.ap_vvi_ref)
			XPLMSetDataf(self.ap_vvi_ref, vvi+100)
		return 0
	
	def CmdVSdnConnCallback(self, cmd, phase, refcon): #AP vertical speed -100 fpm
		if(phase==0): #KeyDown event
			vvi=XPLMGetDataf(self.ap_vvi_ref)
			XPLMSetDataf(self.ap_vvi_ref, vvi-100)
		return 0
	
	def CmdLCConnCallback(self, cmd, phase, refcon): #Left hdg or aileron trim
		#if(phase==0): #KeyDown event
		self.CondSet(self.ap_hdg_ref, self.trim_ail_ref, -1, -0.01, phase)
		return 0
	
	def CmdRCConnCallback(self, cmd, phase, refcon): #Right hdg or aileron trim
		#if(phase==0): #KeyDown event
		self.CondSet(self.ap_hdg_ref, self.trim_ail_ref, 1, 0.01, phase)
		return 0
	
	def CmdDCConnCallback(self, cmd, phase, refcon): #Down vert speed or elev trim
		#if(phase==0): #KeyDown event
		self.CondSet(self.ap_vvi_ref, self.trim_elv_ref, -100, -0.01, phase)
		return 0
	
	def CmdUCConnCallback(self, cmd, phase, refcon): #Up vert speed or elev trim
		#if(phase==0): #KeyDown event
		self.CondSet(self.ap_vvi_ref, self.trim_elv_ref, 100, 0.01, phase)
		return 0
	
		# self.view_ref
		# 1000 Forwards
		# 1001 Down 4 Degrees*
		# 1002 Down 8 Degrees*
		# 1004 Left 45 Degrees
		# 1005 Right 45 Degrees
		# 1006 Left 90 Degrees
		# 1007 Right 90 Degrees
		# 1008 Left 135 Degrees
		# 1009 Right 135 Degrees
		# 1010 Backward
		# 1011 Left and up
		# 1012 Right and up
		# 1014 Airport Beacon Tower
		# 1015 On Runway
		# 1017 Chase
		# 1018 Follow
		# 1019 Follow with Panel
		# 1020 Spot
		# 1021 Spot Moving
		# 1023 Full screen with HUD
		# 1024 Full screen no HUD
		# 1025 Straight Down+
		# 1026 3D Cockpit+
	
	def CondSet(self, apset_ref, trim_ref, ap_del, trim_del, phase): #Set AP ref+del if AP on, else set trim ref+del
		ap=XPLMGetDatai(self.ap_ref)
		if ap==2:
			apset=XPLMGetDataf(apset_ref)
			XPLMSetDataf(apset_ref, apset+ap_del)
		else:
			if trim_ref==self.trim_elv_ref:
				if trim_del>0:
					trim_cmd=XPLMFindCommand("sim/flight_controls/pitch_trim_up")
				else:
					trim_cmd=XPLMFindCommand("sim/flight_controls/pitch_trim_down")
			elif trim_ref==self.trim_ail_ref:
				if trim_del>0:
					trim_cmd=XPLMFindCommand("sim/flight_controls/aileron_trim_right")
				else:
					trim_cmd=XPLMFindCommand("sim/flight_controls/aileron_trim_left")
			if phase==0:
				XPLMCommandBegin(trim_cmd)
			elif phase==2:
				XPLMCommandEnd(trim_cmd)
			#trim=XPLMGetDataf(trim_ref)
			#XPLMSetDataf(trim_ref, trim+trim_del)
	
	def nextflaps(self,handle,flaps):
		i=0
		while handle<flaps[i]+0.001:
			i+=1
		XPLMSetDataf(self.flap_h_pos_ref, flaps[i])
	
	def getshortac(self,acf_desc):
		if acf_desc[0:27]=="['Boeing 737-800 xversion 4":
			AC="B738"
		elif acf_desc=="['Pilatus PC-12']":
			AC="PC12"
		elif acf_desc[0:9]=="['BE1900D":
			AC="B190"
		elif acf_desc=="['Bombardier Challenger 300']":
			AC="CL30"
		elif acf_desc[0:21]=="['C208B Grand Caravan":
			AC="C208"
		else:
			AC=acf_desc
			print str(acf_desc)
		return ac_short
	
	def XPluginStop(self):
		XPLMUnregisterCommandHandler(self, self.CmdSTConn, self.CmdSTConnCB, 0, 0)
		XPLMUnregisterCommandHandler(self, self.CmdLTConn, self.CmdLTConnCB, 0, 0)
		XPLMUnregisterCommandHandler(self, self.CmdFTConn, self.CmdFTConnCB, 0, 0)
		XPLMUnregisterCommandHandler(self, self.CmdVSupConn, self.CmdVSupConnCB, 0, 0)
		XPLMUnregisterCommandHandler(self, self.CmdVSdnConn, self.CmdVSdnConnCB, 0, 0)
		XPLMUnregisterCommandHandler(self, self.CmdLCConn, self.CmdLCConnCB, 0, 0)
		XPLMUnregisterCommandHandler(self, self.CmdRCConn, self.CmdRCConnCB, 0, 0)
		XPLMUnregisterCommandHandler(self, self.CmdUCConn, self.CmdUCConnCB, 0, 0)
		XPLMUnregisterCommandHandler(self, self.CmdDCConn, self.CmdDCConnCB, 0, 0)
		pass

	def XPluginEnable(self):
		return 1

	def XPluginDisable(self):
		pass

	def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
		pass
