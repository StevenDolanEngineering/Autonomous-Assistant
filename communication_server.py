import asyncio
import json
import dataclasses
from typing import Dict, Any
import websockets

# Import local optimization and prediction layers
from assistant_engine import process_aac_intent, fallback_system

# Priority tiers for the AAC device
PRIORITY_URGENT = 0  # User vocalizations, physical button actions
PRIORITY_ROUTINE = 1 # UI updates, prediction suggestions
PRIORITY_BACKGROUND = 2 # Sensor polling, telemetry dumps

@dataclasses.dataclass(order=True)
class OutboundMessage:
    priority: int
    payload: Dict[str, Any] = dataclasses.field(compare=False)

class OttoNetworkEngine:
    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        self.host = host
        self.port = port
        # Centralized async multi-producer, multi-consumer priority queue
        self.outbound_queue = asyncio.PriorityQueue()
        # Track connected frontend clients
        self.connected_clients = set()
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

                if self.connected_clients:
                    # Broadcast to all open frontends simultaneously
                    await asyncio.gather(
                        *[client.send(message_str) for client in self.connected_clients],
                        return_exceptions=True
                    )
                self.outbound_queue.task_done()
            except asyncio.CancelledError:
                break
    
    async def handle_incoming(self, websocket):
        """Handles incoming character/word typing events from the user interface."""
        async_loop = asyncio.get_running_loop()

        async for message in websocket:
            try:
                data = json.loads(message)
                event_type = data.get("event")

                # Triggers whenever user types or modifies characters/words
                if event_type == "LIVE_TYPING_UPDATE":
                    current_text = data.get("text", "").strip()
                    if not current_text:
                        continue

                    print(f"Keystroke event caught: '{current_text}'")

                    # RUN LOCAL INTELLIGENCE IN A SEPARATE THREAD
                    # This stops the LLM generation loop from blocking network activity
                    prediction_result = await async_loop.run_in_executor(
                        None, process_aac_intent, current_text
                    )

                    # Package and inject prediction payloads to the routine priority loop
                    await self.queue_message(PRIORITY_ROUTINE, {
                        "event": "PREDICTION_UPDATE",
                        "data": prediction_result
                    })

                # Triggers when a user confirms their final phrase statement
                elif event_type == "PHRASE_COMPLETED":
                    completed_text = data.get("text", "").strip()
                    if completed_text:
                        # Feed back into adaptive learning corpus matric
                        fallback_system.learn_completed_phrase(completed_text)

            except json.JSONDecodeError:
                print("Received unparaseable JSON stream payload.")
        
    async def queue_message(self, priority: int, payload: dict):
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
        sender_task = asyncio.create_task(self.send_worker())
        # Spin up the sensor tracking thread
        sensor_task = asyncio.create_task(self.environment_polling_loop())

        self.background_tasks.extend([sender_task, sensor_task])

        async def handler(websocket):
            await self.register_client(websocket)
            try:
                await self.handle_incoming(websocket)
            finally:
                await self.unregister_client(websocket)
            
        print(f"Otto live network layer running on ws://{self.host}:{self.port}")
        async with websockets.serve(handler, self.host, self.port):
            # Run forever
            await asyncio.Future()
if __name__ == "__main__":
    server = OttoNetworkEngine()
    try:
        asyncio.run(server.main_server_loop())
    except KeyboardInterrupt:
        print("\nStopping background daemon cleanly...")