#!/usr/bin/python3

import os, sys

address = sys.argv[1]

try:
    with os.popen('curl https://devnet-gateway.elrond.com/address/{}/key/454c524f4e44657364745a48452d353061356437 --silent'.format(address)) as fd:
        data = eval(fd.read().strip().replace('null', 'None'))
        print(data)
except:
    data = {'data': {'value': 0}}

value = data['data']['value']
print(value)
if value[0:2] == '12':

    count = eval('0x' + value[2:4])
    slice = value[4 : 4 + 2*count]
    amount = eval('0x' + slice)
    print(slice, amount)
else:
    amount = 0

with open('reserve', mode = 'w') as fd: fd.write(str(amount))

