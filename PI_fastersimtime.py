from XPLMProcessing import * #Flight loops
from XPLMDataAccess import * #Datarefs
from XPLMDisplay import * #Draw window
from XPLMGraphics import * #Draw things
from XPLMDefs import * #Object definitions
from XPLMUtilities import * #Commands

class PythonInterface:

	def XPluginStart(self):
		self.Name="Faster Sim Time"
		self.Sig= "natt.fastsimtime"
		self.Desc="Increses the sim time faster than default"
		self.VERSION="0.1"
		
		self.timeactual_ref=XPLMFindDataRef("sim/time/sim_speed_actual")
		self.timerequest_ref=XPLMFindDataRef("sim/time/sim_speed")
		winPosX=800
		winPosY=1000
		win_w=100
		win_h=30
		self.msg1=""
		self.simtime=1
		
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
			if self.simtime>1:
				self.simtime=1
				XPLMUnregisterFlightLoopCallback(self, self.gameLoopCB, 0)
			else:
				self.simtime=32
				XPLMRegisterFlightLoopCallback(self, self.gameLoopCB, 0.25, 0)
			XPLMSetDatai(self.timerequest_ref, self.simtime)
		return 0
	
	def XPluginStop(self):
		if self.simtime>1:
			XPLMUnregisterFlightLoopCallback(self, self.gameLoopCB, 0)
			self.simtime=1
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
		if self.simtime>1:
			lLeft=[];	lTop=[]; lRight=[];	lBottom=[]
			XPLMGetWindowGeometry(inWindowID, lLeft, lTop, lRight, lBottom)
			left=int(lLeft[0]); top=int(lTop[0]); right=int(lRight[0]); bottom=int(lBottom[0])
			XPLMDrawTranslucentDarkBox(left,top,right,bottom)
			color=1.0, 1.0, 1.0
			XPLMDrawString(color, left+5, top-(20), self.msg, 0, xplmFont_Basic)

	def gameLoopCallback(self, inElapsedSinceLastCall, elapsedSim, counter, refcon):
		warp=XPLMGetDataf(self.timeactual_ref)
		self.msg="Warp: "+str(round(warp,1))
		return 0.1
