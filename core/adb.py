import platform
import os
import sys
import subprocess
import pprint

from core.paths import resource_path
from core.apk import APK

DROID_TOOLS = resource_path("tools")

system = platform.system()

if system == "Windows":
    ANDROID_DEBUG_BRIDGE = os.path.join(DROID_TOOLS, "windows", "adb.exe")
elif system == "Darwin":
    ANDROID_DEBUG_BRIDGE = os.path.join(DROID_TOOLS, "macos", "adb")
elif system == "Linux":
    ANDROID_DEBUG_BRIDGE = os.path.join(DROID_TOOLS, "linux", "adb")
else:
    raise RuntimeError(f"unsupported platform: {system}")

class ADB():

    def __init__(self):
        pass

    def install_apk(self):
        try:
            result = subprocess.run(ANDROID_DEBUG_BRIDGE, "install", APK.path)
        except:
            pass

    def uninstall_apk(self):
        pass

    def list_devices(self):
        pass

    