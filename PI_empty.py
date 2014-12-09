from XPLMProcessing import *
from XPLMDataAccess import *
from XPLMDisplay import *
from XPLMGraphics import *
from XPLMDefs import *
from XPLMUtilities import *

class PythonInterface:

	def XPluginStart(self):
		self.Name=""
		self.Sig= ""
		self.Desc=""
		self.VERSION="0.0"
		
		self._ref=XPLMFindDataRef("sim/")

		winPosX=20
		winPosY=400
		win_w=230
		win_h=80
		self.msg=[]
		for i in range(0,5):
			self.msg.append("")
		self.ac=""
		self.eng_type=[]
		
		self.gameLoopCB=self.gameLoopCallback
		self.DrawWindowCB=self.DrawWindowCallback
		self.KeyCB=self.KeyCallback
		self.MouseClickCB=self.MouseClickCallback
		self.gWindow=XPLMCreateWindow(self, winPosX, winPosY, winPosX + win_w, winPosY - win_h, 1, self.DrawWindowCB, self.KeyCB, self.MouseClickCB, 0)
		
		self.CmdATConn = XPLMCreateCommand("","")
		self.CmdATConnCB = self.CmdATConnCallback
		XPLMRegisterCommandHandler(self, self.CmdATConn, self.CmdATConnCB, 0, 0)

		return self.Name, self.Sig, self.Desc
		
	def MouseClickCallback(self, inWindowID, x, y, inMouse, inRefcon):
		return 0

	def KeyCallback(self, inWindowID, inKey, inFlags, inVirtualKey, inRefcon, losingFocus):
		pass 

	def CmdATConnCallback(self, cmd, phase, refcon):
		if(phase==0): #KeyDown event

		return 0
	
	def XPluginStop(self):
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
			for i in range(0,5):
				XPLMDrawString(color, left+5, top-(20+15*i), self.msg[i], 0, xplmFont_Basic)

	def gameLoopCallback(self, inElapsedSinceLastCall, elapsedSim, counter, refcon):
		alpha=XPLMGetDataf(self._ref)
		return 1
