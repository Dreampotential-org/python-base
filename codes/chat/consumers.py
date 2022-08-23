from ast import Delete
import json
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from asgiref.sync import async_to_sync, sync_to_async
from chat.models import *
from .serializers import *
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken, TokenError
from django.contrib.auth import get_user_model
from urllib.parse import urlparse, parse_qs
User = get_user_model()
# =============================================MessageChannel============================================
class ChatConsumer(AsyncWebsocketConsumer):

    user_dictionary = {}
    user_channels_details = {}
    user_counter = 0
    user_name = 'Anonymous'
    user_list = []
    user_channel_name_list = {} #dict of all active users
    user_keys_list = [] #dict of all active users
    access_token = 0
    room_name = ""
    room_exists =False

    
    @database_sync_to_async
    def get_room(self,user_id,room_name):
        try:
            room_name = Channel.objects.get(name=room_name)
            our_channel = ChannelMember.objects.filter(Channel=room_name).filter(user=user_id)
            return our_channel.exists()
        except :
            return False

    @database_sync_to_async
    def get_user_only(self,user_id):
        try:
            our_user = User.objects.filter(id=user_id)
            
            return our_user.exists()
        except User.DoesNotExist:
            return False

    @database_sync_to_async
    def get_profile_pic_url(self, user_id):
        profile_pic = Member.objects.filter(user_id=user_id).last()
        return profile_pic.profile_pic

    @database_sync_to_async
    def get_channel_info(self,room_name):
        try:
            channel_info = Channel.objects.filter(name=room_name).first()
            if channel_info:
                channel_member = ChannelMember.objects.filter(Channel=channel_info).filter(user=self.user_id).first()
            else:
                return False
            return channel_member
        except Channel.DoesNotExist:
            return False

    @database_sync_to_async
    def extract_username_from_db(self,user_id):
        try:
            username = User.objects.filter(id=user_id).first()
            if username:
                return username.username
            else:
                return "Anonymous"
        except Channel.DoesNotExist:
            return False
 
    async def connect(self): 
        try:
            parsed_query_string = parse_qs(self.scope["query_string"])
            if parsed_query_string:
                token = parsed_query_string.get(b"token")[0].decode("utf-8")
                self.access_token = AccessToken(token)
                self.user_id = self.access_token["user_id"]
                if self.user_id:
                    #Adding user in dict
                    self.user_channel_name_list[self.access_token["user_id"]] = self.channel_name
                try:
                    #Identifying user is in group or not
                    self.room_name =  parsed_query_string.get(b"roomname")[0].decode("utf-8")
                    self.room_exists = await self.get_room(self.user_id,self.room_name)
                except:
                    self.close()
                else:  

                    self.close()
            else:
                
                self.close()
        except TokenError as e:
            # Socket has not been accepted, so cannot send over it
            # await self.channel_layer.send(
            #             self.unidentified_user,
            #     {
            #         'type': 'error_message',
            #         'message': json.dumps({"message":f"{e}"})
            #     },
            #     )
            self.close()

        if self.room_exists:
            self.channel_member = await self.get_channel_info(self.room_name)      
            await self.store_user_name(self.channel_name)
            if not self.channel_member:
                return 'No Channel defined'

            await self.accept()            
            await self.channel_layer.group_add(f"{self.room_name}", 
                                                self.channel_name)

        

        else:
            self.close()

    async def receive(self, text_data):
        msg_from_db = await self.load_message(text_data)
        msg_from_db["name"] = await self.extract_username_from_db(msg_from_db.get('user'))
        del msg_from_db['id']
        msg_from_db['User'] = msg_from_db['user']
        del msg_from_db['user']
        print(msg_from_db)
        print()
        # send_data = json.dumps(msg_from_db)
        send_data = msg_from_db
        # send_data = json.loads(text_data)
        # send_data["User"] = str(self.user_id)
        
        await self.print_details(send_data)
        await self.channel_layer.group_send(
        self.room_name,
        {
            'type': 'notification_broadcast',
            'message':  json.dumps(send_data),
        },
        )
        

    @sync_to_async
    def load_message(self, text_data):
        try:
            channel_info = Channel.objects.filter(name=self.room_name).first()
            message_details = {}
            message_details['media_link'] = json.loads(text_data)["media_link"]
            message_details['message_text'] = json.loads(text_data)["message_text"]
            message_details['meta_attributes'] = json.loads(text_data)["meta_attributes"]
            message_details['user'] = self.user_id
            message_details['channel'] = channel_info.id
            message_serializer = MessageChannelSerializers(data=message_details)
            message_serializer.is_valid(raise_exception=True)
            message = message_serializer.save()
            return MessageChannelSerializers(message).data
        except Channel.DoesNotExist:
            return False



    async def send_info_to_user_group(self, event):
        message = event["text"]
        await self.send(text_data=json.dumps(message))

    async def send_last_message(self, event):
        last_msg = await self.get_last_message(self.user_id)
        last_msg["status"] = event["text"]
        await self.send(text_data=json.dumps(last_msg))




    async def store_user_name(self, channel):
        self.user_counter += 1
        self.user_dictionary[channel] = self.user_name
        self.user_list.clear()
        self.user_list.extend(self.user_dictionary.values())

    async def users_list(self, event):
        await self.send(text_data=event["users"])

    async def print_details(self, send_data):
        pass

   

    async def notification_broadcast(self, event): 
        await self.send(text_data=event["message"])

    async def error_message(self, event):       
        await self.send(text_data=json.dumps( event["message"]))
    
    
    # Receive message from room group

    async def chat_message(self, event):
        message = event['message']

        await self.send(text_data=json.dumps({
            'message': message
        }))

    async def disconnect(self, close_code):
        # Leave room group
        try:
            # del self.user_dictionary[self.channel_name]
            # self.user_list.clear()
            # self.user_list.extend(self.user_dictionary.values())
            # await self.channel_layer.group_send(
            #     self.room_group_name,
            #     {
            #         'type': 'users_list',
            #         'users': json.dumps({'users': self.user_list, 'action': 'users_list'}),
            #     },
            # )
            await self.channel_layer.group_discard(
            self.room_name,
            self.channel_name
            )
        except:
            self.close()

# =============================================MessageUser==================================================
# This will Delete all data in Clients if we restart the server
Clients.objects.all().delete()
class MessageUserConsumer(AsyncWebsocketConsumer):

    user_channel_name_list = {} #dict of all active users
    user_keys_list = [] #dict of all active users
    access_token = 0
    receiver_id = 0
    receiver_id_exists = False
    
 

    @database_sync_to_async
    def get_user_only(self,user_id):
        try:
            our_user = User.objects.filter(id=user_id)       
            return our_user.exists()
        except User.DoesNotExist:
            return False

    @database_sync_to_async
    def to_channel_name(self,id):
            clients_active = Clients.objects.filter(user_id=id).last()  
            return clients_active.channel_name

    @database_sync_to_async
    def is_client_active(self,user_id):
        
            clients_active = Clients.objects.filter(user_id=user_id)
            # import pdb; pdb.set_trace()
            return clients_active.exists()

    @database_sync_to_async
    def clients_add(self,channel,user_id):
            createChannel = {'channel_name':channel,
            'modified_at' : models.DateTimeField(auto_now=True)
            }
            obj, create = Clients.objects.update_or_create(user_id = user_id, defaults=createChannel)
            return True

    @database_sync_to_async
    def clients_delete(self,channel):
        Clients.objects.filter(channel_name=channel).delete()
        return  True
 
    async def connect(self):       
        try:
            parsed_query_string = parse_qs(self.scope["query_string"])
            if parsed_query_string:
                token = parsed_query_string.get(b"token")[0].decode("utf-8")
                self.access_token = AccessToken(token)
                self.user_id = int(self.access_token["user_id"])
                if self.user_id:
                    #Adding user in dict
                    self.user_channel_name_list[self.access_token["user_id"]] = str(self.channel_name)
                    await self.clients_add(self.channel_name,self.user_id)
                    #Identifying receiver exist

                    try:
                        self.receiver_id = int(parsed_query_string.get(b"receiver_id")[0].decode("utf-8"))
                        self.receiver_id_exists = await self.get_user_only(self.receiver_id)
                    except:
                        self.close()
                        
                else:  

                    self.close()
                    
            else:
                
                self.close()
                
        except TokenError as e:
            # Socket has not been accepted, so cannot send over it
            # print(self.unidentified_user)
            # await self.channel_layer.send(
            #             self.unidentified_user,
            #     {
            #         'type': 'error_message',
            #         'message': json.dumps({"message":f"{e}"})
            #     },
            #     )
            self.close()

    

        if self.receiver_id_exists:
            await self.accept() 
            self.user_keys_list = [i for i in self.user_channel_name_list.keys()]
            await self.send(text_data =json.dumps(
                {
                    'action': 'users_list',
                    'users':self.user_keys_list,
                },
            ))

        else:
            self.close()

    async def receive(self, text_data):
        await self.load_message(text_data)

        send_data = json.loads(text_data)
        send_data = json.loads(text_data)
        send_data["User"] = str(self.user_id)
        if await self.is_client_active(self.receiver_id):
            await self.channel_layer.send(
                    await self.to_channel_name(self.receiver_id),
            {
                'type': 'notification_to_user',
                'message': json.dumps(send_data),
            },
            )
        elif await self.is_client_active(self.user_id):
            await self.channel_layer.send(
                    await  self.to_channel_name(self.user_id),
            {
                'type': 'error_message',
                'message': json.dumps({"message":"User is not currently active"})
            },
            )
        else:
            pass

    @sync_to_async
    def load_message(self, text_data):
        try:
            message_details = {}
            message_details['from_user'] = self.user_id
            message_details['to_user'] = self.receiver_id
            message_details['message_text'] = json.loads(text_data)["message_text"]
            message_details["media_link"] = json.loads(text_data)["media_link"]
            message_details["meta_attributes"] = json.loads(text_data)["meta_attributes"]
            message_serializer = MessageUserSerializers(data=message_details)
            message_serializer.is_valid(raise_exception=True)
            message = message_serializer.save()
            return MessageUserSerializers(message).data
        except Channel.DoesNotExist:
            return False


    async def store_user_name(self, channel):
        self.user_counter += 1
        self.user_dictionary[channel] = self.user_name
        self.user_list.clear()
        self.user_list.extend(self.user_dictionary.values())

    async def users_list(self, event):
        await self.send(text_data=event["users"])

    async def print_details(self, send_data):
        pass

    async def notification_to_user(self, event):
        await self.send(text_data=event["message"])

    async def error_message(self, event):       
        await self.send(text_data=json.dumps( event["message"]))
    
    
    # Receive message from room group

    async def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))

    async def disconnect(self, close_code):
        # Leave room group
        await self.clients_delete(self.channel_name)
        self.user_channel_name_list.pop(self.user_id)
        self.close()


# =============================================MessageSMS============================================


class MessageSMSConsumer(AsyncWebsocketConsumer):

    user_channel_name_list = {} #dict of all active users
    user_keys_list = [] #dict of all active users
    access_token = 0
    receiver_id = 0
    receiver_id_exists = False
    

    @database_sync_to_async
    def get_user_only(self,user_id):
        try:
            our_user = User.objects.filter(id=user_id)
            
            return our_user.exists()
        except User.DoesNotExist:
            return False

    @database_sync_to_async
    def clients_add(self,channel,user_id):
            createChannel = {'channel_name':channel,
            'modified_at' : models.DateTimeField(auto_now=True)
            }
            obj, create = Clients.objects.update_or_create(user_id = user_id, defaults=createChannel)
            return True
    @database_sync_to_async
    def clients_delete(self,channel):
        Clients.objects.filter(channel_name=self.channel_name).delete()
        return 1 
 
    async def connect(self):       
        try:
            parsed_query_string = parse_qs(self.scope["query_string"])
            if parsed_query_string:
                token = parsed_query_string.get(b"token")[0].decode("utf-8")
                self.access_token = AccessToken(token)
                self.user_id = int(self.access_token["user_id"])
                if self.user_id:
                    #Adding user in dict
                    self.user_channel_name_list[self.access_token["user_id"]] = str(self.channel_name)
                    await self.clients_add(self.channel_name,self.user_id)
                    #Identifying receiver exist
                    await self.accept() 
                    self.user_keys_list = [i for i in self.user_channel_name_list.keys()]
                    await self.send(text_data =json.dumps(
                        {
                            'action': 'users_list',
                            'users':self.user_keys_list,
                        },
                    ))
                        
                else:  

                    self.close()
                    
            else:
                
                self.close()
                
        except TokenError as e:
            # Socket has not been accepted, so cannot send over it
            # print(self.unidentified_user)
            # await self.channel_layer.send(
            #             self.unidentified_user,
            #     {
            #         'type': 'error_message',
            #         'message': json.dumps({"message":f"{e}"})
            #     },
            #     )
            self.close()

    

        
        

    

    async def users_list(self, event):
        await self.send(text_data=event["users"])


    async def notification_to_user(self, event):
        await self.send(text_data=event["message"])

    async def error_message(self, event):       
        await self.send(text_data=json.dumps( event["message"]))
    
    
    # Receive message from room group


    async def disconnect(self, close_code):
        # Leave room group
        await self.clients_delete(self.channel_name)
        self.user_channel_name_list.pop(self.user_id)

        self.close()




#=======================================Queue============================================================


import redis

redisconn = redis.StrictRedis(
    host='127.0.0.1', port=6379, db=0, decode_responses=True)


class ChatConsumerQueue(AsyncWebsocketConsumer):
    pass