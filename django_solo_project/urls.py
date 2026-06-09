"""django_solo_project URL Configuration"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from families_app.media_serve import serve_media

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('families_app.urls')),
]

# خدمة ملفات media في بيئة التطوير مع دعم Range (ضروري للفيديو/الصوت)
if settings.DEBUG:
    media_prefix = settings.MEDIA_URL.lstrip('/')
    urlpatterns += [
        re_path(r'^' + media_prefix + r'(?P<path>.*)$', serve_media),
    ]
