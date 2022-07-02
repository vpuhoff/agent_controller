import consul
from time import sleep
from tqdm import tqdm
from prometheus_client import start_http_server, Summary

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('consul', type=str, help='consul <host:port>')
args = parser.parse_args()

consul_host = args.consul.split(':')[0]
consul_port = int(args.consul.split(':')[1])
EPOCH_TIME = Summary('epoch_time', 'Time spent to change epoch')

consul_client = consul.Consul(consul_host, consul_port)
print(f'Consul connect to: {args.consul} ...')

def load_current_epoch(consul_client):
    epoch_index, resp = consul_client.kv.get('epoch')
    if not resp:
        resp = {'Value': 0}
    epoch = int(resp['Value'])
    return epoch


epoch = load_current_epoch(consul_client)
start_epoch = epoch
start_http_server(80)
epoch_index = None

with tqdm(initial=epoch) as pbar:
    while True:
        epoch_index, resp = consul_client.kv.get('epoch', index=epoch_index)
        epoch = int(resp['Value'].decode()) if resp else 0
        pbar.update(1)
        dropped = epoch-pbar.n
        drop_percent = round(dropped/(epoch - start_epoch)*100, 4)
        pbar.desc = f"{dropped} dropped\t({drop_percent:4}%)\t{epoch}"
        if pbar.n % 100 == 0:
            dropped = 0
            pbar.n = epoch
