from XPLMProcessing import *
from XPLMDataAccess import *
from XPLMDisplay import *
from XPLMGraphics import *
from XPLMUtilities import *
from XPLMDefs import *

class PythonInterface:

	def getSign(self, val): #Puts a plus sign in front of positive values
		sign=""
		if val>0:
			sign="+"
		return sign
	
	def getAlt(self, SL, AM): #Determines altitude based on pressure delta
		alt=1000*(SL-AM)
		return alt
	
	def setBaro(self, bar_new): #Set the barometer
		bar_old=XPLMGetDataf(self.baro_set_ref)
		XPLMSetDataf(self.baro_set_ref, bar_new)
		del_baro_set=bar_new-bar_old
		del_baro_str=self.getSign(del_baro_set)+str(round(del_baro_set,2))
		#print "Altimeter changed to: " + str(round(bar_new,2))
		self.msg1="Altimeter  " + str(round(bar_new,2))+"  "+del_baro_str+" inHg"
		self.remainingShowTime=self.showTime
		
		pass
	
	def showBaro(self, bar_new): #Show the barometer setting
		self.msg1="Altimeter  " + str(round(bar_new,2))
		self.remainingShowTime=self.showTime
		pass

	def XPluginStart(self):
		self.Name="Altimeter Helper 1.2"
		self.Sig= "natt.python.altimeterhelper"
		self.Desc="A plugin that helps with altimeter settings"
		self.VERSION="1.2"
		
		self.baro_set_ref=XPLMFindDataRef("sim/cockpit/misc/barometer_setting")
		self.baro_act_ref=XPLMFindDataRef("sim/weather/barometer_sealevel_inhg")
		self.baro_am_ref=XPLMFindDataRef("sim/weather/barometer_current_inhg")
		self.alt_act_ref=XPLMFindDataRef("sim/flightmodel/position/elevation")
		self.alt_ind_ref=XPLMFindDataRef("sim/flightmodel/misc/h_ind")
		self.vvi_ref=XPLMFindDataRef("sim/flightmodel/position/vh_ind_fpm")
		
		self.mft=3.2808399 #m -> ft
		self.msg1=""
		self.remainingShowTime=0
		self.showTime=3 #Seconds to show the altimeter setting when changed
		winPosX=20
		winPosY=500
		win_w=200
		win_h=35
		self.stdpress=0 #Whether standard pressure is set
		self.trans_alt=18000
		self.tol=[17.009, 0.0058579, -0.000000012525] #Parameters for altimeter tolerance
		self.last_bar=XPLMGetDataf(self.baro_set_ref)

		self.DrawWindowCB=self.DrawWindowCallback
		self.KeyCB=self.KeyCallback
		self.MouseClickCB=self.MouseClickCallback
		self.gWindow=XPLMCreateWindow(self, winPosX, winPosY, winPosX + win_w, winPosY - win_h, 1, self.DrawWindowCB, self.KeyCB, self.MouseClickCB, 0)
		
		self.gameLoopCB=self.gameLoopCallback
		XPLMRegisterFlightLoopCallback(self, self.gameLoopCB, 1, 0)
		
		self.CmdSHConn = XPLMCreateCommand("althelp/set_altimeter","Sets altimeter for current position and altitude")
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
			if round(newbaro,2)!=round(XPLMGetDataf(self.baro_set_ref),2):
				self.last_bar=newbaro
				self.setBaro(newbaro)
			else:
				self.showBaro(newbaro)
		return 0

	def DrawWindowCallback(self, inWindowID, inRefcon):
		if self.remainingShowTime > 0:
			lLeft=[];	lTop=[];	lRight=[];	lBottom=[]
			XPLMGetWindowGeometry(inWindowID, lLeft, lTop, lRight, lBottom)
			left=int(lLeft[0]); top=int(lTop[0]); right=int(lRight[0]); bottom=int(lBottom[0])
			XPLMDrawTranslucentDarkBox(left,top,right,bottom)
			color=1.0, 1.0, 1.0
			gResult=XPLMDrawString(color, left+5, top-20, self.msg1, 0, xplmFont_Basic)

	def XPluginStop(self):
		XPLMUnregisterCommandHandler(self, self.CmdSHConn, self.CmdSHConnCB, 0, 0)
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
		
		alt=XPLMGetDataf(self.alt_ind_ref) #Indicated altitude, ft
		vvi=XPLMGetDataf(self.vvi_ref) #Vertical speed, fpm
		alt_act=XPLMGetDataf(self.alt_act_ref)*self.mft #Real altitude, convert to ft
		bar=XPLMGetDataf(self.baro_set_ref) #Current altimeter setting
		bar_am=XPLMGetDataf(self.baro_am_ref) #Current outside barometric pressure
		bar_act=XPLMGetDataf(self.baro_act_ref) #Current local sea level pressure
		
		if (vvi >= 500 and alt >= (self.trans_alt-25) or vvi < 500 and vvi > 0 and alt > self.trans_alt + 250) and self.stdpress==0: # Climbing through 18000
			bar=29.92
			self.stdpress=1
			self.setBaro(bar)
		elif (vvi <= -500 and alt < (self.trans_alt-25) or vvi > -500 and vvi < 0 and alt < self.trans_alt - 250) and self.stdpress==1: # Descending through 18000
			bar=XPLMGetDataf(self.baro_act_ref)
			self.stdpress=0
			self.setBaro(bar)
		
		alt_err=self.getAlt(bar-bar_act,0)
		alt_err=(alt-alt_act)
		tolerance=self.tol[2]*alt**2+self.tol[1]*alt+self.tol[0] #Determine altimeter error tolerance
		if abs(alt_err)>tolerance and self.stdpress==0:
			alt_err_str=self.getSign(alt_err)+str(round(alt_err))
			self.msg1="Altimeter off by "+alt_err_str+" feet!"
			self.remainingShowTime=self.showTime
		
		if round(self.last_bar,2)!=round(bar,2):
			self.showBaro(bar)

		self.last_bar=bar
		
		return 0.1
