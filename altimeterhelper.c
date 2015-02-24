#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "SDK/CHeaders/XPLM/XPLMUtilities.h"
#include "SDK/CHeaders/XPLM/XPLMDisplay.h"
#include "SDK/CHeaders/XPLM/XPLMGraphics.h"
#include "SDK/CHeaders/XPLM/XPLMDataAccess.h"
#include "SDK/CHeaders/XPLM/XPLMProcessing.h"
#include "SDK/CHeaders/XPLM/XPLMDefs.h"

#include <GL/glew.h>

static float gameLoopCallback(float inElapsedSinceLastCall,
				float inElapsedTimeSinceLastFlightLoop, int inCounter,	
				void *inRefcon);

#define WINDOW_WIDTH 200
#define WINDOW_HEIGHT 35
#define FEET 3.28084 //m -> ft

static XPLMHotKeyID	gHotKey = NULL;
static XPLMWindowID gWindow = NULL;
static char ChgMsg[64];
static XPLMDataRef baro_set_ref, baro_act_ref, baro_am_ref, alt_act_ref, alt_ind_ref, vvi_ref;
static XPLMCommandRef CmdSHConn;
static float last_bar, last_alt;
static float remainingShowTime = 0.0f;
//static float remainingUpdateTime = 0.0f;

static int showTime = 2.0f; //Seconds to show the altimeter setting when changed
static int winPosX = 20;
static int winPosY = 500;
static int lastMouseX, lastMouseY;
static int windowCloseRequest = 0;
static int stdpress=0; //Whether standard pressure is set
static int trans_alt=18000;
static float tol[3];
tol = {17.009, 0.0058579, -0.000000012525}; //Parameters for altimeter tolerance

char getSign(float val);
float getAlt(float SL, float AM);
void setBaro(float bar_new);
void showBaro(float bar_new);
int CmdSHConnCB(XPLMCommandRef inCommand, XPLMCommandPhase inPhase, void * inRefcon);
void drawWindowCallback(XPLMWindowID inWindowID, void *inRefcon);
static int mouseCallback(XPLMWindowID inWindowID, int x, int y,	XPLMMouseStatus inMouse, void *inRefcon);
static void keyboardCallback(XPLMWindowID inWindowID, char inKey, XPLMKeyFlags inFlags,	char inVirtualKey, void *inRefcon, int losingFocus);

char getSign(float val) { //Puts a plus sign in front of positive values
	char sign;
	if (val>0)
		sign='+';
	return sign;
}

float getAlt(float SL, float AM) { //Determines altitude based on pressure delta
	float alt;
	alt=1000*(SL-AM);
	return alt;
}

void setBaro(float bar_new) { //Set the barometer
	float bar_old, del_baro_set;
	char *del_baro_str, *buf;
	size_t sz;
	bar_old=XPLMGetDataf(baro_set_ref);
	XPLMSetDataf(baro_set_ref, bar_new);
	del_baro_set=bar_new-bar_old;
	sz = snprintf(NULL,0,"Altimeter changed to: %.2f",bar_new);
	buf = (char *)malloc(sz+1);
	sz = snprintf(buf,sz+1,"Altimeter changed to: %.2f",bar_new);
	XPLMDebugString(buf);
	free(buf);
	sz = snprintf(NULL,0,"Altimeter  %.2f  %c%.2f inHg",bar_new,getSign(del_baro_set),del_baro_set);
	buf = (char *)malloc(sz+1);
	snprintf(buf,sz+1,"Altimeter  %.2f  %c%.2f inHg",bar_new,getSign(del_baro_set),del_baro_set);
	strcpy(ChgMsg, buf);
	remainingShowTime=showTime;
}

void showBaro(float bar_new) { //Show the barometer setting
	char *buf;
	size_t sz;
	sz=snprintf(NULL,0,"Altimeter  %.2f",bar_new);
	buf=(char *)malloc(sz+1);
	snprintf(buf,sz+1,"Altimeter  %.2f",bar_new);
	strcpy(ChgMsg, buf);
	remainingShowTime=showTime;
}

PLUGIN_API int XPluginStart(char *outName, char *outSig, char *outDesc)
{

	strcpy(outName, "Altimeter Helper 1.2");
	strcpy(outSig, "natt.altimeterhelper");
	strcpy(outDesc, "A plugin that helps with altimeter settings.");

	baro_set_ref = XPLMFindDataRef("sim/cockpit/misc/barometer_setting"); //   float	660+	yes	???	The pilots altimeter setting
	baro_act_ref = XPLMFindDataRef("sim/weather/barometer_sealevel_inhg"); //   float	660+	yes	29.92 +- ....	The barometric pressure at sea level.
	baro_am_ref = XPLMFindDataRef("sim/weather/barometer_current_inhg"); //   float	660+	no	29.92+-....	This is the barometric pressure at the point the current flight is at.
	alt_act_ref = XPLMFindDataRef("sim/flightmodel/position/elevation"); // 	double	660+	no	meters	The elevation above MSL of the aircraft
	alt_ind_ref = XPLMFindDataRef("sim/cockpit2/gauges/indicators/altitude_ft_pilot"); // 	float	900+	no	feet	Indicated height, MSL, in feet, primary system, based on pilots barometric pressure input.
	vvi_ref = XPLMFindDataRef("sim/flightmodel/position/vh_ind_fpm"); // float 740+ yes fpm VVI (vertical velocity in feet per second)
	
	//memset(ChgMsg, 0, sizeof(ChgMsg));
	XPLMRegisterFlightLoopCallback(gameLoopCallback, 0.05f, NULL);
	gWindow=XPLMCreateWindow(winPosX, winPosY, winPosX + WINDOW_WIDTH, winPosY - WINDOW_HEIGHT, 1, drawWindowCallback, keyboardCallback, mouseCallback, 0);

	CmdSHConn = XPLMCreateCommand("althelp/set_altimeter","Sets altimeter for current position and altitude");
	XPLMRegisterCommandHandler(CmdSHConn, CmdSHConnCB, 0, (void *) 0);
	
	//printf("ALTI - plugin loaded\n");	

	return 1;
}

PLUGIN_API void	XPluginStop(void)
{
	XPLMUnregisterCommandHandler(CmdSHConn, CmdSHConnCB, 0, 0);
	XPLMUnregisterFlightLoopCallback(gameLoopCallback, NULL);
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

int CmdSHConnCB(XPLMCommandRef cmd, XPLMCommandPhase phase, void * refcon) {
	if (phase==0) { //KeyDown event
		float newbaro;
		XPLMDebugString("AltHelper = CMD set altimeter\n");
		if (XPLMGetDataf(alt_ind_ref) > trans_alt) {
			newbaro=29.92;
		} else {
			newbaro=XPLMGetDataf(baro_act_ref);
		}
		newbaro_hund=newbaro*100;
		baroset_hund=XPLMGetDataf(baro_set_ref)*100;
		newbaro_hund >= 0 ? (long)(newbaro_hund+0.5) : (long)(newbaro_hund-0.5);
		baroset_hund >= 0 ? (long)(baroset_hund+0.5) : (long)(baroset_hund-0.5);
		if (abs(newbaro_hund-baroset_hund)>0) {
			last_bar=newbaro;
			setBaro(newbaro);
		} else {
			showBaro(newbaro);
		}
	}
	return 0;
}

void drawWindowCallback(XPLMWindowID inWindowID, void *inRefcon)
{
	//XPLMDebugString("ALTI - DrawWindow\n");

	if (0.0f < remainingShowTime) {
		int left, top, right, bottom;
		float color[] = { 1.0, 1.0, 1.0 }; 	/* RGB White */
			
		XPLMGetWindowGeometry(inWindowID, &left, &top, &right, &bottom);
		XPLMDrawTranslucentDarkBox(left, top, right, bottom);
		XPLMDrawString(color, left + 5, top - 20, 
					ChgMsg, NULL, xplmFont_Basic);
		
		glDisable(GL_TEXTURE_2D);
		glColor3f(0.7, 0.7, 0.7);
		glBegin(GL_LINES);
		  glVertex2i(right - 1, top - 1);
		  glVertex2i(right - 7, top - 7);
		  glVertex2i(right - 7, top - 1);
		  glVertex2i(right - 1, top - 7);
		glEnd();
		glEnable(GL_TEXTURE_2D);
	}
}								   

static int mouseCallback(XPLMWindowID inWindowID, int x, int y,	
				   XPLMMouseStatus inMouse, void *inRefcon)
{
	return 0;
}

static void keyboardCallback(XPLMWindowID inWindowID, char inKey, XPLMKeyFlags inFlags,	
				   char inVirtualKey, void *inRefcon, int losingFocus)
{
}

static float gameLoopCallback(float inElapsedSinceLastCall,
				float inElapsedTimeSinceLastFlightLoop, int inCounter,	
				void *inRefcon)
{
	float alt = XPLMGetDataf(alt_ind_ref), vvi = XPLMGetDataf(vvi_ref);
	float alt_act=XPLMGetDataf(alt_act_ref)*FEET, bar=XPLMGetDataf(baro_set_ref);
	float bar_am=XPLMGetDataf(baro_am_ref), bar_act=XPLMGetDataf(baro_act_ref);
	float alt_err, tolerance, baro_hund, lastbar_hund;
	
	if ( 0 < remainingShowTime)
		remainingShowTime -= inElapsedSinceLastCall;
	
	if ((vvi >= 500 && alt >= (trans_alt-25) || vvi < 500 && vvi > 0 && alt > trans_alt+250) && stdpress==0) { // Climbing through 18000
		bar=29.92;
		stdpress=1;
		setBaro(bar);
	} else if ((vvi <= -500 && alt < (trans_alt-25) || vvi > -500 && vvi < 0 && alt < trans_alt - 250) && stdpress==1) { // Descending through 18000
		bar=XPLMGetDataf(baro_act_ref);
		stdpress=0;
		setBaro(bar);
	}
	
	alt_err=getAlt(bar-bar_act,0);
	alt_err=(alt-alt_act);
	tolerance=tol[2]*alt*alt+tol[1]*alt+tol[0]; //Determine altimeter error tolerance
	if (fabs(alt_err)>tolerance && stdpress==0) {
		char *buf;
		size_t sz;
		sz = snprintf(NULL,0,"Altimeter off by %c%.0f feet!",getSign(alt_err),alt_err);
		buf = (char *)malloc(sz+1);
		sz = snprintf(buf,sz+1,"Altimeter off by %c%.0f feet!",getSign(alt_err),alt_err);
		strcpy(ChgMsg,buf);
		remainingShowTime=showTime;
	}
	baro_hund=bar*100;
	lastbar_hund=last_bar*100;
	baro_hund >= 0 ? (long)(baro_hund+0.5) : (long)(baro_hund-0.5);
	lastbar_hund >= 0 ? (long)(lastbar_hund+0.5) : (long)(lastbar_hund-0.5);
	if (abs(baro_hund-lastbar_hund)>0)
		showBaro(bar);
	
	last_bar = bar;
	last_alt = alt;

	return 0.1f;
}
