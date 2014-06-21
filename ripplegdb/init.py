#################################### IMPORTS ###################################

# Std Libs
import functools
import os
import re
import struct
import sys
import threading
import time

from pprint import pprint as pp

# Gdb
import gdb.printing
import gdb.types
import collections

# Ripple ;)
from ripplegdb.base58 import base58_check_encode
from ripplegdb.helpers import reload_module, read_value
from ripplegdb.funcs import func
from ripplegdb.commands import command

################################### CONSTANTS ##################################

DEV = True

#################################### HELPERS ###################################

ddir = lambda o: [d  for d in dir(o) if True or not d.startswith('__')]
pd   = lambda o: pp(ddir(o))
gt   = gdb.types

def D(o):
    print('---------------------------------------------------------')
    print(type(o))
    for a in ddir(o):
        print(a, getattr(o, a))

    print('---------------------------------------------------------')