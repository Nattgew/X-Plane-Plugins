from XPLMProcessing import * #Flight loops
from XPLMDataAccess import * #Datarefs
from XPLMDisplay import * #Draw window
from XPLMGraphics import * #Draw things
from XPLMDefs import * #Object definitions
from XPLMUtilities import * #Commands

class PythonInterface:

	def XPluginStart(self):
		self.Name="Efficiency Display"
		self.Sig= "natt.perfdisp"
		self.Desc="Displays efficiency info"
		self.VERSION="0.0"
		
		self.FF_ref=XPLMFindDataRef("sim/flightmodel/engine/ENGN_FF_")
		self.TH_ref=XPLMFindDataRef("sim/flightmodel/engine/POINT_thrust")
		self.PWR_ref=XPLMFindDataRef("sim/flightmodel/engine/ENGN_power")
		self.TIM_ref=XPLMFindDataRef("sim/time/sim_speed_actual")
		self.Nlb=0.22481 # N to lbf
		winPosX=1000
		winPosY=800
		win_w=230
		win_h=80
		self.msg1=""
		self.msg2=""
		self.started=0
		
		self.gameLoopCB=self.gameLoopCallback
		self.DrawWindowCB=self.DrawWindowCallback
		self.KeyCB=self.KeyCallback
		self.MouseClickCB=self.MouseClickCallback
		self.gWindow=XPLMCreateWindow(self, winPosX, winPosY, winPosX + win_w, winPosY - win_h, 1, self.DrawWindowCB, self.KeyCB, self.MouseClickCB, 0)
		
		self.CmdATConn = XPLMCreateCommand("fsei/flight/efficiency","Show/hide efficiency info")
		self.CmdATConnCB = self.CmdATConnCallback
		XPLMRegisterCommandHandler(self, self.CmdATConn, self.CmdATConnCB, 0, 0)

		return self.Name, self.Sig, self.Desc
		
	def MouseClickCallback(self, inWindowID, x, y, inMouse, inRefcon):
		return 0

	def KeyCallback(self, inWindowID, inKey, inFlags, inVirtualKey, inRefcon, losingFocus):
		pass 

	def CmdATConnCallback(self, cmd, phase, refcon):
		if(phase==0): #KeyDown event
			if self.started==0:
				XPLMRegisterFlightLoopCallback(self, self.gameLoopCB, 0.25, 0)
				self.started=1
			else:
				XPLMUnregisterFlightLoopCallback(self, self.gameLoopCB, 0)
				self.started=0
		return 0
	
	def XPluginStop(self):
		if self.started==1:
			XPLMUnregisterFlightLoopCallback(self, self.gameLoopCB, 0)
			self.started=0
		XPLMUnregisterCommandHandler(self, self.CmdATConn, self.CmdATConnCB, 0, 0)
		XPLMDestroyWindow(self, self.gWindow)
		pass

	def XPluginEnable(self):
		return 1

	def XPluginDisable(self):
		pass

	def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
		pass
		
	def DrawWindowCallback(self, inWindowID, inRefcon):
		if self.started==1:
			lLeft=[];	lTop=[]; lRight=[];	lBottom=[]
			XPLMGetWindowGeometry(inWindowID, lLeft, lTop, lRight, lBottom)
			left=int(lLeft[0]); top=int(lTop[0]); right=int(lRight[0]); bottom=int(lBottom[0])
			XPLMDrawTranslucentDarkBox(left,top,right,bottom)
			color=1.0, 1.0, 1.0
			XPLMDrawString(color, left+5, top-(20), self.msg1, 0, xplmFont_Basic)
			XPLMDrawString(color, left+5, top-(20+15), self.msg2, 0, xplmFont_Basic)

	def gameLoopCallback(self, inElapsedSinceLastCall, elapsedSim, counter, refcon):
		FF=[]
		TH=[]
		PWR=[]
		XPLMGetDatavf(self.FF_ref, FF, 0, 1)
		XPLMGetDatavf(self.TH_ref, TH, 0, 1)
		XPLMGetDatavf(self.PWR_ref, PWR, 0, 1)
		warp=XPLMGetDataf(self.TIM_ref)
		tsfc=3600*FF[0]/(TH[0]/self.Nlb)
		bsfc=3600*FF[0]/(PWR[0])
		self.msg1="Time: "+str(round(warp,1))
		self.msg2="T: "+str(round(tsfc,2))+"  B: "+str(round(bsfc,2))
		return 0.25
