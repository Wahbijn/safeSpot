"""
ASGI config for core project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Use Channels ProtocolTypeRouter to support WebSocket handling for chat
try:
	from channels.routing import ProtocolTypeRouter, URLRouter
	from channels.auth import AuthMiddlewareStack
	import messaging.routing as messaging_routing

	django_asgi_app = get_asgi_application()

	application = ProtocolTypeRouter({
		"http": django_asgi_app,
		"websocket": AuthMiddlewareStack(
			URLRouter(
				messaging_routing.websocket_urlpatterns
			)
		),
	})
except Exception:
	# Fallback to normal ASGI app if channels is not available
	application = get_asgi_application()
