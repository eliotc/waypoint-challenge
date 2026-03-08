"""
Quick WebSocket smoke test — sends a text message to the live session
and prints everything that comes back for 15 seconds.
Usage: python test_ws.py
"""
import asyncio
import json
import uuid
import websockets

WS_URL = f"ws://localhost:8000/ws/{uuid.uuid4()}"
TEXT_MSG = json.dumps({"type": "text", "content": "Hi, what courses does Kingsford University offer in engineering?"})

async def main():
    print(f"Connecting to {WS_URL}")
    async with websockets.connect(WS_URL) as ws:
        print("Connected. Sending text message...")
        await ws.send(TEXT_MSG)

        print("Waiting for responses (15s)...\n")
        try:
            async with asyncio.timeout(15):
                async for msg in ws:
                    if isinstance(msg, bytes):
                        print(f"[AUDIO] {len(msg)} bytes")
                    else:
                        data = json.loads(msg)
                        print(f"[TEXT]  {json.dumps(data, indent=2)}")
        except TimeoutError:
            print("\nTimeout — done.")

asyncio.run(main())
