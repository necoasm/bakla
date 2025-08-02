# bakla_project/asgi.py
import os
from django.core.asgi import get_asgi_application

# Önce Django'nun temel ayarlarını yapmasına izin ver
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bakla_project.settings')

# get_asgi_application() çağrısı, Django'nun ayarlarını ve uygulama
# kayıtlarını (app registry) yüklemesini tetikler.
django_asgi_app = get_asgi_application()

# Ayarlar yüklendikten SONRA, Channels ve routing'i import et
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import messaging.routing

application = ProtocolTypeRouter({
    # HTTP istekleri için, Django'nun standart ASGI uygulamasını kullan
    "http": django_asgi_app,

    # WebSocket istekleri geldiğinde, Channels'ın yönlendirmesini kullan
    "websocket": AuthMiddlewareStack(
        URLRouter(
            messaging.routing.websocket_urlpatterns
        )
    ),
})