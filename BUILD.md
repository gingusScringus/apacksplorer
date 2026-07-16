# Dependencies
>[!NOTE] Make sure you have these specific dependencies if you want to build for older platforms! Newer versions of dependencies may not work in older OSes.

- Python 3.8.20
- PyQt5 5.15.10
- etc according to requirements.txt

# Building

## Setting up the environment
Simply run `setup_env.sh` (macOS/Linux) or `setup_env.ps1` (Windows) to set up the virtual environment for the program. Activate the venv to start.

## Build the program
Run `produce.sh` or `produce.ps1` to build the program with PyInstaller.

## Directory Glossary
- `.venv/`: Python virtual environment
- `assets/`: icons, images, resources
- `core/`: core scripts to run (i.e. apk and adb)
- `forms/`: Qt5 forms and dialogs
- `gui/`: scripts for handling Qt5 operations and main window
- `tools/`: android platform/build tools 
- `produce.sh`: PyInstaller build script
- `setup_env.sh`: automatic Python environment setup for Unix-based OSes (i.e. Linux, macOS)
- `setup_env.psh`: ditto, for Windows Powershell
- `requirements.txt`: list of dependencies for the program
- `main.py`: program's entry point.

