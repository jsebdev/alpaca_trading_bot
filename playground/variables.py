import sys


print('>>>>> variables.py:4 "sys.path"')
print(sys.path)


from a import a_function


print('>>>>> variables.py:1 "__name__"')
print(__name__)

print('>>>>> variables.py:4 "__file__"')
print(__file__)

a_function()
