# Imports from the python standard library:
import ctypes as C
import os

# Third party imports, installable via pip:
import numpy as np

class Camera:
    '''
    Basic device adaptor for The Imaging Source DMK 33UJ003 USB 3.0 monochrome
    industrial camera. Many more commands are available and have not been
    implemented.
    '''    
    def __init__(self,
                 name='tis_DMK_33UJ003',
                 verbose=True,
                 very_verbose=False):
        self.name = name
        self.verbose = verbose
        self.very_verbose = very_verbose
        # initialize and check device:
        self._init_dll()
        device_count = self._get_device_count()
        if device_count != 1:
            raise Exception("currently only 1 device supported " +
                            "(found %i)"%device_count)
        device_name = self._get_device_name(0)  # zeroth only (1 device)
        dev_type = (device_name.decode('ascii').split()[0] + "_" +
                    device_name.decode('ascii').split()[1])
        if self.verbose:
            print("%s: -> device type = %s"%(self.name, dev_type))
        assert dev_type == 'DMK_33UJ003', "device type not supported"
        self.handle = self._get_handle()
        self._open_device(device_name)
        self._validate_device()
        # find available video formats:
        video_format_count = self._get_video_format_count()
        self.video_formats_from_device = []
        for i in range(video_format_count):
            video_format = self._get_video_format(i)
            if video_format.startswith("Y16"):  # support 16bit only
                self.video_formats_from_device.append(video_format)
        # actually only some of the video formats work!
        # so here's a hand picked dict:
        self.video_formats = {'Y16 (640x480)'   :5,
                              'Y16 (1024x768)'  :11,
                              'Y16 (1280x960)'  :12,
                              'Y16 (1280x1024)' :13,
                              'Y16 (1600x1200)' :14,
                              'Y16 (1920x1080)' :15,
                              'Y16 (2048x1536)' :16,
                              'Y16 (3856x2764)' :17}
        # get limits on settings and set defaults:
        self._set_auto_camera_property(4, False)    # switch off autoexposure
        self.min_exposure_us, self.max_exposure_us = self._get_exposure_range()
        self.max_exposure_us = 1600000              # wierd after ~1.6s
        self._set_auto_video_property(9, False)     # switch off autogain
        self.min_gain, self.max_gain = self._get_video_property_range(9)
        self.apply_settings(
            exposure_us=self.min_exposure_us,       # default min
            gain=self.max_gain,                     # default max
            video_format='Y16 (3856x2764)',         # default (max)
            trigger_enable=True,                    # default tigger camera
            timeout_ms=1000                         # default 1s timeout
            )

    def _init_dll(self):
        if self.very_verbose:
            print("%s: initializing DLL library..."%self.name, end='')
        dll.init(None)
        if self.very_verbose:
            print("done")
        return None

    def _get_device_count(self):
        if self.very_verbose:
            print("%s: getting device count"%self.name)
        device_count = dll.get_device_count()
        if self.very_verbose:
            print("%s: -> num_devices = %i"%(self.name, device_count))
        return device_count

    def _get_device_name(self, name_index):
        if self.verbose:
            print("%s: getting device name (index=%i)"%(
                self.name, name_index))
        assert isinstance(name_index, int), 'name_index must be an integer'
        device_name = dll.get_name_from_list(name_index)
        if self.verbose:
            print("%s: -> device name = %s"%(
                self.name, device_name.decode('ascii')))
        return device_name

    def _get_handle(self):
        if self.very_verbose:
            print("%s: getting handle..."%self.name, end='')
        handle = dll.create_grabber()
        if self.very_verbose:
            print("done")
        return handle

    def _open_device(self, device_name):
        if self.very_verbose:
            print("%s: opening device..."%self.name, end='')
        dll.open_by_name(self.handle, device_name)
        if self.very_verbose:
            print("done")
        return None

    def _validate_device(self):
        if self.very_verbose:
            print("%s: validating device..."%self.name, end='')
        dll.is_device_valid(self.handle)
        if self.very_verbose:
            print("done")
        return None

    def _set_overlay(self, enable):
        if self.very_verbose:
            print("%s: setting overlay = %s"%(self.name, enable))
        assert enable in (0, 1), "enable must be '0' or '1'"
        dll.set_overlay(self.handle, enable)
        if self.very_verbose:
            print("%s: -> done setting overlay"%self.name)
        return None

    def _start_live(self):
        if self.very_verbose:
            print("%s: starting live..."%self.name, end='')
        dll.start_live(self.handle, 0)
        self.live_mode = True
        if self.very_verbose:
            print("done.")
        return None

    def _stop_live(self):
        if self.very_verbose:
            print("%s: stopping live..."%self.name, end='')
        dll.stop_live(self.handle)
        self.live_mode = False
        if self.very_verbose:
            print("done.")
        return None

    def _get_color_format(self):
        if self.very_verbose:
            print("%s: getting color format"%self.name)
        color_index = dll.get_format(self.handle)
        if self.very_verbose:
            print("%s: -> color format = %s"%(self.name, color_index))
        return color_index

    def _set_color_format(self, color_index):
        if self.very_verbose:
            print("%s: setting color format = %s"%(
                self.name, color_index))
        assert isinstance(color_index, int), 'color_index must be an integer'
        dll.set_format(self.handle, color_index)
        # Must start and stop live mode to register color format and return
        # the correct value (seemingly not not documented)
        self._start_live()
        self._stop_live()
        assert self._get_color_format() == color_index
        if self.very_verbose:
            print("%s: -> done setting color format"%self.name)
        return None

    def _get_auto_camera_property(self, property_index):
        if self.very_verbose:
            print("%s: getting auto camera property (property_index=%i)"%(
                self.name, property_index))
        assert isinstance(
            property_index, int), 'property_index must be an integer'
        en = C.c_int(777)
        dll.get_auto_camera_property(self.handle, property_index, en)
        enable = bool(en.value)
        if self.very_verbose:
            print("%s: -> auto property value = %s"%(self.name, enable))
        return enable

    def _set_auto_camera_property(self, property_index, enable):
        if self.very_verbose:
            print("%s: setting camera property = %s (property_index=%s)"%(
                self.name, enable, property_index))
        assert isinstance(property_index, int),(
            'property_index must be an integer')
        assert isinstance(enable, bool),(
            'enable must be boolean')
        dll.set_auto_camera_property(self.handle, property_index, enable)
        assert self._get_auto_camera_property(property_index) == enable
        if self.very_verbose:
            print("%s: -> done setting camera property"%self.name)
        return None

    def _get_exposure_range(self):
        if self.very_verbose:
            print("%s: getting exposure range"%self.name)
        mn, mx = C.c_float(777), C.c_float(777)
        dll.get_exposure_range(self.handle, mn, mx)
        min_exposure_us = int(round(1e6 * mn.value))
        max_exposure_us = int(round(1e6 * mx.value))
        if self.very_verbose:
            print("%s: -> property range = %s -> %s"%(
                self.name, min_exposure_us, max_exposure_us))
        return min_exposure_us, max_exposure_us

    def _get_exposure_us(self):
        if self.very_verbose:
            print("%s: getting exposure"%self.name)
        exp = C.c_float(777)
        dll.get_exposure(self.handle, exp)
        self.exposure_us = int(round(1e6 * exp.value))
        if self.very_verbose:
            print("%s: -> exposure_us = %i"%(self.name, self.exposure_us))
        return self.exposure_us

    def _set_exposure_us(self, exposure_us):
        if self.very_verbose:
            print("%s: setting exposure_us = %s"%(self.name, exposure_us))
        assert isinstance(exposure_us, int), 'exposure_us must be an integer'
        assert self.min_exposure_us <= exposure_us <= self.max_exposure_us, (
            'exposure_us (%s) out of range'%exposure_us)
        exp = 1e-6 * exposure_us
        dll.set_exposure(self.handle, exp)
        assert self._get_exposure_us() == exposure_us
        if self.very_verbose:
            print("%s: -> done setting exposure"%self.name)
        return None

    def _get_auto_video_property(self, property_index):
        if self.very_verbose:
            print("%s: getting auto video property (property_index=%i)"%(
                self.name, property_index))
        assert isinstance(
            property_index, int), 'property_index must be an integer'
        en = C.c_int(777)
        dll.get_auto_video_property(self.handle, property_index, en)
        enable = en.value
        if self.very_verbose:
            print("%s: -> auto property value = %s"%(self.name, enable))
        return enable

    def _set_auto_video_property(self, property_index, enable):
        if self.very_verbose:
            print("%s: setting video property = %s (property_index=%s)"%(
                self.name, enable, property_index))
        assert isinstance(property_index, int),(
            'property_index must be an integer')
        assert isinstance(enable, bool),(
            'enable must be boolean')
        dll.set_auto_video_property(self.handle, property_index, enable)
        assert self._get_auto_video_property(property_index) == enable
        if self.very_verbose:
            print("%s: -> done setting video property"%self.name)
        return None

    def _get_video_property_range(self, property_index):
        "0 = black level"
        "4 = frame rate?"
        "5 = gamma?"
        "9 = gain"
        if self.very_verbose:
            print("%s: getting video property range (property_index=%i)"%(
                self.name, property_index))
        assert isinstance(
            property_index, int), 'property_index must be an integer'
        mn, mx = C.c_long(777), C.c_long(777)
        dll.get_video_property_range(self.handle, property_index, mn, mx)
        property_min, property_max = mn.value, mx.value
        if self.very_verbose:
            print("%s: -> property range = %s -> %s"%(
                self.name, property_min, property_max))
        return property_min, property_max

    def _get_video_property(self, property_index):
        if self.very_verbose:
            print("%s: getting video property (property_index=%i)"%(
                self.name, property_index))
        assert isinstance(
            property_index, int), 'property_index must be an integer'
        pv = C.c_long(777)
        dll.get_video_property(self.handle, property_index, pv)
        property_value = pv.value
        if self.very_verbose:
            print("%s: -> property value = %s"%(self.name, property_value))
        return property_value

    def _set_video_property(self, property_index, property_value):
        if self.very_verbose:
            print("%s: setting video property = %s (property_index=%s)"%(
                self.name, property_value, property_index))
        assert isinstance(property_index, int),(
            'property_index must be an integer')
        dll.set_video_property(self.handle, property_index, property_value)
        assert self._get_video_property(property_index) == property_value
        if self.very_verbose:
            print("%s: -> done setting video property"%self.name)
        return None

    def _get_video_format_count(self):
        if self.very_verbose:
            print("%s: getting video format count"%self.name)
        video_format_count = dll.get_video_format_count(self.handle)
        if self.very_verbose:
            print("%s: -> video format count = %s"%(
                self.name, video_format_count))
        return video_format_count

    def _get_video_format(self, format_index):
        if self.very_verbose:
            print("%s: getting video format (format_index=%i)"%(
                self.name, format_index))
        assert isinstance(format_index, int), 'format_index must be an integer'
        vf = dll.get_video_format(self.handle, format_index)
        video_format = vf.decode('ascii')
        if self.very_verbose:
            print("%s: -> video format = %s"%(self.name, video_format))
        return video_format

    def _set_video_format(self, video_format):
        if self.very_verbose:
            print("%s: setting video format = %s"%(self.name, video_format))
        assert video_format in self.video_formats.keys(), (
            'video format %s not supported'%video_format)
        dll.set_video_format(self.handle, video_format.encode('ascii'))
        format_index = self.video_formats[video_format]
        assert self._get_video_format(format_index) == video_format
        if self.very_verbose:
            print("%s: -> done setting video format"%self.name)
        return None            

    def _get_image_parameters(self):
        if self.very_verbose:
            print("%s: getting image parameters"%self.name)
        width_px, height_px = C.c_long(), C.c_long()
        bit_depth, color = C.c_int(), C.c_int()
        dll.get_image_description(self.handle,
                                  width_px,
                                  height_px,
                                  bit_depth,
                                  color)
        self.width_px, self.height_px = width_px.value, height_px.value
        self.bit_depth, self.color = bit_depth.value, color.value
        if self.very_verbose:
            print("%s: -> %i x %i (width x height)"%(
                self.name, self.width_px, self.height_px))
            print("%s: -> bit depth = %s"%(self.name, self.bit_depth))
            print("%s: -> color = %s"%(self.name, self.color))
        return None

    def _set_trigger_enable(self, enable):
        if self.very_verbose:
            print("%s: setting trigger enable = %s"%(self.name, enable))
        assert isinstance(enable, bool), 'enable must be boolean'
        dll.is_trigger_available(self.handle)
        dll.enable_trigger(self.handle, enable)
        if self.very_verbose:
            print("%s: -> done setting trigger enable"%self.name)
        return None

    def _send_software_trigger(self):
        if self.very_verbose:
            print("%s: sending software trigger..."%self.name, end='')
        dll.software_trigger(self.handle)
        if self.very_verbose:
            print("done.")
        return None

    def _snap_image(self):
        if self.very_verbose:
            print("%s: snaping image..."%self.name, end='')
        # timeout_ms: how long will the dll call wait for an image before error
        timeout_ms = int(round(self.timeout_ms + 1e3 * self.exposure_us))
        if self.timeout_ms == -1:
            timeout_ms = -1 # no timeout, block indefinitely
        dll.snap_image(self.handle, timeout_ms)
        if self.very_verbose:
            print("done.")
        return None

    def _get_image(self):
        if self.very_verbose:
            print("%s: getting image..."%self.name, end='')
        pointer = dll.get_image_pointer(self.handle)
        bytes_per_image = 2 * self.width_px * self.height_px
        image = np.ctypeslib.as_array(pointer, (bytes_per_image,))
        image = image.view(dtype=np.uint16) # view as 16bit
        image = image.reshape(self.height_px, self.width_px) # line to image
        if self.very_verbose:
            print("done.")
        return image

    def apply_settings(
        self,
        num_images=None,    # total number of images to record, type(int)
        exposure_us=None,   # 100 <= type(int) <= 1,600,000
        gain=None,          # 100 <= type(int) <= 383
        video_format=None,  # e.g. 'Y16 (3856x2764)'
        trigger_enable=None,# True or False
        timeout_ms=None,    # set to -1 for no timeout while waiting for image
        ):
        if self.verbose:
            print("%s: applying settings..."%self.name)
        if num_images is not None:
            assert isinstance(num_images, int), (
            "%s: unexpected type for num_images"%self.name)
            self.num_images = num_images
        if exposure_us is not None:
            assert isinstance(
                exposure_us, int) or isinstance(exposure_us, float)
            exposure_us = int(round(exposure_us))
            self._set_exposure_us(exposure_us)
        if gain is not None:
            assert isinstance(gain, int) or isinstance(gain, float)
            gain = int(round(gain))
            assert self.min_gain <= gain <= self.max_gain, (
                "%s: gain %s out of range"%(self.name, gain))
            self._set_video_property(9, gain)
        if video_format is not None:
            self._set_video_format(video_format)
            # configure device for 16bit operation:
            self._set_overlay(0) # "for Y16 format the overlay must be removed"
            self._set_color_format(4) # Y16 = 4 (seemingly not not documented)
            self._get_image_parameters() # update attributes
        if trigger_enable is not None:
            self._set_trigger_enable(trigger_enable)
        if timeout_ms is not None:
            assert isinstance(timeout_ms, int), (
            "%s: unexpected type for timeout_ms"%self.name)
            self.timeout_ms = timeout_ms
        if self.verbose:
            print("%s: -> done applying settings."%self.name)
        return None

    def record_to_memory(
        self,
        allocated_memory=None,  # optionally pass numpy array for images
        software_trigger=True,  # False -> external trigger needed
        ):
        if self.verbose:
            print("%s: recording to memory..."%self.name)
        if not self.live_mode:
            self._start_live()
        h_px, w_px = self.height_px, self.width_px
        if allocated_memory is None: # make numpy array if none given
            allocated_memory = np.zeros((self.num_images, h_px, w_px), 'uint16')
            output = allocated_memory # no memory provided so return some images
        else: # images placed in provided array
            assert isinstance(allocated_memory, np.ndarray), (
            "%s: unexpected type for allocated_memory"%self.name)
            assert allocated_memory.dtype == np.uint16, (
            "%s: unexpected dtype for allocated_memory"%self.name)
            assert allocated_memory.shape == (self.num_images, h_px, w_px), (
            "%s: unexpected shape for allocated_memory"%self.name)
            output = None # avoid returning potentially large array
        for i in range(self.num_images):
            if software_trigger:
                self._send_software_trigger()
            try:
                self._snap_image()
            except Exception as e:
                print("%s: -> buffer timeout?"%self.name)
                raise
            try:
                image = self._get_image()
            except Exception as e:
                print("%s: -> image transfer failed?"%self.name)
                raise
            allocated_memory[i, :, :] = image # get image
            remaining_images = self.num_images - i - 1
        assert remaining_images == 0, (
            "%s: acquired images != requested"%self.name)
        self._stop_live() # should this be done?
        if self.verbose:
            print("%s: -> done recording to memory."%self.name)
        return output

    def close(self):
        if self.verbose:
            print("%s: closing..."%self.name, end='')
        dll.release_grabber(self.handle)
        if self.verbose:
            print("done.")
        return None

### Tidy and store DLL calls away from main program:

os.add_dll_directory(os.getcwd())
try:
    dll = C.windll.LoadLibrary("tisgrabber_x64") # Load the DLL
except (OSError,):
    print('Failed to load essential "tisgrabber_x64.dll"')
    print('("TIS_UDSHL10_x64.dll" is also required)')
    raise

def check_error(error_code):
    if error_code == 1: # success
        return 1
    else:
        raise OSError('dll error: %i'%error_code)

# Initialize the library
dll.init = dll.IC_InitLibrary       
dll.init.argtypes = [C.c_char_p]
dll.init.restype = check_error

# Get the number of the currently available devices
dll.get_device_count = dll.IC_GetDeviceCount
dll.get_device_count.argtypes = []
dll.get_device_count.restype = C.c_int

# Get the unique name of a video capture device
dll.get_name_from_list = dll.IC_GetUniqueNamefromList
dll.get_name_from_list.argtypes = [C.c_int]
dll.get_name_from_list.restype = C.c_char_p

class GrabberHandle_t(C.Structure):
    _fields_ = [('unused', C.c_int)]
GrabberHandle = C.POINTER(GrabberHandle_t)

# Create a new grabber handle
dll.create_grabber = dll.IC_CreateGrabber
dll.create_grabber.argtypes = []
dll.create_grabber.restype = GrabberHandle

# Release HGRABBER object
dll.release_grabber = dll.IC_ReleaseGrabber
dll.release_grabber.argtypes = [C.POINTER(GrabberHandle)]
dll.release_grabber.restype = None

# Open a video capture by using its UniqueName
dll.open_by_name = dll.IC_OpenDevByUniqueName
dll.open_by_name.argtypes = [GrabberHandle, C.c_char_p]
dll.open_by_name.restype = check_error

# Returns whether a video capture device is valid
dll.is_device_valid = dll.IC_IsDevValid
dll.is_device_valid.argtypes = [GrabberHandle]
dll.is_device_valid.restype = check_error

# Starts the live video
dll.start_live = dll.IC_StartLive
dll.start_live.argtypes = [GrabberHandle, C.c_int]
dll.start_live.restype = check_error

# Stops the live video
dll.stop_live = dll.IC_StopLive
dll.stop_live.argtypes = [GrabberHandle]
dll.stop_live.restype = None

# Remove or insert the the overlay bitmap to the grabber object
dll.set_overlay = dll.IC_RemoveOverlay
dll.set_overlay.argtypes = [GrabberHandle, C.c_int]
dll.set_overlay.restype = check_error

# Returns the current color format of the sink
dll.get_format = dll.IC_GetFormat
dll.get_format.argtypes = [GrabberHandle]
dll.get_format.restype = C.c_int

# Sets the color format of the sink
dll.set_format = dll.IC_SetFormat
dll.set_format.argtypes = [GrabberHandle, C.c_int]
dll.set_format.restype = check_error

# Retrieve whether automatic is enabled for the specifield camera property
dll.get_auto_camera_property = dll.IC_GetAutoCameraProperty
dll.get_auto_camera_property.argtypes = [GrabberHandle,
                                        C.c_int,
                                        C.POINTER(C.c_int)]
dll.get_auto_camera_property.restype = check_error

# Enable or disable automatic for a video propertery
dll.set_auto_camera_property = dll.IC_EnableAutoCameraProperty
dll.set_auto_camera_property.argtypes = [GrabberHandle, C.c_int, C.c_int]
dll.set_auto_camera_property.restype = check_error

# Retrieve exposure absolute values lower and upper limits
dll.get_exposure_range = dll.IC_GetExpAbsValRange
dll.get_exposure_range.argtypes = [GrabberHandle,
                                   C.POINTER(C.c_float),
                                   C.POINTER(C.c_float)]
dll.get_exposure_range.restype = check_error

# Retrieve exposure absolute value
dll.get_exposure = dll.IC_GetExpAbsVal
dll.get_exposure.argtypes = [GrabberHandle, C.POINTER(C.c_float)]
dll.get_exposure.restype = check_error

# Retrieve exposure absolute value
dll.set_exposure = dll.IC_SetExpAbsVal
dll.set_exposure.argtypes = [GrabberHandle, C.c_float]
dll.set_exposure.restype = check_error

# Get the automation state of a video property
dll.get_auto_video_property = dll.IC_GetAutoVideoProperty
dll.get_auto_video_property.argtypes = [GrabberHandle,
                                        C.c_int,
                                        C.POINTER(C.c_int)]
dll.get_auto_video_property.restype = check_error

# Enable or disable automatic for a video propertery
dll.set_auto_video_property = dll.IC_EnableAutoVideoProperty
dll.set_auto_video_property.argtypes = [GrabberHandle, C.c_int, C.c_int]
dll.set_auto_video_property.restype = check_error

# Retrieve the lower and upper limit of a video property
dll.get_video_property_range = dll.IC_VideoPropertyGetRange
dll.get_video_property_range.argtypes = [GrabberHandle,
                                         C.c_uint,
                                         C.POINTER(C.c_long),
                                         C.POINTER(C.c_long)]
dll.get_video_property_range.restype = check_error

# Retrieve the the current value of the specified video property
dll.get_video_property = dll.IC_GetVideoProperty
dll.get_video_property.argtypes = [GrabberHandle,
                                   C.c_uint,
                                   C.POINTER(C.c_long)]
dll.get_video_property.restype = check_error

# Set a video property like brightness, contrast...
dll.set_video_property = dll.IC_SetVideoProperty
dll.set_video_property.argtypes = [GrabberHandle, C.c_uint, C.c_long]
dll.set_video_property.restype = check_error

# Returns the count of available video formats
dll.get_video_format_count = dll.IC_GetVideoFormatCount
dll.get_video_format_count.argtypes = [GrabberHandle]
dll.get_video_format_count.restype = C.c_int

# Return the name of a video format
dll.get_video_format = dll.IC_GetVideoFormat
dll.get_video_format.argtypes = [GrabberHandle, C.c_int]
dll.get_video_format.restype = C.c_char_p

# Sets the video format
dll.set_video_format = dll.IC_SetVideoFormat
dll.set_video_format.argtypes = [GrabberHandle, C.c_char_p]
dll.set_video_format.restype = check_error

# Retrieve the properties of the current video format and sink type
dll.get_image_description = dll.IC_GetImageDescription
dll.get_image_description.argtypes = [GrabberHandle,
                                      C.POINTER(C.c_long),
                                      C.POINTER(C.c_long),
                                      C.POINTER(C.c_int),
                                      C.POINTER(C.c_int)]
dll.get_image_description.restype = check_error

# Check for external trigger support
dll.is_trigger_available = dll.IC_IsTriggerAvailable
dll.is_trigger_available.argtypes = [GrabberHandle]
dll.is_trigger_available.restype = check_error

# Enable or disable the external trigger
dll.enable_trigger = dll.IC_EnableTrigger
dll.enable_trigger.argtypes = [GrabberHandle, C.c_int]
dll.enable_trigger.restype = check_error

# Sends a software trigger to the camera
dll.software_trigger = dll.IC_SoftwareTrigger
dll.software_trigger.argtypes = [GrabberHandle]
dll.software_trigger.restype = C.c_int

# Snaps an image from the live stream
dll.snap_image = dll.IC_SnapImage
dll.snap_image.argtypes = [GrabberHandle, C.c_int]
dll.snap_image.restype = check_error

# Returns a pointer to the image data
dll.get_image_pointer = dll.IC_GetImagePtr
dll.get_image_pointer.argtypes = [GrabberHandle]
dll.get_image_pointer.restype = C.POINTER(C.c_ubyte)

if __name__ == '__main__':
    import time
    from tifffile import imread, imwrite
    camera = Camera(verbose=True, very_verbose=False)

    print('\nTake some pictures:')
    camera.apply_settings(num_images=3, exposure_us=100)
    images = camera.record_to_memory(software_trigger=True)
    imwrite('test0.tif', images, imagej=True)

    print('\nTest video formats:')
    camera.apply_settings(num_images=1, exposure_us=100)
    for vf in camera.video_formats.keys():
        camera.apply_settings(video_format=vf)
        images = camera.record_to_memory()
        imwrite('test_%s.tif'%vf, images, imagej=True)

    print('\nMax fps test:')
    num_images = 10         # enough frames to minimize startup time
    exposure_us = 100       # min exposure
    expected_time_s = num_images * 1e-6 * exposure_us   # naive expectaction
    expected_fps = min(14, num_images / expected_time_s)# 14fps or lower
    camera.apply_settings(num_images=num_images,
                          exposure_us=exposure_us,
                          trigger_enable=False)
    images = np.zeros(
        (camera.num_images, camera.height_px, camera.width_px), 'uint16')
    t0 = time.perf_counter()
    camera.record_to_memory(allocated_memory = images,
                            software_trigger=True) # doesn't seem to slow
    actual_time_s = time.perf_counter() - t0
    imwrite('test1.tif', images, imagej=True)
    print('actual time (s) = %0.2f (expected = %0.6f)'%(
        actual_time_s, expected_time_s))
    actual_fps = num_images / actual_time_s
    print('actual fps = %0.2f (expected = %0.2f)'%(actual_fps, expected_fps))
    # actual fps = 13.78 (expected = 14.00), trigger_enable=False
    # actual fps = 8.42  (expected = 14.00), trigger_enable=True

    print('\nMax fps test -> multiple recordings:')
    iterations = 5
    num_images = 10         # enough frames to minimize startup time
    total_images = iterations * num_images
    exposure_us = 100       # min exposure
    expected_time_s = total_images * 1e-6 * exposure_us # naive expectaction
    expected_fps = min(14, num_images / expected_time_s)# 14fps or lower
    camera.apply_settings(num_images=num_images,
                          exposure_us=exposure_us,
                          trigger_enable=False)
    images = np.zeros(
        (camera.num_images, camera.height_px, camera.width_px), 'uint16')
    t0 = time.perf_counter()
    for i in range(iterations):
        camera.record_to_memory(allocated_memory = images)
    actual_time_s = time.perf_counter() - t0
    imwrite('test2.tif', images, imagej=True)
    print('actual time (s) = %0.2f (expected = %0.6f)'%(
        actual_time_s, expected_time_s))
    actual_fps = total_images / actual_time_s
    print('actual fps = %0.2f (expected = %0.2f)'%(actual_fps, expected_fps))
    # actual fps = 13.27 (expected = 14.00), trigger_enable=False
    # actual fps = 8.72  (expected = 14.00), trigger_enable=True

    print('\nRandom input testing:')
    num_acquisitions = 10 # tested to 1000
    camera.verbose, camera.very_verbose = False, False
    blank_frames, total_latency_ms = 0, 0
    for i in range(num_acquisitions):
        print('\nRandom input test: %06i'%i)
        num_img = np.random.randint(1, 10)
        exp_us  = np.random.randint(100, 100000)
        gain    = np.random.randint(100, 383)
        vid_fmt = np.random.choice(tuple(camera.video_formats.keys()))
        trig_en = bool(np.random.randint(0, 1))
        camera.apply_settings(
            num_images=num_img,
            exposure_us=exp_us,
            gain=gain,
            video_format=vid_fmt,
            trigger_enable=trig_en)
        images = np.zeros(
            (camera.num_images, camera.height_px, camera.width_px), 'uint16')
        t0 = time.perf_counter()
        camera.record_to_memory(allocated_memory=images)
        t1 = time.perf_counter()
        time_per_image_ms = 1e3 * (t1 - t0) / num_img
        latency_ms = time_per_image_ms - 1e-3 * camera.exposure_us
        total_latency_ms += latency_ms
        print("latency (ms) = %0.6f"%latency_ms)
        print("shape of images:", images.shape)
        if i == 0: imwrite('test3.tif', images, imagej=True)
        print("min image values: %s"%images.min(axis=(1, 2)))
        print("max image values: %s"%images.max(axis=(1, 2)))
        for j in range(num_img):
            if min(images.min(axis=(1, 2))) == 0:
                blank_frames += 1
                print('%d blank frames received...'%blank_frames)
    average_latency_ms = total_latency_ms / num_acquisitions
    print("\n -> total blank frames received = %i"%blank_frames)
    print(" -> average latency (ms) = %0.6f"%average_latency_ms)
    # with 1000 iterations:
    # -> total blank frames received = 10 (short exposure + low gain?)
    # -> average latency (ms) = 80.791314

    camera.close()
