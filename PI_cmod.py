from XPLMDataAccess import *
from XPLMDefs import *
from XPLMUtilities import *
from XPLMProcessing import * #Flight loops

class PythonInterface:

	def XPluginStart(self):
		self.Name="Controller Mods"
		self.Sig= "natt.python.cmod"
		self.Desc="Command modifications for using controllers"
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
		self.sbrake_ref=XPLMFindDataRef("sim/cockpit2/controls/speedbrake_ratio
		self.flap_ref=XPLMFindDataRef("sim/cockpit2/controls/flap_ratio
		
		#self._ref=XPLMFindDataRef("sim/joystick/
		self.axis_assign_ref=XPLMFindDataRef("sim/joystick/joystick_axis_assignments")	# int[100] - prop=7
		self.axis_values_ref=XPLMFindDataRef("sim/joystick/joystick_axis_values")
		self.axis_min_ref=XPLMFindDataRef("sim/joystick/joystick_axis_minimum")
		self.axis_max_ref=XPLMFindDataRef("sim/joystick/joystick_axis_maximum")
		
		self.cmdhold=0
		self.propbrakes=0
		self.assignments=[]
		self.mins=[]
		self.maxs=[]
		self.propindex=-1

		XPLMGetDatavi(self.axis_assign_ref, self.assignments, 0, 100)
		XPLMGetDatavi(self.axis_min_ref, self.mins, 0, 100)
		XPLMGetDatavi(self.axis_max_ref, self.maxs, 0, 100)
		for i in range(0,100):
			assignment=self.assignments[i]
			if assignment==7: # 7 = prop
				self.propindex=i
				break
		self.propmin=self.mins[i]
		self.propmax=self.maxs[i]
		self.proprange=self.propmax-self.propmin
		
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
		
		# self.CmdRUCConn = XPLMCreateCommand("cmod/custom/right_up_cond","Based on view")
		# self.CmdRUCConnCB = self.CmdRUCConnCallback
		# XPLMRegisterCommandHandler(self, self.CmdRUCConn, self.CmdRUCConnCB, 0, 0)
		
		# self.CmdCConn = XPLMCreateCommand("cmod/custom/right_up_cond","Cockpit view right/up based on airplane")
		# self.CmdCConnCB = self.CmdCConnCallback
		# XPLMRegisterCommandHandler(self, self.CmdCConn, self.CmdCConnCB, 0, 0)
		
		self.CmdVDConn = XPLMCreateCommand("cmod/custom/view_down_cond","Cockpit view down based on airplane")
		self.CmdVDConnCB = self.CmdVDConnCallback
		XPLMRegisterCommandHandler(self, self.CmdVDConn, self.CmdVDConnCB, 0, 0)
		
		self.CmdVUConn = XPLMCreateCommand("cmod/custom/view_up_cond","Cockpit view up based on airplane")
		self.CmdVUConnCB = self.CmdVUConnCallback
		XPLMRegisterCommandHandler(self, self.CmdVUConn, self.CmdVUConnCB, 0, 0)
		
		self.CmdVLConn = XPLMCreateCommand("cmod/custom/view_left_cond","Cockpit view left based on airplane")
		self.CmdVLConnCB = self.CmdVLConnCallback
		XPLMRegisterCommandHandler(self, self.CmdVLConn, self.CmdVLConnCB, 0, 0)
		
		self.CmdVRConn = XPLMCreateCommand("cmod/custom/view_right_cond","Cockpit view right based on airplane")
		self.CmdVRConnCB = self.CmdVRConnCallback
		XPLMRegisterCommandHandler(self, self.CmdVRConn, self.CmdVRConnCB, 0, 0)
		
		self.CmdCPConn = XPLMCreateCommand("cmod/custom/view_cockpit_cond","Cockpit front view based on airplane")
		self.CmdCPConnCB = self.CmdCPConnCallback
		XPLMRegisterCommandHandler(self, self.CmdCPConn, self.CmdCPConnCB, 0, 0)
		
		self.CmdMBConn = XPLMCreateCommand("cmod/custom/prop_speedbrakes","Use prop axis for speed brakes")
		self.CmdMBConnCB = self.CmdMBConnCallback
		XPLMRegisterCommandHandler(self, self.CmdMBConn, self.CmdMBConnCB, 0, 0)
		
		self.gameLoopCB=self.gameLoopCallback

		return self.Name, self.Sig, self.Desc
		
	def CmdSTConnCallback(self, cmd, phase, refcon): #Toggle speedbrakes
		if(phase==0): #KeyDown event
			position=XPLMGetDataf(self.speed_brake_ref)
			if position<1: #armed, stowed, or not fully deployed
				XPLMSetDataf(self.speed_brake_ref, 1.0) #Deploy
			else: #fully deployed
				XPLMSetDataf(self.speed_brake_ref, -0.5) #Armed
		return 0
	
	def CmdLTConnCallback(self, cmd, phase, refcon): #Toggle landing gear and lights together
		if(phase==0): #KeyDown event
			gear=XPLMGetDatai(self.gearhand_ref)
			light=XPLMGetDatai(self.landing_lights_ref)
			print "CMOD - gear = "+str(gear)+"  light = "+str(light)
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
			# ac=self.getshortac(self.acf_desc_ref)
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

	def CmdVDConnCallback(self, cmd, phase, refcon): #Cockpit view down based on airplane
		#if(phase==0): #KeyDown event
		self.cmdif3D("sim/general/down_fast","sim/view/pan_down_fast")
		return 0
	def CmdVUConnCallback(self, cmd, phase, refcon): #Cockpit view up based on airplane
		#if(phase==0): #KeyDown event
		self.cmdif3D("sim/general/up_fast","sim/view/pan_up_fast")
		return 0
	def CmdVLConnCallback(self, cmd, phase, refcon): #Cockpit view left based on airplane
		#if(phase==0): #KeyDown event
		self.cmdif3D("sim/general/left_fast","sim/view/pan_left_fast")
		return 0
	def CmdVRConnCallback(self, cmd, phase, refcon): #Cockpit view right based on airplane
		#if(phase==0): #KeyDown event
		self.cmdif3D("sim/general/right_fast","sim/view/pan_right_fast")
		return 0
	
	def CmdCPConnCallback(self, cmd, phase, refcon): #Cockpit view based on airplane
		if(phase==0): #KeyDown event
			self.cmdif3D("sim/view/3d_cockpit_cmnd_look","sim/view/forward_with_panel")
		return 0
	
	def CmdMBConnCallback(self, cmd, phase, refcon): #propture for speed brakes
		if(phase==0) and self.propindex>-1:
			if self.propbrakes==0:
				self.propbrakes=1
				XPLMRegisterFlightLoopCallback(self, self.gameLoopCB, 0.1, 0)
			else:
				self.propbrakes=0
				XPLMUnregisterFlightLoopCallback(self, self.gameLoopCB, 0)
		return 0
	
	def cmdif3D(self, cmd3D, cmd2D): #Run command depending on 3D cockpit
		ac,has3D=self.getshortac(self.acf_desc_ref)
		#print "CMOD - AC "+ac+" has3D = "+str(has3D)
		if has3D==1: #view 3D
			view_cmd=XPLMFindCommand(cmd3D)
		else: #view 2D
			view_cmd=XPLMFindCommand(cmd2D)
		if view_cmd is not None:
			XPLMCommandOnce(view_cmd)
		else:
			print "XDMG = Couldn't find either '"+cmd3D+"' or '"+cmd2D
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
			if phase==0:
				apset=XPLMGetDataf(apset_ref)
				XPLMSetDataf(apset_ref, apset+ap_del)
			elif phase==1:
				if self.cmdhold>10 and self.cmdhold%5==0:
					apset=XPLMGetDataf(apset_ref)
					XPLMSetDataf(apset_ref, apset+ap_del)
				self.cmdhold+=1
			elif phase==2:
				self.cmdhold=0
		elif ap!=2:
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
			if trim_cmd is not None:
				if phase==0:
					XPLMCommandBegin(trim_cmd)
				elif phase==2:
					XPLMCommandEnd(trim_cmd)
			#trim=XPLMGetDataf(trim_ref)
			#XPLMSetDataf(trim_ref, trim+trim_del)
	
	def gameLoopCallback(self, inElapsedSinceLastCall, elapsedSim, counter, refcon):
		#Get current conditions
		vals=[]
		XPLMGetDatavi(self.axis_values_ref, vals, self.propindex, 1)
		propaxis=vals[0]
		proper=(propaxis-self.propmin)/self.proprange
		if proper<.001:
			proper=-0.5
		XPLMSetDataf(self.sbrake_ref,proper)
		return 0.1
	
	def nextflaps(self,handle,flaps):
		i=0
		while handle<flaps[i]+0.001:
			i+=1
		XPLMSetDataf(self.flap_h_pos_ref, flaps[i])
	
	def getshortac(self,acf_desc_ref):
		acf_descb=[]
		XPLMGetDatab(acf_desc_ref, acf_descb, 0, 500)
		acf_desc=str(acf_descb)
		if acf_desc[0:27]=="['Boeing 737-800 xversion 4":
			AC="B738"
			has3D=1
		elif acf_desc=="['Pilatus PC-12']":
			AC="PC12"
			has3D=1
		elif acf_desc[0:9]=="['BE1900D" or acf_desc[0:19]=="['B1900 for X-plane":
			AC="B190"
			has3D=1
		elif acf_desc=="['Bombardier Challenger 300']":
			AC="CL30"
			has3D=1
		elif acf_desc[0:21]=="['C208B Grand Caravan":
			AC="C208"
			has3D=1
		else:
			AC=acf_desc
			has3D=0
			print str(acf_desc)
		return AC, has3D
	
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
		XPLMUnregisterCommandHandler(self, self.CmdVDConn, self.CmdVDConnCallback, 0, 0)
		XPLMUnregisterCommandHandler(self, self.CmdVUConn, self.CmdVUConnCallback, 0, 0)
		XPLMUnregisterCommandHandler(self, self.CmdVLConn, self.CmdVLConnCallback, 0, 0)
		XPLMUnregisterCommandHandler(self, self.CmdVRConn, self.CmdVRConnCallback, 0, 0)
		XPLMUnregisterCommandHandler(self, self.CmdCPConn, self.CmdCPConnCallback, 0, 0)
		XPLMUnregisterCommandHandler(self, self.CmdMBConn, self.CmdMBConnCallback, 0, 0)
		pass

	def XPluginEnable(self):
		return 1

	def XPluginDisable(self):
		pass

	def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
		pass
