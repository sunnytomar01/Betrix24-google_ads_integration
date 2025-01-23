from django.urls import path
from .views import bitrix24_handler

urlpatterns = [
    path('bitrix24-handler/', bitrix24_handler, name='bitrix24_handler'),
]
