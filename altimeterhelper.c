#include <string.h>
#include <stdio.h>
#include "XPLMDisplay.h"
#include "XPLMGraphics.h"
#include "XPLMDataAccess.h"
#include "XPLMProcessing.h"

#include <GL/glew.h>

static float gameLoopCallback(float inElapsedSinceLastCall,
				float inElapsedTimeSinceLastFlightLoop, int inCounter,	
				void *inRefcon);

static void	MyHotKeyCallback(void *	inRefcon);

#define WINDOW_WIDTH 130
#define WINDOW_HEIGHT 80
#define FEET 3.28084

static XPLMHotKeyID	gHotKey = NULL;
static XPLMWindowID gWindow = NULL;
static char ChgMsg[17];
static XPLMDataRef baro_set_ref, baro_act_ref, flightTimeRef, alt_act_ref, alt_ind_ref, vvi_ref;
static float last_baro_set, last_alt;
static float remainingShowTime = 0.0f;
//static float remainingUpdateTime = 0.0f;

static int showTime = 2.0f;
static int winPosX = 20;
static int winPosY = 600;
static int lastMouseX, lastMouseY;
static int windowCloseRequest = 0;


PLUGIN_API int XPluginStart(char *outName, char *outSig, char *outDesc)
{

	strcpy(outName, "Altimeter Helper 1.0");
	strcpy(outSig, "natt.altimeterhelper");
	strcpy(outDesc, "A plugin that helps with altimeter settings.");

	baro_set_ref = XPLMFindDataRef("sim/cockpit/misc/barometer_setting"); //   float	660+	yes	???	The pilots altimeter setting
	baro_act_ref = XPLMFindDataRef("sim/weather/barometer_sealevel_inhg"); //   float	660+	yes	29.92 +- ....	The barometric pressure at sea level.
	flightTimeRef = XPLMFindDataRef("sim/time/total_flight_time_sec"); //   float	660+	yes	seconds	Total time since the flight got reset by something
	alt_act_ref = XPLMFindDataRef("sim/flightmodel/position/elevation"); // 	double	660+	no	meters	The elevation above MSL of the aircraft
	alt_ind_ref = XPLMFindDataRef("sim/cockpit2/gauges/indicators/altitude_ft_pilot"); // 	float	900+	no	feet	Indicated height, MSL, in feet, primary system, based on pilots barometric pressure input.
	vvi_ref = XPLMFindDataRef("sim/flightmodel/position/vh_ind_fpm"); // float 740+ yes fpm VVI (vertical velocity in feet per second)
	
	memset(ChgMsg, 0, sizeof(ChgMsg));
	XPLMRegisterFlightLoopCallback(gameLoopCallback, 0.05f, NULL);
	gHotKey = XPLMRegisterHotKey(XPLM_VK_B, xplm_DownFlag+xplm_ShiftFlag+xplm_ControlFlag, 
				"Sets altimeter automatically",
				MyHotKeyCallback,
				NULL);

	//printf("ALTI - plugin loaded\n");	

	return 1;
}


static void closeEventWindow()
{
	
	if (gWindow) {
		XPLMDestroyWindow(gWindow);
		gWindow = NULL;
	}
	
	memset(ChgMsg, 0, sizeof(ChgMsg));
	remainingShowTime = 0.0f;
}

PLUGIN_API void	XPluginStop(void)
{
	XPLMUnregisterHotKey(gHotKey);
	XPLMUnregisterFlightLoopCallback(gameLoopCallback, NULL);
	closeEventWindow();
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

void	MyHotKeyCallback(void *			   inRefcon)
{
	float alt, newbaro, baroact;
	alt = XPLMGetDataf(alt_ind_ref);
	baroact = XPLMGetDataf(baro_act_ref);
	if (alt > 18000.0) {
		newbaro = 29.92;
	} else {
		newbaro = baroact;
	}
		
	XPLMSetDataf(baro_set_ref, newbaro);
	//printf("ALTI - Alt ind: %.0f - Set altimeter to: %.2f\n",alt,newbaro);
}

void drawWindowCallback(XPLMWindowID inWindowID, void *inRefcon)
{
	//printf("ALTI - DrawWindow\n");

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
	if (windowCloseRequest)
		return 1;
	
	switch (inMouse) {
		case xplm_MouseDown:
			if ((x >= winPosX + WINDOW_WIDTH - 8) && (x <= winPosX + WINDOW_WIDTH) && 
						(y <= winPosY) && (y >= winPosY - 8))
				windowCloseRequest = 1;
			else {
				lastMouseX = x;
				lastMouseY = y;
			}
			break;
			
		case xplm_MouseDrag:
			winPosX += x - lastMouseX;
			winPosY += y - lastMouseY;
			XPLMSetWindowGeometry(gWindow, winPosX, winPosY, 
					winPosX + WINDOW_WIDTH, winPosY - WINDOW_HEIGHT);
			lastMouseX = x;
			lastMouseY = y;
			break;
			
		case xplm_MouseUp:
			break;
	}

	return 1;
}

static void keyboardCallback(XPLMWindowID inWindowID, char inKey, XPLMKeyFlags inFlags,	
				   char inVirtualKey, void *inRefcon, int losingFocus)
{
}


static void createEventWindow()
{
	remainingShowTime = showTime;
	//remainingUpdateTime = 1.0f;
	if (! gWindow)
		gWindow = XPLMCreateWindow(winPosX, winPosY, 
					winPosX + WINDOW_WIDTH, winPosY - WINDOW_HEIGHT, 
					1, drawWindowCallback, keyboardCallback, 
					mouseCallback, NULL);
}


static float gameLoopCallback(float inElapsedSinceLastCall,
				float inElapsedTimeSinceLastFlightLoop, int inCounter,	
				void *inRefcon)
{
	float alt = XPLMGetDataf(alt_ind_ref), vvi = XPLMGetDataf(vvi_ref);
	if (alt >= 18000.0 && last_alt < 18000.0) {
		// Climbing through 18000
		if (vvi >= 500.0 || (vvi < 500.0 && alt > 18250.0)) {
			XPLMSetDataf(baro_set_ref, 29.92);
			alt = XPLMGetDataf(alt_ind_ref);
		}
	} else if (alt < 18000.0 && last_alt >= 18000.0) {
		// Descending through 18000
		if (vvi < -500.0 || (vvi > -500.0 && alt < 17750.0)) {
			XPLMSetDataf(baro_set_ref, XPLMGetDataf(baro_act_ref));
			alt = XPLMGetDataf(alt_ind_ref);
		}
	}	
	
	float timeFromStart = XPLMGetDataf(flightTimeRef);
	float baro_set = XPLMGetDataf(baro_set_ref);

	//printf("ALTI - flight loop, tfs %.2f\n",timeFromStart);
	//printf("ALTI - P: %.2f   C: %.2f  remain: %.0f  tfs:%.2f\n",last_baro_set,baro_set,remainingUpdateTime,timeFromStart);

	if (3.0 < timeFromStart) {
	//printf("ALTI - over 3 from start\n");
		if (windowCloseRequest) {
			windowCloseRequest = 0;
		//printf("ALTI - Close window\n");
			closeEventWindow();
		} /*else
			if (0.0 < remainingUpdateTime) {
				remainingUpdateTime -= inElapsedSinceLastCall;
				if (0.0 > remainingUpdateTime)
					remainingUpdateTime = 0.0;
			printf("ALTI - 0 remain time\n");
			}*/
		if (0.0f < remainingShowTime) {
			remainingShowTime -= inElapsedSinceLastCall;
			//printf("ALTI - cdown show time\n");
			if (0.0f >= remainingShowTime)
				closeEventWindow();
		//printf("ALTI - close window\n");
		}
		if (baro_set != last_baro_set) {
			//printf("ALTI - altimeter changed to: %.2f\n",baro_set);
			sprintf(ChgMsg, "Altimeter  %.2f", baro_set);
			//printf("ALTI - create window\n");
			createEventWindow();
		}
	}
	
	last_baro_set = baro_set;
	last_alt = alt;

	return 0.05f;
}
