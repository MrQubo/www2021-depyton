#!/usr/bin/env python3

from base64 import b64decode

import secure_pickle as pickle


def login():
    user = input().encode('ascii')
    user = b64decode(user)
    user = pickle.loads(user)
    raise NotImplementedError("Not Implemented QAQ")

if __name__ == '__main__':
    login()
