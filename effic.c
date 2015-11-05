#define XPLM200 1

#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include "SDK/CHeaders/XPLM/XPLMUtilities.h"
#include "SDK/CHeaders/XPLM/XPLMDefs.h"
#include "SDK/CHeaders/XPLM/XPLMDataAccess.h"
#include "SDK/CHeaders/XPLM/XPLMProcessing.h"
#include "SDK/CHeaders/XPLM/XPLMDisplay.h"
#include "SDK/CHeaders/XPLM/XPLMGraphics.h"

static XPLMCommandRef CmdATConn;
static XPLMDataRef FF_ref,TH_ref,PWR_ref,TIM_ref;

char * msg1, msg2;
int started=0;

static float gameLoopCallback(
	float  inElapsedSinceLastCall,
	float  inElapsedTimeSinceLastFlightLoop,
	int		  inCounter,
	void *	       inRefcon);

static void DrawWindowCB(
					   XPLMWindowID         inWindowID,    
					   void *               inRefcon);    

static void KeyCB(
					   XPLMWindowID         inWindowID,    
					   char                 inKey,    
					   XPLMKeyFlags         inFlags,    
					   char                 inVirtualKey,    
					   void *               inRefcon,    
					   int                  losingFocus);    

static int MouseClickCB(
					   XPLMWindowID         inWindowID,    
					   int                  x,    
					   int                  y,    
					   XPLMMouseStatus      inMouse,    
					   void *               inRefcon);    

PLUGIN_API int XPluginStart(char *outName, char *outSig, char *outDesc)
{

	strcpy(outName, "Efficiency Display");
	strcpy(outSig, "natt.perfdisp");
	strcpy(outDesc, "Displays efficiency info");
			
	float FF_ref=XPLMFindDataRef("sim/flightmodel/engine/ENGN_FF_"); //
	float TH_ref=XPLMFindDataRef("sim/flightmodel/engine/POINT_thrust"); //
	float PWR_ref=XPLMFindDataRef("sim/flightmodel/engine/ENGN_power"); //
	float TIM_ref=XPLMFindDataRef("sim/time/sim_speed_actual"); //
	
	float Nlb=0.22481; // N to lbf
	float Whp=0.00134102209; // W to hp
	int winPosX=800;
	int winPosY=1000;
	int win_w=200;
	int win_h=50;
	
	gWindow=XPLMCreateWindow(winPosX, winPosY, winPosX + win_w, winPosY - win_h, 1, DrawWindowCB, KeyCB, MouseClickCB, 0);
		
	CmdATConn = XPLMCreateCommand("fsei/flight/efficiency","Show/hide efficiency info");
	XPLMRegisterCommandHandler(CmdATConn, CmdATConnCB, 0, (void *) 0);
		
	printf("EFFIC - plugin loaded\n");	

	return 1;
}
		
int MouseClickCB(
				   XPLMWindowID         inWindowID,    
				   int                  x,    
				   int                  y,    
				   XPLMMouseStatus      inMouse,    
				   void *               inRefcon)
{
	return 1;
}

void MyHandleKeyCallback(
						   XPLMWindowID         inWindowID,    
						   char                 inKey,    
						   XPLMKeyFlags         inFlags,    
						   char                 inVirtualKey,    
						   void *               inRefcon,    
						   int                  losingFocus)
{
}    

int CmdATConnCB(XPLMCommandRef cmd, XPLMCommandPhase phase, void * refcon) { //Toggle reality
	if (phase==0) { //KeyDown event
		if (started==0) {
			XPLMRegisterFlightLoopCallback(gameLoopCB, 0.25, 0);
			started=1;
		} else {
			XPLMUnregisterFlightLoopCallback(gameLoopCB, 0);
			started=0;
		}
	}
	return 0;
}

PLUGIN_API void	XPluginStop(void)
{
	if (started==1)
		XPLMUnregisterFlightLoopCallback(gameLoopCB, 0);
		started=0;
	XPLMUnregisterCommandHandler(CmdATConn, CmdATConnCB, 0, 0);
	XPLMDestroyWindow(gWindow);
}

PLUGIN_API void XPluginDisable(void)
{
}

PLUGIN_API int XPluginEnable(void)
{
	return 1;
}

PLUGIN_API void XPluginReceiveMessage(XPLMPluginID inFromWho,
				long inMessage,	void *inParam)
{
}
		
void DrawWindowCallback(XPLMWindowID inWindowID, void * inRefcon):
	if (started==1) {
		int lLeft, lTop, lRight, lBottom;
		XPLMGetWindowGeometry(inWindowID, &lLeft, &lTop, &lRight, &lBottom);
		XPLMDrawTranslucentDarkBox(left,top,right,bottom);
		float color[]={1.0, 1.0, 1.0};
		XPLMDrawString(color, lLeft+5, lTop-(20), msg1, 0, xplmFont_Basic);
		XPLMDrawString(color, lLeft+5, lTop-(20+15), msg2, 0, xplmFont_Basic);
	}
}

float	gameLoopCallback(
                                   float                inElapsedSinceLastCall,    
                                   float                inElapsedTimeSinceLastFlightLoop,    
                                   int                  inCounter,    
                                   void *               inRefcon)
{
	float * FF, TH, PWR;
	XPLMGetDatavf(FF_ref, FF, 0, 1);
	XPLMGetDatavf(TH_ref, TH, 0, 1);
	XPLMGetDatavf(PWR_ref, PWR, 0, 1);
	float warp=XPLMGetDataf(TIM_ref);
	float tsfc=3600*FF[0]/(TH[0]*Nlb);
	float bsfc=3600*FF[0]/(PWR[0]*Whp);
	msg1="Warp: "+str(round(warp,1))+" FF: "+str(round(FF[0],3))+" kg/s";
	msg2="TSFC: "+str(round(tsfc,3))+"  BSFC: "+str(round(bsfc,3));
	
	msg1 = realloc(msg1, snprintf(NULL, 0, "Warp: %.1f FF: %.3f kg/s", warp, FF[0])+1);
	msg2 = realloc(msg2, snprintf(NULL, 0, "TSFC: %.3f  BSFC: %.3f", tsfc, bsfc)+1);
	sprintf(msg1, "Warp: %.1f FF: %.3f kg/s", warp, FF[0]);
	sprintf(msg2, "TSFC: %.3f  BSFC: %.3f", tsfc, bsfc);
	
	return 0.25;
}
