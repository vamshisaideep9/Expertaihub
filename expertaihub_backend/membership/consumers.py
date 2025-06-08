# chats/consumers.py

import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer


class UsageConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer that listens for "usage" broadcasts for a given user.
    Each user joins a group named f"usage_{user_id}".
    Whenever the backend broadcasts a new usage count to that group,
    this consumer will forward it to the client.
    """

    async def connect(self):
        # The URL route will be /ws/usage/<user_id>/
        self.user_id = self.scope["url_route"]["kwargs"]["user_id"]
        self.group_name = f"usage_{self.user_id}"

        # Join group "usage_{user_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # Leave the group on disconnect
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # This method will be called by group_send
    async def usage_update(self, event):
        await self.send_json({"count": event["count"]})