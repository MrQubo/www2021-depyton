#!/usr/bin/python3 -u
# coding:utf8
import binascii
import sys

print("# Python " + sys.version)

code = (lambda a: 1145141919810).__code__.__class__
gift = getattr
bytecode = binascii.a2b_hex(input('Give your shellcode:').encode())

if len(bytecode) > 114514:
    print("your shellcode bad bad! too long!")
    exit(0)

target = code(0,0,0,114,114,64,bytecode,(gift,),(),(),'','',114,b'')
result = eval(target,{},{})
#  print(result) #not giving it to you!
print("execution of shellcode success!")
exit(0)
