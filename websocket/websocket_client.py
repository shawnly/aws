import asyncio
import websockets

async def listen():
    uri = 'wss://your-api-id.execute-api.your-region.amazonaws.com/Prod'
    
    async with websockets.connect(uri) as websocket:
        print("Connected to the WebSocket API Gateway")

        while True:
            # Wait for messages from the WebSocket
            message = await websocket.recv()
            print(f"Received message: {message}")
            # Here you can process the message, e.g., send email based on the message data

# Run the WebSocket client
asyncio.get_event_loop().run_until_complete(listen())
