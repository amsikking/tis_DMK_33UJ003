# tis_DMK_33UJ003
Python device adaptor: The Imaging Source DMK 33UJ003 USB 3.0 monochrome industrial camera.
## Quick start:
- Install the device driver from The Imaging Source website (Device Driver for USB 33U, 37U, 38U Cameras and DFG/HDMI Converter). The version used here was "Cam33U_setup_5.1.0.1719.exe".
- Install the GUI (End User Software, IC Capture - Image Acquisition). The version used here was "setup_iccapture_2.5.1557.4007.en_US.exe".
- Check the camera with the GUI.
- Try to run 'tis_DMK_33UJ003.py' (requires Python and numpy). It needs the DLL files "tisgrabber_x64.dll" and "TIS_UDSHL11_x64.dll" in the same directory to work (versions included here for convenience).

![social_preview](https://github.com/amsikking/tis_DMK_33UJ003/blob/main/social_preview.png)

## Details:
- See the '\_\_main__' block at the bottom of "tis_DMK_33UJ003.py" for some typical ways to interact with the camera.
- The adaptor reveals a minimal API from the extensive TIS SDK.
- To develop the adaptor further, install the C SDK (Software Development Kit, IC Imaging Control C Library). The version used here was "TISGrabberSetup_3.4.0.51.exe". Navigate to "index.chm" for more information/options (here located at 
C:\Users\SOLS\Documents\The Imaging Source Europe GmbH\TIS Grabber DLL\doc). Also see "tisgrabber_import.py" in 
the 'include' folder for some Python example code, and 'theimagingsource.py' in https://github.com/AndrewGYork/tools for
some more example code and comments about interacting with TIS cameras. As a last resort look at the header file
"tisgrabber.h" in the 'include' folder for some more glues.
- **NOTE:** The TIS cameras/SDK are very challenging to work with! Often the documentation is incomplete or the device does not
behave as documented. A combination of the example code, GUI and testing can reveal the correct way to operate. This is tricky to navigate and time consuming.
