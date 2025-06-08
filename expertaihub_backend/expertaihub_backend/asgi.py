# expertaihub_backend/asgi.py

import os
import django
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "expertaihub_backend.settings")
django.setup()

# Initialize Django ASGI application early to ensure the app is loaded before routing
django_asgi_app = get_asgi_application()

from .routing import application
