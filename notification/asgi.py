"""
ASGI config for srcs project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter, ChannelNameRouter
from notification.middleware import WebSocketAuthMiddleware
from notification.TokenAuthenticationMiddleware import TokenAuthMiddleware
from channels.security.websocket import AllowedHostsOriginValidator
from django.urls import path
from notification.consumers import NotificationConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

application = ProtocolTypeRouter({
	"http": get_asgi_application(),
	"websocket": TokenAuthMiddleware(
		AllowedHostsOriginValidator(
			URLRouter([
				path('ws/notif/<str:username>', NotificationConsumer.as_asgi()),
			])
		)
	),
})
