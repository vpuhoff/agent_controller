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
DROPPED_EPOCH = Summary('dropped_epoch', 'Dropped epoch')

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
cycles = start_epoch

with tqdm(initial=epoch) as pbar:
    while True:
        cycles += 1
        epoch_index, resp = consul_client.kv.get('epoch', index=epoch_index)
        epoch = int(resp['Value'].decode()) if resp else 0
        pbar.update(1)
        dropped = epoch - cycles
        drop_pers = round(dropped / (cycles - start_epoch), 3) if cycles - start_epoch > 0 else 0
        pbar.desc = f"{dropped} dropped\t({drop_pers}%)\t{epoch}"
        if pbar.n % 100 == 0:
            DROPPED_EPOCH.observe(dropped)
            dropped = 0
            cycles = epoch
