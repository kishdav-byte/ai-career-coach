import sys, os
INTERP = sys.executable
if sys.executable != INTERP: os.execl(INTERP, INTERP, *sys.argv)
sys.path.append(os.getcwd())

from app import app as application
