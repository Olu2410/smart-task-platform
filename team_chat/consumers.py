# import json
# from channels.generic.websocket import AsyncWebsocketConsumer
# from channels.db import database_sync_to_async
# from .models import TeamChannel, ChannelMessage


# class ChatConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         self.channel_id = self.scope['url_route']['kwargs']['channel_id']
#         self.channel_group_name = f'chat_{self.channel_id}'
        
#         # Check if user can access this channel
#         can_access = await self.can_access_channel()
#         if not can_access:
#             await self.close()
#             return
        
#         # Join channel group
#         await self.channel_layer.group_add(
#             self.channel_group_name,
#             self.channel_name
#         )
        
#         await self.accept()
        
#         # Send last 50 messages
#         messages = await self.get_channel_messages()
#         await self.send(text_data=json.dumps({
#             'type': 'message_history',
#             'messages': messages
#         }))

#     async def disconnect(self, close_code):
#         # Leave channel group
#         if hasattr(self, 'channel_group_name'):
#             await self.channel_layer.group_discard(
#                 self.channel_group_name,
#                 self.channel_name
#             )

#     async def receive(self, text_data):
#         try:
#             text_data_json = json.loads(text_data)
#             message_type = text_data_json.get('type')
            
#             if message_type == 'chat_message':
#                 message_content = text_data_json['message']
#                 parent_message_id = text_data_json.get('parent_message_id')
                
#                 # Save message to database
#                 message = await self.save_message(message_content, parent_message_id)
                
#                 # Send message to channel group
#                 await self.channel_layer.group_send(
#                     self.channel_group_name,
#                     {
#                         'type': 'chat_message',
#                         'message': await self.message_to_dict(message)
#                     }
#                 )
            
#             elif message_type == 'typing':
#                 # Broadcast typing indicator
#                 await self.channel_layer.group_send(
#                     self.channel_group_name,
#                     {
#                         'type': 'user_typing',
#                         'user_id': str(self.scope['user'].id),
#                         'username': self.scope['user'].username,
#                         'typing': text_data_json['typing']
#                     }
#                 )
            
#             elif message_type == 'message_reaction':
#                 message_id = text_data_json['message_id']
#                 emoji = text_data_json['emoji']
#                 action = text_data_json['action']  # 'add' or 'remove'
                
#                 message = await self.update_message_reaction(message_id, emoji, action)
#                 if message:
#                     await self.channel_layer.group_send(
#                         self.channel_group_name,
#                         {
#                             'type': 'message_updated',
#                             'message': await self.message_to_dict(message)
#                         }
#                     )
#         except json.JSONDecodeError:
#             pass

#     async def chat_message(self, event):
#         """Receive message from channel group"""
#         message = event['message']
        
#         await self.send(text_data=json.dumps({
#             'type': 'chat_message',
#             'message': message
#         }))

#     async def user_typing(self, event):
#         """Handle typing indicators"""
#         await self.send(text_data=json.dumps({
#             'type': 'user_typing',
#             'user_id': event['user_id'],
#             'username': event['username'],
#             'typing': event['typing']
#         }))

#     async def message_updated(self, event):
#         """Handle message updates (reactions, etc.)"""
#         await self.send(text_data=json.dumps({
#             'type': 'message_updated',
#             'message': event['message']
#         }))

#     @database_sync_to_async
#     def can_access_channel(self):
#         """Check if user can access this channel"""
#         try:
#             channel = TeamChannel.objects.get(id=self.channel_id)
#             user = self.scope['user']
#             return channel.team.members.filter(id=user.id).exists()
#         except (TeamChannel.DoesNotExist, AttributeError):
#             return False

#     @database_sync_to_async
#     def get_channel_messages(self, limit=50):
#         """Get recent messages for the channel"""
#         messages = ChannelMessage.objects.filter(
#             channel_id=self.channel_id
#         ).select_related('user').prefetch_related('replies')[:limit]
        
#         return [self.message_to_dict_sync(message) for message in messages]

#     @database_sync_to_async
#     def save_message(self, content, parent_message_id=None):
#         """Save message to database"""
#         parent_message = None
#         if parent_message_id:
#             try:
#                 parent_message = ChannelMessage.objects.get(id=parent_message_id)
#             except ChannelMessage.DoesNotExist:
#                 pass
        
#         message = ChannelMessage.objects.create(
#             channel_id=self.channel_id,
#             user=self.scope['user'],
#             content=content,
#             parent_message=parent_message
#         )
        
#         return message

#     @database_sync_to_async
#     def update_message_reaction(self, message_id, emoji, action):
#         """Add or remove reaction from message"""
#         try:
#             message = ChannelMessage.objects.get(id=message_id)
#             if action == 'add':
#                 message.add_reaction(self.scope['user'], emoji)
#             elif action == 'remove':
#                 message.remove_reaction(self.scope['user'], emoji)
#             return message
#         except ChannelMessage.DoesNotExist:
#             return None

#     def message_to_dict_sync(self, message):
#         """Convert message to dictionary (sync version)"""
#         return {
#             'id': str(message.id),
#             'user': {
#                 'id': message.user.id,
#                 'username': message.user.username,
#                 'full_name': message.user.get_full_name() or message.user.username,
#             },
#             'content': message.content,
#             'message_type': message.message_type,
#             'reactions': message.reactions,
#             'reply_count': message.reply_count,
#             'created_at': message.created_at.isoformat(),
#             'parent_message_id': str(message.parent_message.id) if message.parent_message else None,
#         }

#     async def message_to_dict(self, message):
#         """Convert message to dictionary (async version)"""
#         return self.message_to_dict_sync(message)

#team_chat/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import TeamChannel, ChannelMessage

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.channel_id = self.scope['url_route']['kwargs']['channel_id']
        self.room_group_name = f'chat_{self.channel_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send last 20 messages
        messages = await self.get_recent_messages()
        await self.send(text_data=json.dumps({
            'type': 'message_history',
            'messages': messages
        }))

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        print("WS RECEIVE:", text_data)
        data = json.loads(text_data)
        message = data.get('message')
        print("USER:", self.scope["user"], self.scope["user"].is_authenticated)

        if not message:
            return

        saved_message = await self.save_message(message)
        print("SAVED MESSAGE:", saved_message)
        if not saved_message:
            return

        payload = await self.message_to_dict(saved_message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': payload
            }
        )


    # async def receive(self, text_data):
    #     try:
    #         text_data_json = json.loads(text_data)
    #         message = text_data_json.get('message', '')
            
    #         if message:
    #             # Save to database
    #             saved_message = await self.save_message(message)
                
    #             # Send to room group
    #             await self.channel_layer.group_send(
    #                 self.room_group_name,
    #                 {
    #                     'type': 'chat_message',
    #                     'message': await self.message_to_dict(saved_message)
    #                 }
    #             )
    #     except json.JSONDecodeError:
    #         pass

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': message
        }))

    @database_sync_to_async
    def get_recent_messages(self, limit=20):
        """Get recent messages for the channel"""
        messages = ChannelMessage.objects.filter(
            channel_id=self.channel_id
        ).select_related('user').order_by('-created_at')[:limit]
        
        # Return in chronological order
        return [self.message_to_dict_sync(msg) for msg in reversed(messages)]

    @database_sync_to_async
    def save_message(self, content):
        """Save message to database"""
        user = self.scope['user']
        if user.is_anonymous:
            return None
            
        message = ChannelMessage.objects.create(
            channel_id=self.channel_id,
            user=user,
            content=content
        )
        return message

    def message_to_dict_sync(self, message):
        """Convert message to dictionary"""
        return {
            'id': str(message.id),
            'user': {
                'id': message.user.id,
                'username': message.user.username,
                'full_name': message.user.get_full_name() or message.user.username,
            },
            'content': message.content,
            'message_type': message.message_type,
            'created_at': message.created_at.isoformat(),
            'is_file': message.message_type == 'file',
            'file_name': message.file_attachment.filename if message.file_attachment else None,
        }

    async def message_to_dict(self, message):
        """Convert message to dictionary (async)"""
        return self.message_to_dict_sync(message)