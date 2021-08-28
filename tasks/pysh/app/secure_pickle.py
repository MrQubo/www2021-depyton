#!/usr/bin/python

import pickle, io


whitelist = ['sys']

# See https://docs.python.org/3.7/library/pickle.html#restricting-globals
class RestrictedUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if module not in whitelist or '.' in name:
            raise KeyError('The pickle is spoilt :(')
        return pickle.Unpickler.find_class(self, module, name)

def loads(s):
    """Helper function analogous to pickle.loads()."""
    return RestrictedUnpickler(io.BytesIO(s)).load()

def load(b):
    """Helper function analogous to pickle.load()."""
    return RestrictedUnpickler(b).load()

dumps = pickle.dumps
