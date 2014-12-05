from XPLMProcessing import *
from XPLMDataAccess import *
from XPLMDisplay import *
from XPLMGraphics import *
from XPLMDefs import *
from XPLMUtilities import *

class PythonInterface:

	def XPluginStart(self):
		self.Name="PCAT"
		self.Sig= "natt.python.pcat"
		self.Desc="Basic auto-throttle"
		self.VERSION="0.1"
		
		self.TO_ref=XPLMFindDataRef("sim/operation/override/override_throttles") #	int	710+	yes	boolean	Override the throttles (use ENGN_thro_use to control them)
		self.thrott_ref=XPLMFindDataRef("sim/flightmodel/engine/ENGN_thro") #	float[8]	660+	yes	ratio	Throttle (per engine) as set by user, 0 = idle, 1 = max
		self.throtto_ref=XPLMFindDataRef("sim/flightmodel/engine/ENGN_thro_use") #	float[8]	710+	yes	ratio 	Throttle (per engine) when overridden by you, plus with thrust vectors - use override_throttles to change.
		self.TRQ_ref=XPLMFindDataRef("sim/flightmodel/engine/ENGN_TRQ") #	float[8]	660+	yes	NewtonMeters	Torque (per engine)
		self.N1_ref=XPLMFindDataRef("sim/flightmodel/engine/ENGN_N1_")
		self.num_eng_ref=XPLMFindDataRef("sim/aircraft/engine/acf_num_engines")
		self.ias_ref=XPLMFindDataRef("sim/flightmodel/position/indicated_airspeed")
		self.alpha_ref=XPLMFindDataRef("sim/flightmodel/position/alpha")
		self.alphawarn_ref=XPLMFindDataRef("sim/aircraft/overflow/acf_stall_warn_alpha")
		self.stallwarn_ref=XPLMFindDataRef("sim/cockpit2/annunciators/stall_warning")
		self.acf_desc_ref=XPLMFindDataRef("sim/aircraft/view/acf_descrip")
		self.ap_as_ref=XPLMFindDataRef("sim/cockpit/autopilot/airspeed")
		self.ap_asmach_ref=XPLMFindDataRef("sim/cockpit/autopilot/airspeed_is_mach")
		self.eng_type_ref=XPLMFindDataRef("sim/aircraft/prop/acf_en_type")

		self.Nlb=0.22481 # N to lbf
		self.mft=3.2808399 # m to ft
		self.Kp=1.0 # PID controller gains
		self.Ki=0.005
		self.Kd=10.0
		self.Integrator_max=10
		self.Integrator_min=-10
		self.Integrator=0
		self.Derivator=0
		self.IAS=140.0
		self.started=0
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
		self.CmdATConn = XPLMCreateCommand("pcat/toggle","Starts or stops auto throttle")
		self.CmdATConnCB = self.CmdATConnCallback
		XPLMRegisterCommandHandler(self, self.CmdATConn, self.CmdATConnCB, 0, 0)
		self.CmdUpConn = XPLMCreateCommand("pcat/ias_up","Set IAS +1kt")
		self.CmdUpConnCB = self.CmdUpConnCallback
		XPLMRegisterCommandHandler(self, self.CmdUpConn, self.CmdUpConnCB, 0, 0)
		self.CmdDnConn = XPLMCreateCommand("pcat/ias_down","Set IAS -1kt")
		self.CmdDnConnCB = self.CmdDnConnCallback
		XPLMRegisterCommandHandler(self, self.CmdDnConn, self.CmdDnConnCB, 0, 0)

		return self.Name, self.Sig, self.Desc
		
	def MouseClickCallback(self, inWindowID, x, y, inMouse, inRefcon):
		return 0

	def KeyCallback(self, inWindowID, inKey, inFlags, inVirtualKey, inRefcon, losingFocus):
		pass 

	def CmdATConnCallback(self, cmd, phase, refcon):
		if(phase==0): #KeyDown event
			print "PCAT = Toggle AT"
			self.toggleInfo()
		return 0
	
	def CmdUpConnCallback(self, cmd, phase, refcon):
		if(phase==0): #KeyDown event
			print "PCAT = IAS +"
			self.IAS+=1.0
			XPLMSetDataf(self.ap_as_ref, self.IAS)
		return 0
	
	def CmdDnConnCallback(self, cmd, phase, refcon):
		if(phase==0): #KeyDown event
			print "PCAT = IAS -"
			self.IAS-=1.0
			XPLMSetDataf(self.ap_as_ref, self.IAS)
		return 0
		
	def toggleInfo(self):
		if self.started==0:
			XPLMSetDatai(self.ap_asmach_ref, 0)
			acf_descb=[]
			XPLMGetDatab(self.acf_desc_ref, acf_descb, 0, 500)
			self.ac=self.getshortac(str(acf_descb))
			self.num_eng=XPLMGetDatai(self.num_eng_ref)
			XPLMSetDataf(self.ap_as_ref, self.IAS)
			XPLMGetDatavi(self.eng_type_ref, self.eng_type, 0, self.num_eng)
			#T=[]
			#XPLMGetDatavf(self.thrott_ref, T, 0, self.num_eng)
			#XPLMSetDatavf(self.throtto_ref, T, 0, self.num_eng)
			#XPLMSetDatai(self.TO_ref, 1)
			#override=XPLMGetDatai(self.TO_ref)
			XPLMRegisterFlightLoopCallback(self, self.gameLoopCB, 0.5, 0)
			self.started=1
		else:
			XPLMUnregisterFlightLoopCallback(self, self.gameLoopCB, 0)
			self.ac=""
			self.eng_type=[]
			#T=[]
			#XPLMGetDatavf(self.throtto_ref, T, 0, self.num_eng)
			#XPLMSetDatavf(self.thrott_ref, T, 0, self.num_eng)
			#XPLMSetDatai(self.TO_ref, 0)
			self.started=0
		pass
		
	def XPluginStop(self):
		XPLMUnregisterCommandHandler(self, self.CmdATConn, self.CmdATConnCB, 0, 0)
		XPLMUnregisterCommandHandler(self, self.CmdUpConn, self.CmdUpConnCB, 0, 0)
		XPLMUnregisterCommandHandler(self, self.CmdDnConn, self.CmdDnConnCB, 0, 0)
		if self.started==1:
			self.toggleInfo()
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
		kias=XPLMGetDataf(self.ias_ref)
		TO=[]
		XPLMGetDatavf(self.thrott_ref, TO, 0, self.num_eng)
		alpha=XPLMGetDataf(self.alpha_ref)
		awarn=XPLMGetDataf(self.alphawarn_ref)
		swarn=XPLMGetDatai(self.stallwarn_ref)
		err=self.IAS-kias
		PID=self.update(err)
		torque_psi=0.0
		if alpha<awarn-0.25 and swarn==0:
			if self.eng_type[0]==2 or self.eng_type[0]==8: #Turboprop
				TRQ=[]
				XPLMGetDatavf(self.TRQ_ref, TRQ, 0, self.num_eng)
				if self.ac == "PC12":
					#print "PCAT - setting PC12 throttle"
					torque_psi=0.0088168441*TRQ[0]
					if torque_psi > 36.95:
						TO[0]-=0.02
					else:
						TO[0]+=PID/400.0
				elif self.ac == "B190":
					torque_ftlb1=self.Nlb*self.mft*TRQ[0]
					torque_ftlb2=self.Nlb*self.mft*TRQ[1]
					if torque_ftlb1>3750.0 or torque_ftlb2>3750.0:
						TO[0]-=0.02
						TO[1]-=0.02
					else:
						TO[0]+=PID/400.0
						TO[1]+=PID/400.0
				else:
					for i in range(0,self.num_eng):
						TO[i]+=PID/400.0	
			elif self.eng_type[0]==4 or self.eng_type[0]==5: #Jet
				N1=[]
				XPLMGetDatavf(self.N1_ref, N1, 0, self.num_eng)
				if self.ac == "CL30":
					if N1[0]>95.0 or N1[1]>95.0:
						TO[0]-=0.02
						TO[1]-=0.02
					else:
						TO[0]+=PID/400.0
						TO[1]+=PID/400.0
				else:
					for i in range(0,self.num_eng):
						TO[i]+=PID/400.0
		else:
			#print "PCAT - STALL!"
			for i in range(0,self.num_eng):
				TO[i]=1.0
		if TO[0]>1:
			TO[0]=1.0
		elif TO[0]<0:
			TO[0]=0.0
		
		#override=XPLMGetDatai(self.TO_ref)
		#print "PCAT - override "+str(override)
		XPLMSetDatavf(self.thrott_ref, TO, 0, self.num_eng)
		
		self.msg[0]="err: "+str(round(err,2))+" a: "+str(round(alpha,1))+"/"+str(round(awarn,1))+" warn: "+str(swarn)
		self.msg[1]="TO: "+str(round(TO[0],3))+" PID: "+str(round(PID,4))
		self.msg[2]="ac: "+self.ac+" trq: "+str(round(torque_psi,2))+" psi "+str(round(TRQ[0],2))
		
		return 1

	def update(self,error):
		P_value = self.Kp * error
		D_value = self.Kd * ( error - self.Derivator)
		self.Derivator = error
		self.Integrator += error
		if self.Integrator > self.Integrator_max:
			self.Integrator = self.Integrator_max
		elif self.Integrator < self.Integrator_min:
			self.Integrator = self.Integrator_min
		I_value = self.Integrator * self.Ki

		self.msg[3]=str(round(P_value,4))+" "+str(round(I_value,4))+" "+str(round(D_value,4))
		PID = P_value + I_value + D_value

		return PID
		
	def getshortac(self,acf_desc):
		if acf_desc=="['Pilatus PC-12']":
			ac_short="PC12"
		elif acf_desc=="['wouldnt you like to be a pepper too']":
			ac_short="B190"
		elif acf_desc=="['ok']":
			ac_short="CL30"
			self.IAS=250.0
		else:
			ac_short=acf_desc
		return ac_short
