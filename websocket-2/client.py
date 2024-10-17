# client.py
import websockets
import asyncio
import json

async def connect_websocket():
    # Replace with your WebSocket URL from the SAM deployment output
    uri = "wss://your-api-id.execute-api.region.amazonaws.com/Prod"
    
    async with websockets.connect(uri) as websocket:
        # Send a message
        message = {
            "action": "sendmessage",
            "message": "Hello, WebSocket!"
        }
        await websocket.send(json.dumps(message))
        
        # Receive messages
        while True:
            try:
                response = await websocket.recv()
                print(f"Received: {response}")
            except websockets.exceptions.ConnectionClosed:
                print("Connection closed")
                break

# Run the WebSocket client
asyncio.get_event_loop().run_until_complete(connect_websocket())