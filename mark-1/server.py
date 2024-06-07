import asyncio
import json
import os
from aiohttp import web
import websockets
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

HOST = '192.168.122.50'
PORT = 8000
WEBSOCKET_PORT = 8001

connected_clients = {}  # Dictionary to store client connections by device ID
connected_devices = []  # List to store connected device IDs

# Get the directory where the script is running
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Serve the HTML file
async def handle_index(request):
    return web.FileResponse(os.path.join(BASE_DIR, 'index.html'))

# HTTP server setup
app = web.Application()
app.router.add_get('/', handle_index)

# WebSocket handler
async def websocket_handler(websocket, path):
    device_id = None
    try:
        async for message in websocket:
            data = json.loads(message)
            device_id = data.get('device_id')
            led_name = data.get('led_name')
            status = data.get('status')

            if device_id and led_name and status:
                # Store the websocket connection with the device ID
                connected_clients[device_id] = websocket

                # Add device_id to connected_devices if not already present
                if device_id not in connected_devices:
                    connected_devices.append(device_id)

                # Here you would send a message to the ESP8266 to toggle the LED
                print(f"Device ID: {device_id}, LED: {led_name}, Status: {status}")

                # Send message to the specific connected client
                response = json.dumps({ "led_name": led_name, "status": status })
                if device_id in connected_clients:
                    try:
                        await connected_clients[device_id].send(response)
                    except (ConnectionClosedError, ConnectionClosedOK) as e:
                        print(f"Error sending message to {device_id}: {e}")
                        if device_id in connected_clients:
                            del connected_clients[device_id]
                            if device_id in connected_devices:
                                connected_devices.remove(device_id)
                else:
                    print(f"No connected client with device ID {device_id}")
    except websockets.ConnectionClosed:
        print("Client disconnected")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        if device_id in connected_clients and connected_clients[device_id] == websocket:
            del connected_clients[device_id]
            if device_id in connected_devices:
                connected_devices.remove(device_id)

# Start the HTTP and WebSocket servers
async def start_servers():
    # Start HTTP server
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, HOST, PORT)
    await site.start()
    print(f"HTTP server running on http://{HOST}:{PORT}")

    # Start WebSocket server
    websocket_server = await websockets.serve(websocket_handler, HOST, WEBSOCKET_PORT)
    print(f"WebSocket server running on ws://{HOST}:{WEBSOCKET_PORT}")

    # Simulate sending JSON packets to connected devices periodically
    async def send_json_to_devices():
        while True:
            for device_id in connected_devices:
                if device_id in connected_clients:
                    message = json.dumps({
                        "device_id": device_id,
                        "message": "This is a periodic update"
                    })
                    try:
                        await connected_clients[device_id].send(message)
                        print(f"Sent to {device_id}: {message}")
                    except (ConnectionClosedError, ConnectionClosedOK) as e:
                        print(f"Error sending periodic message to {device_id}: {e}")
                        if device_id in connected_clients:
                            del connected_clients[device_id]
                            if device_id in connected_devices:
                                connected_devices.remove(device_id)
            await asyncio.sleep(10)  # Send every 10 seconds

    await asyncio.gather(asyncio.Future(), send_json_to_devices())  # Run servers and the periodic sender

# Run the servers
asyncio.run(start_servers())
