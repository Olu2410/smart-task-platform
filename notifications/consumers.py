#notifications/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Notification


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Get user ID from URL route
        # self.user_id = self.scope['url_route']['kwargs'].get('user_id')
        user = self.scope["user"]

        # if not self.user_id:
        #     await self.close()
        #     return
        if not user.is_authenticated:
            await self.close()
            return
            
        # Verify user exists and is authenticated
        self.user = user
        self.user_group_name = f"user_{user.id}_notifications"


        # user = await self.get_user(self.user_id)
        # if not user:
        #     await self.close()
        #     return
            
        self.user_group_name = f'user_{self.user_id}_notifications'
        
        # Join user group
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        # await self.channel_layer.group_add(
        #     self.user_group_name,
        #     self.channel_name
        # )
        
        await self.accept()
        
        # Send current unread count
        unread_count = await self.get_unread_count()
        await self.send(text_data=json.dumps({
            "type": "unread_count",
            "count": unread_count
        }))
        # unread_count = await self.get_unread_count()
        # await self.send(text_data=json.dumps({
        #     'type': 'unread_count',
        #     'count': unread_count
        # }))

    async def disconnect(self, close_code):
        # Leave user group
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'mark_read':
                notification_id = text_data_json.get('notification_id')
                success = await self.mark_notification_read(notification_id)
                
                if success:
                    # Update unread count
                    unread_count = await self.get_unread_count()
                    await self.send(text_data=json.dumps({
                        'type': 'unread_count',
                        'count': unread_count
                    }))
        except json.JSONDecodeError:
            pass

    async def send_notification(self, event):
        """Send notification to WebSocket"""
        notification = event['notification']
        
        await self.send(text_data=json.dumps({
            'type': 'new_notification',
            'notification': notification
        }))
        
        # Update unread count
        unread_count = await self.get_unread_count()
        await self.send(text_data=json.dumps({
            'type': 'unread_count',
            'count': unread_count
        }))

    @database_sync_to_async
    def get_user(self, user_id):
        """Get user by ID"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def get_unread_count(self):
        """Get unread notification count for user"""
        # return Notification.objects.filter(user_id=self.user_id, is_read=False).count()
        return Notification.objects.filter(user=self.user, is_read=False).count()

    # @database_sync_to_async
    # def mark_notification_read(self, notification_id):
    #     """Mark a notification as read"""
    #     try:
    #         notification = Notification.objects.get(id=notification_id, user_id=self.user_id)
    #         notification.mark_as_read()
    #         return True
    #     except Notification.DoesNotExist:
    #         return False
    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        try:
            notification = Notification.objects.get(
                id=notification_id,
                user=self.user
            )
            notification.mark_as_read()
            return True
        except Notification.DoesNotExist:
            return False
