import os
import sys


print("SOME DIAGNOSTIC VALUES:")

print("\nsys.executable: ", sys.executable)

print("\ncwd: ", os.getcwd())

print("\nsys.path: ", sys.path)
print("\nsys.path again, using separate lines: ")
for p in sys.path:
    print("    ", p)
