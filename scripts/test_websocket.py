import asyncio
import websockets

job_id = input('Job ID: ')

async def test_websocket():
    uri = f"ws://localhost:7001/api/v1/ws/job/progress?job_id={job_id}"
    async with websockets.connect(uri) as websocket:
        await websocket.send("Hello WebSocket!")
        response = await websocket.recv()
        print(f"Response from server: {response}")


asyncio.get_event_loop().run_until_complete(test_websocket())
