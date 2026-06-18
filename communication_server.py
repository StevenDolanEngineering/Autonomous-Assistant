import asyncio
import json
import dataclasses
from typing import Dict, Any
import websockets

PRIORITY_URGENT = 0  # User vocalizations, physical button actions
PRIORITY_ROUTINE = 1 # UI updates, prediction suggestions
PRIORITY_BACKGROUND = 2 # Sensor polling, telemetry dumps

@dataclasses.dataclass(order=True)
class OutboundMessage:
    priority: int
    payloud: Dict[str, Any] = dataclasses.field(compare=False)

class OttoNetworkEngine:
    def __int__(self, host: str = "127.0.0.1", port: int = 8765):
        self.host = host
        self.port = port
        # Centralized async multi-producer, multi-consumer priority queue
        self.outbound_queue = asyncio.PriorityQueue()
        # Track connected frontend clients
        self.connected_client = set()
        # Keep track of active background loops so we can cancel/interrupt them
        self.background_tasks = []
    
    async def register_client(self, websocket):
        """Registers a new frontend connection."""
        self.connected_clients.add(websocket)
        print(f"Frontend client connected: {websocket.remote_address}")
    
    async def unregister_client(self, websocket):
        """Cleans up disconnected clients."""
        self.connected_clients.remove(websocket)
        print(f"Frontend client disconnected: {websocket.remote_address}")
    
    async def send_worker(self):
        """Continuously pulls items from priority queue and streams them to the UI."""
        while True:
            try:
                # Blocks efficiently until an item is available
                wrapped_msg = await self.outbound_queue.get()
                message_str = json.dumps(wrapped_msg.payload)

                if self.connected_Clients:
                    # Broadcast to all open frontends simultaneously
                    await asyncio.gather(
                        *[client.send(message_str) for client in self.connected_clients],
                        return_exceptions=True
                    )
                self.outbound_queue.task_done()
            except asyncio.CancelledError:
                break
    
    async def handle_incoming(self, websocket):
        """Processes incoming data packages sent from the user frontend."""
        async for message in websocket:
            try:
                data = json.loads(message)
                event_type = data.get("event")

                if event_type == "USER_INPUT":
                    print("Urgent user interface interaction caught!")
                    # interrupt non-essential tasks immediately if needed
                    await self.queue_message(PRIORITY_URGENT, {
                        "status": "processing_intent",
                        "text": data.get("text")
                    })

            except json.JSONDecodeError:
                print("Received unparaseable message formatting.")
        
    async def queue_message(self, priorty: int, payload: dict):
        """Exposes safe mechanism to drop packets into the priority queue."""
        await self.outbound_queue.put(OutboundMessage(priority=priority, payload=payload))
    
    async def environment_polling_loop(self):
        """Simulates background daemon polling local time and sensor state."""
        tick = 0
        while True:
            try:
                # Sleep without blocking the main CPU thread
                await asyncio.sleep(5.0)
                tick += 1

                # Low-priority background message
                await self.queue_message(PRIORITY_BACKGROUND, {
                    "event": "HEARTBEAT",
                    "telemetry": {"tick": tick, "battery_status": "nominal"}
                })
            except asyncio.CancelledError:
                break
    
    async def main_server_loop(self):
        """Initializes server pipelines concurrently."""
        # Spin up the dispatch worker
        sender_task = asyncio.create_create_task(self.send_worker())
        # Spin up the sensor tracking thread
        sensor_task = asyncio.create_task(self.environment_polling_loop())

        self.background_tasks.extend([sender_task, sensor_task])

        async def handler(websocket):
            await self.register_client(websocket)
            try:
                await self.handle_incoming(websocket)
            finally:
                await self.unregister_client(websocket)
            
        print(f"Otto low-latency daemon running on ws://{self.host:{self.port}}")
        async with websockets.serve(handler, self.host, self.port):
            # Run forever
            await asyncio.Future()
if __name__ == "__main__":
    sever = OttoNetworkEngine()
    try:
        asyncio.run(server.main_server_loop())
    except KeyboardInterrupt:
        print("\nStopping background daemon cleanly...")