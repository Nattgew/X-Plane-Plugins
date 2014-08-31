from XPLMProcessing import *
from XPLMDataAccess import *
from XPLMDisplay import *
from XPLMGraphics import *
from XPLMUtilities import *
from XPLMDefs import *

class PythonInterface:

	def getSign(self, val):
		sign=""
		if val>0:
			sign="+"
		return sign
	
	def setBaro(self, bar_new):
		alt_old=XPLMGetDataf(self.alt_ind_ref)
		bar_old=XPLMGetDataf(self.baro_set_ref)
		XPLMSetDataf(self.baro_set_ref, bar_new)
		del_baro_set=bar_new-bar_old
		alt_new=1000.0000238427*bar_new-29480.049077438
		del_alt_ind=alt_new-alt_old
		
		del_baro_str=self.getSign(del_baro_set)+str(round(del_baro_set,2))
		del_alt_str=self.getSign(del_alt_ind)+str(int(round(del_alt_ind)))
		
		print "Altimeter changed to: " + str(round(bar_new,2))
		#print "From "+str(int(round(alt_old)))+" to "+str(int(round(alt_new)))
		self.msg1="Altimeter  " + str(round(bar_new,2))
		self.msg2=del_alt_str+" ft   "+del_baro_str+" inHg"
		self.remainingShowTime=self.showTime
		
		return alt_new

	def XPluginStart(self):
		self.Name="Altimeter Helper 1.2"
		self.Sig= "natt.python.altimeterhelper"
		self.Desc="A plugin that helps with altimeter settings"
		self.VERSION="1.2"
		
		self.baro_set_ref=XPLMFindDataRef("sim/cockpit/misc/barometer_setting")
		self.baro_act_ref=XPLMFindDataRef("sim/weather/barometer_sealevel_inhg")
		#self.flightTimeRef=XPLMFindDataRef("sim/time/total_flight_time_sec")
		self.alt_act_ref=XPLMFindDataRef("sim/flightmodel/position/elevation")
		self.alt_ind_ref=XPLMFindDataRef("sim/cockpit2/gauges/indicators/altitude_ft_pilot")
		self.vvi_ref=XPLMFindDataRef("sim/flightmodel/position/vh_ind_fpm")
		
		self.mft=3.2808399
		self.msg1=""
		self.msg2=""
		self.remainingShowTime=0
		self.showTime=3
		winPosX=20
		winPosY=500
		win_w=170
		win_h=50
		self.last_alt=XPLMGetDataf(self.alt_ind_ref)
		self.trans_alt=18000
		self.last_bar=XPLMGetDataf(self.baro_set_ref)

		self.DrawWindowCB=self.DrawWindowCallback
		self.KeyCB=self.KeyCallback
		self.MouseClickCB=self.MouseClickCallback
		self.gWindow=XPLMCreateWindow(self, winPosX, winPosY, winPosX + win_w, winPosY - win_h, 1, self.DrawWindowCB, self.KeyCB, self.MouseClickCB, 0)
		
		#print "Registering loopback"
		self.gameLoopCB=self.gameLoopCallback
		XPLMRegisterFlightLoopCallback(self, self.gameLoopCB, 1, 0)
		
		self.CmdSHConn = XPLMCreateCommand("althelp/tools/set_altimeter","Sets altimeter for current position and altitude")
		self.CmdSHConnCB  = self.CmdSHConnCallback
		XPLMRegisterCommandHandler(self, self.CmdSHConn,  self.CmdSHConnCB, 0, 0)
		
		return self.Name, self.Sig, self.Desc

	def MouseClickCallback(self, inWindowID, x, y, inMouse, inRefcon):
		return 0

	def KeyCallback(self, inWindowID, inKey, inFlags, inVirtualKey, inRefcon, losingFocus):
		pass 

	def CmdSHConnCallback(self, cmd, phase, refcon):
		if(phase==0): #KeyDown event
			print "AltHelper = CMD set altimeter"
			if XPLMGetDataf(self.alt_ind_ref) > self.trans_alt:
				newbaro=29.92
			else:
				newbaro=XPLMGetDataf(self.baro_act_ref)
			self.last_bar=newbaro
			alt=self.setBaro(newbaro)
		return 0

	def DrawWindowCallback(self, inWindowID, inRefcon):
		if self.remainingShowTime > 0:
			lLeft=[];	lTop=[];	lRight=[];	lBottom=[]
			XPLMGetWindowGeometry(inWindowID, lLeft, lTop, lRight, lBottom)
			left=int(lLeft[0]); top=int(lTop[0]); right=int(lRight[0]); bottom=int(lBottom[0])
			XPLMDrawTranslucentDarkBox(left,top,right,bottom)
			color=1.0, 1.0, 1.0
			gResult=XPLMDrawString(color, left+5, top-20, self.msg1, 0, xplmFont_Basic)
			gResult2=XPLMDrawString(color, left+5, top-35, self.msg2, 0, xplmFont_Basic)

	def XPluginStop(self):
		XPLMUnregisterCommandHandler(self, self.CmdSHConn, self.CmdSHConnCB, 0)
		XPLMUnregisterFlightLoopCallback(self, self.gameLoopCB, 0);
		XPLMDestroyWindow(self, self.gWindow)
		pass

	def XPluginEnable(self):
		return 1

	def XPluginDisable(self):
		pass

	def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
		pass

	def gameLoopCallback(self, inElapsedSinceLastCall, elapsedSim, counter, refcon):
	
		if 0.0 < self.remainingShowTime:
			self.remainingShowTime -= inElapsedSinceLastCall
	
		alt=XPLMGetDataf(self.alt_ind_ref)
		vvi=XPLMGetDataf(self.vvi_ref)
		alt_act=XPLMGetDataf(self.alt_act_ref)*self.mft
		bar=XPLMGetDataf(self.baro_set_ref)
		
		if alt >= self.trans_alt and self.last_alt < self.trans_alt:
			# Climbing through 18000
			print "Climbing through transition alt"
			if vvi >= 500 or (vvi < 500 and alt > self.trans_alt + 250):
				alt=self.setBaro(29.92)
		elif alt < self.trans_alt and self.last_alt >= self.trans_alt:
			# Descending through 18000
			print "Descending through transition alt"
			if vvi <= -500 or (vvi > -500 and alt < self.trans_alt - 250):
				alt=self.setBaro(XPLMGetDataf(self.baro_act_ref))
		
		alt_err=alt-alt_act
		if abs(alt_err)>250:
			alt_err_str=self.getSign(alt_err)+str(round(alt_err))
			self.msg1="Update altimeter setting!"
			self.msg2="Indicated off by "+alt_err_str+" feet!"
			self.remainingShowTime=self.showTime
			
		if round(self.last_bar,2)!=round(bar,2):
			#print "Setting changed from "+str(round(self.last_bar,2))+" to "+str(round(bar,2))
			alt=self.setBaro(bar)

		self.last_alt=alt
		self.last_bar=bar
		#print str(alt)+"  "+str(bar)

		return 0.1
		
