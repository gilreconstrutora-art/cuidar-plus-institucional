import json
from channels.generic.websocket import AsyncWebsocketConsumer

class InstitutionEventsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "cuidar_events"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send(text_data=json.dumps({"type": "connection", "status": "connected"}))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def cuidar_event(self, event):
        await self.send(text_data=json.dumps(event["payload"]))
