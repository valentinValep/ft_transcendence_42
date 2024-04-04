from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from time import sleep
from channels.exceptions import StopConsumer
from rooms.models import Rooms, Occupy


class RoomConsumer(WebsocketConsumer):
	def connect(self):
		self.room_id = self.scope['url_route']['kwargs']['room_id']
		self.room_group_name = f'room_{self.room_id}'
		async_to_sync(self.channel_layer.group_add)(
			self.room_group_name,
			self.channel_name
		)
		self.user = self.scope['user']
		if self.user.is_anonymous:
			self.close()
		elif (checkRoomAvailability(self.room_id) == False):
			print('Room is full')
			self.close() 
		else :
			addPlayerToRoom(self.room_id, self.user.id)
			assignMaster(self.room_id, self.user.id)
			self.accept()

		# Accept the connection only of there's available spots in the room (in normal mode)
		# If first player to enter - assign master role
	
	def disconnect(self, close_code):
		print('Disconnected')
		async_to_sync(self.channel_layer.group_discard)(
			self.room_group_name,
			self.channel_name
		)
		if Rooms.objects.filter(room_id=self.room_id, player_id=self.user.id).exists():
			occupant = Occupy.objects.get(player_id=self.user.id, room_id=self.room_id)
			occupant.delete()
		# room = Rooms.objects.get(room_id=self.room_id)
		# occupant = Occupy.objects.get(player_id=self.user.id, room_id=self.room_id)
		# if player leaves room, remove player from occupy table
		# if master leaves room, passs master to next player
		# if last player leaves room, delete room_code

	def receive(self, text_data):
		pass


def checkRoomAvailability(room_id):
	if Rooms.objects.filter(room_id=room_id).exists():
		room = Rooms.objects.get(room_id=room_id)
		if room.roomMode == 'normal':
			if Occupy.objects.filter(room_id=room_id).count() <= 6:
				return True
			else:
				return False
		elif room.roomMode == 'tournament':
			return True
	else:
		return False

def addPlayerToRoom(room_id, user_id):
	print(f"User_id is {user_id} Room_id is {room_id}")
	room = Rooms.objects.get(room_id=room_id)
	Occupy.objects.create(room_id=room, player_id=user_id)

def assignMaster(room_id, user_id):
	room = Rooms.objects.get(room_id=room_id)
	occupant = Occupy.objects.get(player_id=user_id, room_id=room_id)
	if Occupy.objects.filter(room_id=room_id).count() == 1:
		occupant.is_master = True
		occupant.save()
	else:
		pass