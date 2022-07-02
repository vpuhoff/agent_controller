import consul
from time import sleep
from tqdm import tqdm
from prometheus_client import start_http_server, Summary
import threading
import argparse
import socketio
from aiohttp import web
import asyncio


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

def refresh_epoch(consul_client):
    async def refresh(consul_client):
        epoch = load_current_epoch(consul_client)
        start_epoch = epoch
        cycles = epoch
        epoch_index = None
        while True:
            cycles += 1
            epoch_index, resp = consul_client.kv.get('epoch', index=epoch_index)
            epoch = int(resp['Value'].decode()) if resp else 0
            dropped = epoch - cycles
            DROPPED_EPOCH.observe(dropped)
            dropped = 0
            cycles = epoch
            await sio.emit('new epoch', {'epoch': epoch})
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(refresh(consul_client))
    loop.close()

sio = socketio.AsyncServer(async_mode='aiohttp')
app = web.Application()
sio.attach(app)


start_http_server(80)


@sio.on('*')
async def catch_all(event, sid, data):
    print(event, data)

@sio.event
async def connect(sid, environ, auth):
    print('connect ', sid)
    await sio.save_session(sid, {'username': sid})


@sio.event
async def disconnect(sid):
    print('disconnect ', sid)


async def run_server():
    global epoch
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, port=8000)
    await site.start()
    while True:
        await asyncio.sleep(0.01)


thread = threading.Thread(target=refresh_epoch, args=(consul_client,))
thread.start()


loop = asyncio.get_event_loop()
tasks = [
    loop.create_task(run_server())
]

loop.run_until_complete(asyncio.wait(tasks))
loop.close()
