from django.urls import path
from . import views

urlpatterns = [
    path('chat/', views.chat, name='chat'),
    path('rate/', views.rate_message, name='rate'),
    path('history/', views.history, name='history'),
]