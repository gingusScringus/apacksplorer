import platform
import os
import subprocess
import pprint
import re
import zipfile
import sys
import yaml
import hashlib

if getattr(sys, 'frozen', False):
    # running as a PyInstaller bundle
    # sys._MEIPASS points at the bundle's extracted resource root
    DROID_TOOLS = os.path.join(sys._MEIPASS, "tools")
    bundle_candidates = []

    # PyInstaller can place data files in different locations depending on the bundle type.
    base_dirs = [sys._MEIPASS, os.path.dirname(sys._MEIPASS)]

    # macOS app bundles commonly store bundled data under Contents/Resources rather than Contents/Frameworks.
    if sys.platform == "darwin":
        contents_dir = os.path.dirname(sys._MEIPASS)
        base_dirs.extend([
            os.path.join(contents_dir, "Resources"),
            os.path.join(contents_dir, "Resources", "core"),
            os.path.join(contents_dir, "Frameworks"),
            os.path.join(contents_dir, "Frameworks", "core"),
        ])

    for base in base_dirs:
        bundle_candidates.extend([
            os.path.join(base, "core", "android_versions.yaml"),
            os.path.join(base, "android_versions.yaml"),
        ])

    _VERSIONS_PATH = next((p for p in bundle_candidates if os.path.exists(p)), bundle_candidates[0])
else:
    # running from source
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    DROID_TOOLS = os.path.join(SCRIPT_DIR, "..", "tools")
    _VERSIONS_PATH = os.path.join(SCRIPT_DIR, "android_versions.yaml")

system = platform.system()

if system == "Windows":
    AAPT2 = os.path.join(DROID_TOOLS, "windows", "aapt2.exe")
elif system == "Darwin":
    AAPT2 = os.path.join(DROID_TOOLS, "macos", "aapt2")
elif system == "Linux":
    AAPT2 = os.path.join(DROID_TOOLS, "linux", "aapt2")
else:
    raise RuntimeError(f"unsupported platform: {system}")


INVALID_FILENAME_CHARS = '\\/:*?"<>|'

with open(_VERSIONS_PATH, 'r', encoding='utf-8') as f:
    ANDROID_VERSIONS = yaml.safe_load(f)

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
        self.maxSdkVersion = None
        self.targetSdkVersion = None
        self.compileSdkVersion = None
        self.supports_any_density = None
        self.opengl_es_version = None

        # lists
        self.uses_permissions = []
        self.native_code = []
        self.locales = []
        self.densities = []
        self.supports_screens = []

        # dictionaries
        self.application_labels = {}
        self.uses_features = {
            "uses": [],
            "not_required": [],
            "implied": []
        }

        # bools
        self.supports_android = True # practically useless but whatever
        self.supports_android_tv = False
        self.supports_wear_os = False
        self.supports_android_auto = False
        self.uses_opengles = False
        self.uses_vulkan = False

    def _parse_quoted_list(self, line):
        values = line.split(":", 1)[1]
        return values.replace("'", "").split()
    
    def _parse_quoted_string(self, line):
        value = line.split(":", 1)[1]
        return value.strip("'")
    
    def _parse_between(self, text, start, end):
        """extract substring between two markers, or '' if not found"""
        try:
            after_start = text.split(start, 1)[1]
            return after_start.split(end, 1)[0]
        except IndexError:
            return ''
    
    def _extract_icon_bytes(self, icon_internal_path):
        if not icon_internal_path:
            return None
        
        try:
            with zipfile.ZipFile(self.path, "r") as z:
                return z.read(icon_internal_path)
        except KeyError:
            # path existed in badging output but not actually in the zip, can happen
            return None
            
    def _gles_version_decode(self, raw):
        """
        aapt2 reports gl-es version as a packed hex value, e.g. '0x30001'
        high bits = major version, low 16 bits = minor version.
        '0x30001' -> major=3, minor=1 -> "3.1"
        """
        if not raw:
            return ''

        if raw.lower().startswith('0x'):
            value = int(raw, 16)
            major = value >> 16
            minor = value & 0xFFFF
            return f"{major}.{minor}"

        # not hex, just return as-is (some old/weird apks might not use the packed format)
        return raw

    def _compute_sha256(self):
        sha256 = hashlib.sha256()
        with open(self.path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    def parse(self):
        print(f"{__file__}: parsing {self.path} with AAPT2 on {system}")
        try:
            result = subprocess.run(
                [AAPT2, "d", "badging", self.path],
                capture_output=True,
                text=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            raise ValueError(f"'{os.path.basename(self.path)}' isn't a valid apk") from e
        except FileNotFoundError as e:
            raise RuntimeError("aapt is borked. might be a program bug.") from e
        output = result.stdout
        self.sha256 = self._compute_sha256()
        
        lines = output.splitlines()
        for line in lines:
            line = line.strip()

            # Package line
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
                    elif key == "compileSdkVersion":
                        self.compileSdkVersion = value
            # Uses permission
            if line.startswith("uses-permission:"):
                parts = line.split()

                for part in parts[1:]:
                    key, value = part.split("=")
                    value = value.strip("'")

                    if key == "name":
                        self.uses_permissions.append(value)

            if line.startswith("minSdkVersion:"):
                self.minSdkVersion = self._parse_quoted_string(line)
            if line.startswith("maxSdkVersion:"):
                self.maxSdkVersion = self._parse_quoted_string(line)
            if line.startswith("targetSdkVersion:"):
                self.targetSdkVersion = self._parse_quoted_string(line)
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
                    self.uses_features["uses"].append(match.group(1))

            if line.startswith("supports-any-density:"):
                value = line.split(":", 1)[1].strip().strip("'")
                self.supports_any_density = (value == "true")

            if line.startswith("application:"):
                label_match = re.search(r"label='([^']*)'", line)
                icon_match = re.search(r"icon='([^']*)'", line)

                icon_path = icon_match.group(1) if icon_match else None
                self.icon_bytes = self._extract_icon_bytes(icon_path)

            if line.startswith("leanback-launchable-activity"):
                self.supports_android_tv = True

            if line.startswith("uses-feature:"):
                name = self._parse_between(line, "name='", "'")
                self.uses_features['uses'].append(name)

                if name == 'android.hardware.type.watch':
                        self.supports_wear_os = True
                if name == 'android.hardware.vulkan.version' or name.startswith('android.hardware.vulkan'):
                        self.uses_vulkan = True

            if line.startswith("meta-data:"):
                if self._parse_between(line, "name='", "'") == 'com.google.android.gms.car.application':
                    self.supports_android_auto = True

            if line.startswith("uses-gl-es:"):
                raw = self._parse_between(line, "'", "'")
                self.opengl_es_version = self._gles_version_decode(raw)
                self.uses_opengles = True


    def format_sdk_level(self, sdk_number):
        if not sdk_number:
            return ''

        entry = ANDROID_VERSIONS.get(int(sdk_number))
        if entry is None:
            return f"API {sdk_number}"

        # return f"API {sdk_number} (Android {entry['version']} {entry['name']})"
        return f"Android {entry['version']} {entry['name']} (API {sdk_number})"
    
    def format_filename(self, pattern):
        replacements = {
            '%label%': self.app_name or '',
            '%version%': self.versionName or '',
            '%build%': self.versionCode or '',
            '%package%': self.package or '',
            '%min%': self.minSdkVersion or '',
            '%target%': self.targetSdkVersion or '',
            '%max%': self.maxSdkVersion or '',
            '%compile%': self.compileSdkVersion or '',
            '%abis%': ' '.join(self.native_code),
            '%screens%': ' '.join(self.supports_screens),
            '%dpis%': ' '.join(self.densities),
        }

        result = pattern
        for placeholder, value in replacements.items():
            result = result.replace(placeholder, value)

        return result

    def sanitize_filename(self, name, replacement=' '):
        for char in INVALID_FILENAME_CHARS:
            name = name.replace(char, replacement)
        return name.strip()


if __name__ == "__main__":
    apk = APK("/Users/ginging/Downloads/app-release.apk")
    apk.parse()
    pprint.pprint(apk.__dict__)