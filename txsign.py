#!/usr/bin/python3


import os
import sys

verbose = 'verbose=' in ' '.join(sys.argv)

import nacl.signing
import nacl.encoding


def get(url):
    with os.popen('curl --silent "{}"'.format(url)) as pipe:
        return eval(pipe.read().strip())

def resolve_network(cfg):
    if 'net' in cfg and cfg['net'] == 'real':
        cfg['root'] = 'https://gateway.elrond.com'
    else:
        cfg['root'] = 'https://devnet-gateway.elrond.com'


HEX = '0123456789abcdef'

def fetch_blockchain_params(cfg, tx):
    resolve_network(cfg)

    sender = tx['sender'].lower()
    tx['sender'] = sender
    #tx['senderUsername'] = nacl.encoding.Base64Encoder.encode(sender.encode('ascii')).decode('ascii')

    if 'receiver' in tx and len(tx['receiver']) != 0:
        tx['receiver'] = tx['receiver'].lower()
    else:
        tx['receiver'] = tx['sender']

    if 'value' in tx:
        value = str(int(eval(tx['value'])))
        if len(value) == 0 or int(value) < 0: tx['value'] = '0'
        else: tx['value'] = value

    nonce = get(cfg['root'] + '/address/' + sender + '/nonce')['data']['nonce']
    tx['nonce'] = nonce

    net = get(cfg['root'] + '/network/config')['data']['config']
    tx['version'] = int(net['erd_min_transaction_version'])
    tx['chainID'] = net['erd_chain_id'] if 'chain' not in cfg else cfg['chain']
    tx['gasLimit'] = int(net['erd_min_gas_limit'])
    if 'gas' in cfg and int(cfg['gas']) > tx['gasLimit']:
        tx['gasLimit'] = int(cfg['gas'])
    tx['gasPrice'] = int(net['erd_min_gas_price'])

    if len(tx['data']) != 0: tx['data'] = nacl.encoding.Base64Encoder.encode(tx['data'].encode('utf-8')).decode('ascii')

    FIELDS = ['nonce', 'value', 'receiver', 'sender', 'senderUsername', 'gasPrice', 'gasLimit', 'data', 'chainID', 'version']
    tx = {k: v for k, v in sorted(tx.items(), key = lambda kv: FIELDS.index(kv[0]))}
    tx['signature'] = sign(tx)

    if 'post' in args:
        post = serialize(tx)
        txurl = cfg['root'] + '/transaction/send'
        cmd = 'curl --silent "{}" -H "Content-Type: application/json" -d \'{}\''.format(txurl, post)

        if verbose:
            print('POST data:')
            print(post)
            print()
            print('cURL command:')
            print(cmd)

        if args['post'] == 'yes':
            if verbose:
                print()
                print('Blockchain result:')
            with os.popen(cmd) as pipe: print(pipe.read())
    return tx


def sign(tx):
    with open(os.getenv('WALLET_PEM'), mode = 'r') as pem:
        lines = [
            line.strip()
            for line in pem.readlines()
            if '-'  not in line
        ]

    seed_pkey = ''.join(lines)
    seed_pkey = nacl.encoding.Base64Encoder.decode(seed_pkey)
    pkey = seed_pkey[:len(seed_pkey) // 2].decode('ascii')

    signer = nacl.signing.SigningKey(pkey, encoder = nacl.encoding.HexEncoder)
    signature = signer.sign(serialize(tx).encode('ascii'),
                            encoder = nacl.encoding.HexEncoder)

    return signature[:128].decode('ascii')


def serialize(kv):
    kv = {k: v for k, v in kv.items()}
    if 'data' in kv and len(kv['data']) == 0: del kv['data']

    return (
        '{'
        + ','.join('"{}":{}'.format(k, tx_repr(v)) for k, v in kv.items())
        + '}'
    )

def tx_repr(x):
    if isinstance(x, str):
        return '"' + x + '"'
    elif isinstance(x, int):
        return str(x)
    else:
        raise ValueError()


args = {}

for arg in sys.argv[1:]:
    assert '=' in arg
    p = arg.find('=')
    k, v = arg[:p], arg[p+1 :]
    assert k not in args
    args[k] = v

TXDATA = {'value': '', 'receiver': '', 'sender': '', 'data':''}

for k in TXDATA:
    if k in args:
        TXDATA[k] = args[k]


TXDATA = fetch_blockchain_params(args, TXDATA)


