from XPLMProcessing import * #Flight loops
from XPLMDataAccess import * #Datarefs
from XPLMDisplay import * #Draw window
from XPLMGraphics import * #Draw things
from XPLMDefs import * #Object definitions
from XPLMUtilities import * #Commands

class PythonInterface:

	def XPluginStart(self):
		self.Name=""
		self.Sig= ""
		self.Desc=""
		self.VERSION="0.0"
		
		self.gpsfail_ref=XPLMFindDataRef("sim/operation/failures/rel_gps")
		self.gpsfail2_ref=XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_gps2")
		self.gps430fail_ref=XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_g430_gps1")
		self.gps430fail2_ref=XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_g430_gps2")

		failed=0
		winPosX=20
		winPosY=400
		win_w=230
		win_h=80
		self.msg=""
		
		self.DrawWindowCB=self.DrawWindowCallback
		self.KeyCB=self.KeyCallback
		self.MouseClickCB=self.MouseClickCallback
		self.gWindow=XPLMCreateWindow(self, winPosX, winPosY, winPosX + win_w, winPosY - win_h, 1, self.DrawWindowCB, self.KeyCB, self.MouseClickCB, 0)
		
		self.CmdVFRConn = XPLMCreateCommand("special/flight/fail_gps","Toggles GPS failure")
		self.CmdVFRConnCB = self.CmdVFRConnCallback
		XPLMRegisterCommandHandler(self, self.CmdVFRConn, self.CmdVFRConnCB, 0, 0)

		return self.Name, self.Sig, self.Desc
		
	def MouseClickCallback(self, inWindowID, x, y, inMouse, inRefcon):
		return 0

	def KeyCallback(self, inWindowID, inKey, inFlags, inVirtualKey, inRefcon, losingFocus):
		pass 

	def CmdVFRConnCallback(self, cmd, phase, refcon):
		if(phase==0): #KeyDown event
			failed=not failed
			XPLMSetDatai(self.gpsfail_ref,failed)
			XPLMSetDatai(self.gpsfail2_ref,failed)
			XPLMSetDatai(self.gps430fail_ref,failed)
			XPLMSetDatai(self.gps430fail2_ref,failed)
		return 0
	
	def XPluginStop(self):
		XPLMUnregisterCommandHandler(self, self.CmdVFRConn, self.CmdVFRConnCB, 0, 0)
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
			XPLMDrawString(color, left+5, top-(20), self.msg, 0, xplmFont_Basic)
