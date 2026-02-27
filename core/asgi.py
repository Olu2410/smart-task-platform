"""
ASGI config for core project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""
#  core/asgi.py
import os
# import django
from django.core.asgi import get_asgi_application
# django.setup()
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
import notifications.routing
import team_chat.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Combine all WebSocket routes
websocket_urlpatterns = (
    notifications.routing.websocket_urlpatterns +
    team_chat.routing.websocket_urlpatterns
)

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})