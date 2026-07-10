import platform
import os
import subprocess
import pprint
import re
import zipfile
import sys

if getattr(sys, 'frozen', False):
    # running as a PyInstaller bundle
    # sys._MEIPASS points at the bundle's extracted resource root
    DROID_TOOLS = os.path.join(sys._MEIPASS, "tools")
else:
    # running from source
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    DROID_TOOLS = os.path.join(SCRIPT_DIR, "..", "tools")

system = platform.system()

if system == "Windows":
    AAPT2 = os.path.join(DROID_TOOLS, "windows", "aapt2.exe")
elif system == "Darwin":
    AAPT2 = os.path.join(DROID_TOOLS, "macos", "aapt2")
elif system == "Linux":
    AAPT2 = os.path.join(DROID_TOOLS, "linux", "aapt2")
else:
    raise RuntimeError(f"unsupported platform: {system}")

class APK:
    def __init__(self, path):
        self.path = path
        self.icon_bytes = None


        # fixed values
        self.app_name = None
        self.package = None
        self.versionCode = None
        self.versionName = None
        self.minSdkVersion = None
        self.targetSdkVersion = None
        self.supports_any_density = None

        # lists
        self.uses_permissions = []
        self.native_code = []
        self.locales = []
        self.densities = []
        self.supports_screens = []

        # dictionaries
        self.application_labels = {}
        self.uses_features = {
            "used": [],
            "not_required": [],
            "implied": []
        }

    def _parse_quoted_list(self, line):
        values = line.split(":", 1)[1]
        return values.replace("'", "").split()
    
    def _extract_icon_bytes(self, icon_internal_path):
        if not icon_internal_path:
            return None
        
        try:
            with zipfile.ZipFile(self.path, "r") as z:
                return z.read(icon_internal_path)
        except KeyError:
            # path existed in badging output but not actually in the zip, can happen
            return None

    def parse(self):
        print(f"{__file__}: parsing {self.path} with AAPT2 on {system}")

        result = subprocess.run(
            [AAPT2, "d", "badging", self.path],
            capture_output=True,
            text=True,
            check=True
        )

        output = result.stdout
        lines = output.splitlines()
        for line in lines:
            line = line.strip()

            # Package
            if line.startswith("package:"):
                parts = line.split()
                
                for part in parts[1:]:
                    key, value = part.split("=")
                    value = value.strip("'")

                    if key == "name":
                        self.package = value
                    elif key == "versionCode":
                        self.versionCode = value
                    elif key == "versionName":
                        self.versionName = value
            # Uses permission
            if line.startswith("uses-permission:"):
                parts = line.split()

                for part in parts[1:]:
                    key, value = part.split("=")
                    value = value.strip("'")

                    if key == "name":
                        self.uses_permissions.append(value)

            if line.startswith("minSdkVersion:"):
                self.minSdkVersion = line.split(":", 1)[1].strip("'")
            if line.startswith("targetSdkVersion:"):
                self.targetSdkVersion = line.split(":", 1)[1].strip("'")
            if line.startswith("native-code:"):
                self.native_code = self._parse_quoted_list(line)
            if line.startswith("densities:"):
                self.densities = self._parse_quoted_list(line)
            if line.startswith("locales:"):
                self.locales = self._parse_quoted_list(line)
            if line.startswith("supports-screens:"):
                self.supports_screens = self._parse_quoted_list(line)
            if line.startswith("application-label"):
                key, value = line.split(":", 1)
                value = value.strip("'")

                prefix = "application-label"
                locale = key[len(prefix):].lstrip("-")
                if locale == "":
                    locale = "default"
                    self.app_name = value

                self.application_labels[locale] = value

            if line.startswith("uses-feature-not-required:"):
                match = re.search(r"name='([^']*)'", line)
                if match:
                    self.uses_features["not_required"].append(match.group(1))

            elif line.startswith("uses-implied-feature:"):
                match = re.search(r"name='([^']*)' reason='([^']*)'", line)
                if match:
                    self.uses_features["implied"].append({
                        "name": match.group(1),
                        "reason": match.group(2)
                    })

            elif line.startswith("uses-feature:"):
                match = re.search(r"name='([^']*)'", line)
                if match:
                    self.uses_features["used"].append(match.group(1))

            if line.startswith("supports-any-density:"):
                value = line.split(":", 1)[1].strip().strip("'")
                self.supports_any_density = (value == "true")

            if line.startswith("application:"):
                label_match = re.search(r"label='([^']*)'", line)
                icon_match = re.search(r"icon='([^']*)'", line)

                icon_path = icon_match.group(1) if icon_match else None
                self.icon_bytes = self._extract_icon_bytes(icon_path)
# test
if __name__ == "__main__":
    #apk = APK("/Users/ginging/Downloads/app-release.apk")
    apk = APK("/Users/ginging/Downloads/com.opera.browser_15.0.1162.60140-1400060140_minAPI9(armeabi,armeabi-v7a)(nodpi)_apkmirror.com.apk")
    apk.parse()
    pprint.pprint(apk.__dict__)