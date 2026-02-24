from django.urls import path
from . import views

urlpatterns = [
    path('chat/', views.chat, name='chat'),
    path('chat/stream/', views.chat_stream, name='chat_stream'),
    path('rate/', views.rate_message, name='rate'),
    path('history/', views.history, name='history'),
    path('conversations/', views.conversations, name='conversations'),
]