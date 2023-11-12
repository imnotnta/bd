import os

ld1 = os.listdir('Bitcoin')
ld2 = os.listdir('blockchain')

print(len(set(ld1).intersection(set(ld2))))