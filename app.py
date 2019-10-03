from sources import IbmSttService
from sources import IbmTtsService
from sources import AnswerService
from sources import Client
import json

#  Load main config
with open('config.json', 'r') as f:
    config = json.load(f)


async def handle_connections(websocket, _):
    """Handle and serve new web-socket connection

    Create all services to analise input audio stream from client
    and pass them as array to manager which wire them and execute
    one in each unique process.

    Args:
        websocket (Websocket): the websocket connection instance
                                see https://websockets.readthedocs.io/en/stable/
        _ (str): the socket connection path
    """

    # Initialize all services and pass them to manager
    stt_service = IbmSttService(config['STT_IBM_KEY'], config['STT_IBM_URL'])
    tts_service = IbmTtsService(config['TTS_IBM_KEY'], config['TTS_IBM_URL'])
    answer_service = AnswerService()
    services = [stt_service, answer_service, tts_service]
    client = Client(services)

    # Lopping though incoming data via socket connection
    async for message in websocket:

        # Send incoming pack of data to the input of wired services chain in manager (Client)
        client.send(message)

        # If services processes do not running then run them
        if not client.running:
            client.running = True
            client.start()

        # Receive the output data of the services chain
        data = client.receive(False)

        # If there are no data then pass 0 bytes
        if not data:
            data = b''

        # Send that data as response to the client
        await websocket.send(data)
