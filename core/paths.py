import sys
import os

def resource_path(*parts):
    """
    resolve a path to a bundled resource, working both from source
    and from a PyInstaller --onedir/--onefile frozen build.
    """
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # core/paths.py -> core/ -> project root
    return os.path.join(base, *parts)