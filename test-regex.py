import re

r = raw_input("Regex : ")
s = raw_input("String: ")
print(r + ' :: ' + s)
print(None != re.match(r, s))
