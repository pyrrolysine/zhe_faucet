#!/usr/bin/python3

sender = [
    'erd13g4yqs0tn8cvjjzwdaxvpn5dmxlrmk2nfv6s7xvph7qa7dql9l4q6dyglv',
    'erd173jn7jhq6xl0zrgnlap4cv0mwjgd3rtjz337kjrh9fff62zr456sc5t0ks',
][0]

WALLET = '/erd/wallets/' + sender + '.pem'

divisor = 10

print('Content-Type: text/html\n\n<html>')

import os

user = os.getenv('USER')

try:
    query = os.getenv('QUERY_STRING').split('&')
except:
    query = []

try:
    os.system('./zhe-amount-checker.py {} &>/dev/null'.format(sender))
except:
    pass

param = {}
for kv in query:
    if '=' in kv:
        p = kv.find('=')
        k, v = kv[:p], kv[p + 1:]
        param[k] = v

verbose = (user == 'lin') or ('test' in param)

def read_int(path):
    with open(path) as fd:
        return int(fd.read().strip())

with open('status') as fd:
    status = fd.read()

txs = []
for line in status.split('\n'):
    try:
        tx = line.strip()
        if len(tx) != 0:
            txs.append(tx)
    except:
        pass

status = ''

pending = []

for tx in txs:
    with os.popen('curl https://devnet-gateway.elrond.com/transaction/{} --silent'.format(tx)) as pipe:
        try:
            data = eval(pipe.read().strip())
            if data['data']['transaction']['status'] == 'pending':
                pending.append(tx)
                status = 'Pending tx: ' + tx
        except:
            pass

if len(txs) != 0:
    with open('status', mode = 'w') as fd:
        fd.write('\n'.join(pending) + '\n')

if 'wallet' in param and len(status) == 0:
    wallet = param['wallet']
    
    total = read_int('total')
    rsvdt = read_int('reserve')
    amount = rsvdt // divisor

    token = '5A48452D353061356437'

    xamount = hex(amount)[2:]
    while len(xamount) & 1 != 0: xamount = '0' + xamount

    if amount > 0:
        rsvdt -= amount
        with open('reserve', mode = 'w') as fd: fd.write(str(rsvdt))
        try:
            end = '&>/dev/null' if not verbose else ' 2>&1'

            os.system('bash -c \'WALLET_PEM=' + WALLET + ' ./txsign.py sender="{}" receiver="{}" value=0 data=ESDTTransfer@{}@{} gas=1000000 post=yes >output\''.format(sender, wallet, token, xamount))
            with open('output') as pipe: data = eval(pipe.read().strip())
            tx = data['data']['txHash']
            with open('status', mode = 'w') as fd: fd.write(tx + '\n')
            os.system('./zhe-amount-checker.py {} {}'.format(sender, end))
            status = '{} sent to {}, tx hash:<br/>{}'.format('%.3f'%(amount / 1000), wallet, tx)
        except BaseException as e:
            import traceback
            status = 'Error: ' + str(e) + traceback.format_exc()

elif len(status) != 0:
    status = 'Please refresh this page after a while'
else:
    status = '''\
    <script>
        const reqZhe = () => {
            const wallet = document.getElementById("address").value
            window.location = "/cgi-bin/zhe_faucet/zhe.py?wallet=" + wallet
        }
    </script>
    <a href="javascript:reqZhe()" enabled="$ENABLE_SEND;">Request</a>
    '''


def fetch_fields():
    data = {}
    data['STATUS'] = status
    data['ENABLE_SEND'] = 'enabled' if len(status) == 0 else 'disabled'
    data['AMOUNT_FREE'] = read_int('reserve') / 1000
    data['AMOUNT_SENT'] = read_int('total') / 1000 - data['AMOUNT_FREE']
    return data


def fill(string):
    for k, v in fetch_fields().items():
        if isinstance(v, float):
            v = ('%.3f' % v).rjust(14, '\u3000')
        else:
            v = str(v)
        string = string.replace('$' + k + ';', v).replace('\u3000', '&nbsp;')
    return string

with open('template.html', mode = 'r', encoding = 'utf-8') as source:
    html = source.read()

print(fill(html))


