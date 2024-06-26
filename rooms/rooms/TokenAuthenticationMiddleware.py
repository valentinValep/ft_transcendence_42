from channels.auth import AuthMiddlewareStack
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections
from channels.db import database_sync_to_async
import requests

class TokenAuthMiddleware:
	"""
	Token authorization middleware for Django Channels 2
	"""

	def __init__(self, app):
		self.app = app

	async def __call__(self, scope, receive, send):
		headers = scope.get('headers', [])
		cookies = [items for items in headers if items[0] == b'cookie']
		scope['user'] = {}
		if len(cookies) == 0:
			return await self.app(scope, receive, send)
		cookies = [cookie.strip() for cookie in cookies[0][1].decode().split(';')]
		token_key = list(filter(lambda x: x.startswith('token='), cookies))[0].split('=')[1]
		if token_key:
			#user = await database_sync_to_async(get_user)(token_key)
			user = get_user(token_key)
			if not user:
				return await self.app(scope, receive, send)
			scope['user'] = user["user"]
			close_old_connections()
		return await self.app(scope, receive, send)

#Change this one to send a request to /auth endpoint
def get_user(token_key):
	response = requests.get(
		'http://proxy/api/auth',
		headers = {'Authorization': 'Token ' + token_key}
	)
	if response.status_code != 200:
		return None
	print(type(response))
	print(response.json())
	return response.json()

def TokenAuthMiddlewareStack(app):
	return TokenAuthMiddleware(AuthMiddlewareStack(app))
