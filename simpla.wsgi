import sys
import os
APP_PATH = "/var/www/simpla"
sys.path.insert(0, APP_PATH)
os.chdir(APP_PATH)
# flaskapp.py is inside APP_PATH folder.
from simpla import app as application
