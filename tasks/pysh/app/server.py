#!/usr/bin/python

from base64 import b64decode
import sys

import secure_pickle as pickle


print("# Python " + sys.version)


def login():
    user = input().encode('ascii')
    user = b64decode(user)
    user = pickle.loads(user)
    raise NotImplementedError("Not Implemented QAQ")

if __name__ == '__main__':
    login()
