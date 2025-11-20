import sys
import os

print("Current working directory:", os.getcwd())
print("sys.path:", sys.path)

try:
    import json
    print("json module:", json)
    print("json file:", json.__file__)
except Exception as e:
    print("Error importing json:", e)

try:
    import flask
    print("flask module:", flask)
    print("flask file:", flask.__file__)
except Exception as e:
    print("Error importing flask:", e)
