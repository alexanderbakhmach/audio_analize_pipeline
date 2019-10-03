import asyncio
import websockets
from app import handle_connections
from app import config


try:
    # Start serving web-socket server
    start_server = websockets.serve(handle_connections, config['HOST'], config['PORT'])
    print(f'Server starting on port {config["PORT"]} on host {config["HOST"]} '
          f'whole url ws://{config["HOST"]}:{config["PORT"]}')
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
except KeyboardInterrupt:
    print('Key pressed. Server will stop')
