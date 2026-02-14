import subprocess
import pprint

result = subprocess.run(
    ["../tools/linux/aapt2", "d", "badging", "./app-debug.apk"],
    capture_output=True,
    text=True,
    check=True
)

output = result.stdout
#print(output)

lines = output.splitlines()


info = {
    "package": None,
    "versionCode": None,
    "versionName": None,
    "targetSdkVersion": None,
    "minSdkVersion": None,
    "uses-permission": [],
    "application-label": {}, # each will be formatted like {"locale": Top Cinco}
    "uses-feature": {}, # each has a required, a not required, and implied features ones like {required: ["appshere", "h"], not-required: ["moreappshere", "g"], "implied":["probablyapp", "nah"]}
    "supports-screens": [],
    "supports-any-density": None,
    "locales" : [], # everything except '--_--' (first locale) cause wtf is that
    "densities": [],
    "native-code": []
}

for line in lines:

    if line.startswith("package:"):
        parts = line.split()
        
        for part in parts[1:]:
            key, value = part.split("=")
            value = value.strip("'")
            info[key] = value

    if line.startswith("uses-permission:"):
        # to do: make lines start with uses-permission (get rid of `name=` first) and maybe application-label be put on a list/tuple.
        pass
    elif line.startswith("native-code: "):
        values = line.split(":", 1)[1]
        abis = values.replace("'", "").split()        
        info["native-code"] = abis

pprint.pprint(info)

        
        
