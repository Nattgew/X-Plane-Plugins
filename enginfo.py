from XPLMProcessing import *
from XPLMDataAccess import *
from XPLMDisplay import *
from XPLMGraphics import *
from XPLMDefs import *
from XPLMUtilities import *

class PythonInterface:

	def XPluginStart(self):
		self.Name="Engine Info"
		self.Sig= "natt.python.enginfo"
		self.Desc="Shows engine info"
		self.VERSION="1.0"
		
		self.acf_desc_ref=XPLMFindDataRef("sim/aircraft/view/acf_descrip")
		self.RPM_ref=XPLMFindDataRef("sim/flightmodel/engine/ENGN_N2_")
		self.CHT_ref=XPLMFindDataRef("sim/flightmodel/engine/ENGN_CHT_c")
		self.ITT_ref=XPLMFindDataRef("sim/flightmodel/engine/ENGN_ITT_c")
		self.EGT_ref=XPLMFindDataRef("sim/flightmodel/engine/ENGN_EGT_c")
		self.CHTr_ref=XPLMFindDataRef("sim/flightmodel/engine/ENGN_CHT")
		self.ITTr_ref=XPLMFindDataRef("sim/flightmodel/engine/ENGN_ITT")
		self.EGTr_ref=XPLMFindDataRef("sim/flightmodel/engine/ENGN_EGT")
		self.mix_ref=XPLMFindDataRef("sim/flightmodel/engine/ENGN_mixt")
		self.num_eng_ref=XPLMFindDataRef("sim/aircraft/engine/acf_num_engines")
		self.m_EGT_ref=XPLMFindDataRef("sim/aircraft/engine/acf_max_EGT")
		self.m_ITT_ref=XPLMFindDataRef("sim/aircraft/engine/acf_max_ITT")
		self.m_CHT_ref=XPLMFindDataRef("sim/aircraft/engine/acf_max_CHT")
		self.eng_type_ref=XPLMFindDataRef("sim/aircraft/prop/acf_en_type")
		self.prop_type_ref=XPLMFindDataRef("sim/aircraft/prop/acf_prop_type")
		self.r_EGT_ref=XPLMFindDataRef("sim/aircraft/limits/red_lo_EGT")
		self.rh_EGT_ref=XPLMFindDataRef("sim/aircraft/limits/red_hi_EGT")
		self.y_EGT_ref=XPLMFindDataRef("sim/aircraft/limits/yellow_lo_EGT")
		self.yh_EGT_ref=XPLMFindDataRef("sim/aircraft/limits/yellow_hi_EGT")
		self.g_EGT_ref=XPLMFindDataRef("sim/aircraft/limits/green_lo_EGT")
		self.gh_EGT_ref=XPLMFindDataRef("sim/aircraft/limits/green_hi_EGT")
		self.r_ITT_ref=XPLMFindDataRef("sim/aircraft/limits/red_lo_ITT")
		self.rh_ITT_ref=XPLMFindDataRef("sim/aircraft/limits/red_hi_ITT")
		self.y_ITT_ref=XPLMFindDataRef("sim/aircraft/limits/yellow_lo_ITT")
		self.yh_ITT_ref=XPLMFindDataRef("sim/aircraft/limits/yellow_hi_ITT")
		self.g_ITT_ref=XPLMFindDataRef("sim/aircraft/limits/green_lo_ITT")
		self.gh_ITT_ref=XPLMFindDataRef("sim/aircraft/limits/green_hi_ITT")
		self.r_CHT_ref=XPLMFindDataRef("sim/aircraft/limits/red_lo_CHT")
		self.rh_CHT_ref=XPLMFindDataRef("sim/aircraft/limits/red_hi_CHT")
		self.y_CHT_ref=XPLMFindDataRef("sim/aircraft/limits/yellow_lo_CHT")
		self.yh_CHT_ref=XPLMFindDataRef("sim/aircraft/limits/yellow_hi_CHT")
		self.g_CHT_ref=XPLMFindDataRef("sim/aircraft/limits/green_lo_CHT")
		self.gh_CHT_ref=XPLMFindDataRef("sim/aircraft/limits/green_hi_CHT")
		self.ind_ITT_ref=XPLMFindDataRef("sim/cockpit2/engine/indicators/ITT_deg_C")
		self.ind_EGT_ref=XPLMFindDataRef("sim/cockpit2/engine/indicators/EGT_deg_C")
		self.ind_CHT_ref=XPLMFindDataRef("sim/cockpit2/engine/indicators/CHT_deg_C")

		self.started=0
		self.gWindow=0
		self.msg1=""
		self.msg2=""
		self.msg3=""
		self.msg4=""
		self.msg5=""
		self.msg6=""
		self.winPosX=20
		self.winPosY=400
		self.WINDOW_WIDTH=230
		self.WINDOW_HEIGHT=90
		self.num_eng=0
		self.runtime=0
		self.chtDamage=0
		self.mixtureDamage=0
		self.eng_type=[]
		self.prop_type=[]
		self.acf_desc=[]

		#self.gameLoopCB=self.gameLoopCallback
		self.DrawWindowCB=self.DrawWindowCallback
		self.KeyCB=self.KeyCallback
		self.MouseClickCB=self.MouseClickCallback

		self.CmdSHConn = XPLMCreateCommand("fsei/flight/enginfo","Shows or hides engine info")
		self.CmdSHConnCB  = self.CmdSHConnCallback
		XPLMRegisterCommandHandler(self, self.CmdSHConn,  self.CmdSHConnCB, 0, 0)
		
		return self.Name, self.Sig, self.Desc

	def MouseClickCallback(self, inWindowID, x, y, inMouse, inRefcon):
		return 0

	def KeyCallback(self, inWindowID, inKey, inFlags, inVirtualKey, inRefcon, losingFocus):
		pass 

	def CmdSHConnCallback(self, cmd, phase, refcon):
		if(phase==0): #KeyDown event
			print "XDMG = CMD engine info"
			self.showhide()
		return 0
		
	def showhide(self):
		if self.started == 0:
			print "XDMG = Starting eng info..."
			self.started=1
			self.num_eng=XPLMGetDatai(self.num_eng_ref)
			XPLMGetDatab(self.acf_desc_ref, self.acf_desc, 0, 500)
			self.getInfo()
		else:
			self.started=0
			self.acf_desc=[]
			self.closeEventWindow()
			
	def DrawWindowCallback(self, inWindowID, inRefcon):
		if self.started==1:
			lLeft=[]; lTop=[]; lRight=[]; lBottom=[]
			XPLMGetWindowGeometry(inWindowID, lLeft, lTop, lRight, lBottom)
			left=int(lLeft[0]); top=int(lTop[0]); right=int(lRight[0]); bottom=int(lBottom[0])
			XPLMDrawTranslucentDarkBox(left,top,right,bottom)
			color=1.0, 1.0, 1.0
			XPLMDrawString(color, left+5, top-20, self.msg1, 0, xplmFont_Basic)
			XPLMDrawString(color, left+5, top-35, self.msg2, 0, xplmFont_Basic)
			XPLMDrawString(color, left+5, top-50, self.msg3, 0, xplmFont_Basic)
			XPLMDrawString(color, left+5, top-65, self.msg4, 0, xplmFont_Basic)
			XPLMDrawString(color, left+5, top-80, self.msg5, 0, xplmFont_Basic)
			XPLMDrawString(color, left+5, top-95, self.msg6, 0, xplmFont_Basic)

	def XPluginStop(self):
		XPLMUnegisterCommandHandler(self, self.CmdSHConn, 0)
		self.closeEventWindow()
		pass

	def XPluginEnable(self):
		return 1

	def XPluginDisable(self):
		pass

	def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
		pass

	def createEventWindow(self):
		if self.gWindow == 0:
			print "XDMG = Creating window..."
			self.gWindow=XPLMCreateWindow(self, self.winPosX, self.winPosY, self.winPosX + self.WINDOW_WIDTH, self.winPosY - self.WINDOW_HEIGHT, 1, self.DrawWindowCB, self.KeyCB, self.MouseClickCB, 0)
	
	def closeEventWindow(self):
		if self.gWindow==1:
			print "XDMG = Smashing window..."
			XPLMDestroyWindow(self, self.gWindow)
			self.gWindow = 0

	def getInfo(self):

		prop_type=[]
		eng_type=[]
		rpms=[]
		iITT=[]
		iEGT=[]
		iCHT=[]
		XPLMGetDatavi(self.eng_type_ref, eng_type, 0, self.num_eng)
		XPLMGetDatavi(self.prop_type_ref, prop_type, 0, self.num_eng)
		XPLMGetDatavf(self.RPM_ref, rpms, 0, self.num_eng)
		XPLMGetDatavf(self.ind_ITT_ref, iITT, 0, self.num_eng)
		XPLMGetDatavf(self.ind_EGT_ref, iEGT, 0, self.num_eng)
		XPLMGetDatavf(self.ind_CHT_ref, iCHT, 0, self.num_eng)
		
		if eng_type[0]==2 or eng_type[0]==8: #Turboprop
			itts=[]
			XPLMGetDatavf(self.ITT_ref, itts, 0, self.num_eng)
			ittrs=[]
			XPLMGetDatavf(self.ITTr_ref, ittrs, 0, self.num_eng)
			m_ITT=XPLMGetDataf(self.m_ITT_ref)
			r_ITT=XPLMGetDataf(self.r_ITT_ref)
			rh_ITT=XPLMGetDataf(self.rh_ITT_ref)
			y_ITT=XPLMGetDataf(self.y_ITT_ref)
			yh_ITT=XPLMGetDataf(self.yh_ITT_ref)
			g_ITT=XPLMGetDataf(self.g_ITT_ref)
			gh_ITT=XPLMGetDataf(self.gh_ITT_ref)
			self.msg1="ITT: "+str(round(itts[0]))+"/"+str(round(m_ITT))+" r: "+str(round(ittrs[0]))+"  RPM: "+str(round(rpms[0]))
			self.msg2="R HI: "+str(round(rh_ITT))+"  Y HI: "+str(round(yh_ITT))+"  G HI: "+str(round(gh_ITT))
			self.msg3="R LO: "+str(round(r_ITT))+"  Y LO: "+str(round(y_ITT))+"  G LO: "+str(round(g_ITT))
		elif eng_type[0]==4 or eng_type[0]==5: #Jet
			egts=[]
			XPLMGetDatavf(self.EGT_ref, egts, 0, self.num_eng)
			egtrs=[]
			XPLMGetDatavf(self.EGTr_ref, egtrs, 0, self.num_eng)
			m_EGT=XPLMGetDataf(self.m_EGT_ref)
			r_EGT=XPLMGetDataf(self.r_EGT_ref)
			rh_EGT=XPLMGetDataf(self.rh_EGT_ref)
			y_EGT=XPLMGetDataf(self.y_EGT_ref)
			yh_EGT=XPLMGetDataf(self.yh_EGT_ref)
			g_EGT=XPLMGetDataf(self.g_EGT_ref)
			gh_EGT=XPLMGetDataf(self.gh_EGT_ref)
			self.msg1="EGT: "+str(round(egts[0]))+"/"+str(round(m_EGT))+" r: "+str(round(egtrs[0]))+"  RPM: "+str(round(rpms[0]))
			self.msg2="R HI: "+str(round(rh_EGT))+"  Y HI: "+str(round(yh_EGT))+"  G HI: "+str(round(gh_EGT))
			self.msg3="R LO: "+str(round(r_EGT))+"  Y LO: "+str(round(y_EGT))+"  G LO: "+str(round(g_EGT))
		else: #Reciprocating or other gets default
			chts=[]
			XPLMGetDatavf(self.CHT_ref, chts, 0, self.num_eng)
			chtrs=[]
			XPLMGetDatavf(self.CHTr_ref, chtrs, 0, self.num_eng)
			self.msg1="CHT: "+str(round(chts[0]))+"  RPM: "+str(round(rpms[0]))
			m_CHT=XPLMGetDataf(self.m_CHT_ref)
			r_CHT=XPLMGetDataf(self.r_CHT_ref)
			rh_CHT=XPLMGetDataf(self.rh_CHT_ref)
			y_CHT=XPLMGetDataf(self.y_CHT_ref)
			yh_CHT=XPLMGetDataf(self.yh_CHT_ref)
			g_CHT=XPLMGetDataf(self.g_CHT_ref)
			gh_CHT=XPLMGetDataf(self.gh_CHT_ref)
			self.msg1="CHT: "+str(round(chts[0]))+"/"+str(round(m_CHT))+" r: "+str(round(chtrs[0]))+"  RPM: "+str(round(rpms[0]))
			self.msg2="R HI: "+str(round(rh_CHT))+"  Y HI: "+str(round(yh_CHT))+"  G HI: "+str(round(gh_CHT))
			self.msg3="R LO: "+str(round(r_CHT))+"  Y LO: "+str(round(y_CHT))+"  G LO: "+str(round(g_CHT))

		self.msg4="En: "+str(eng_type[0])+" Prop: "+str(prop_type[0])
		self.msg5="IND: ITT: "+str(round(iITT[0]))+"  EGT: "+str(round(iEGT[0]))+"  CHT: "+str(round(iCHT[0]))
		self.msg6=str(self.acf_desc)
		print "XDMG = Got info..."
		self.createEventWindow()

		return 1