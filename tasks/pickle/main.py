#!/usr/bin/python3 -u

from base64 import b64decode
import pickle

s = input()
pickle.loads(b64decode(s))
