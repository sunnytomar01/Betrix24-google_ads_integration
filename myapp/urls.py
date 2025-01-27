from django.urls import path
from . import views

urlpatterns = [
    
    path('bitrix24_handler/', views.bitrix24_handler, name='bitrix24_handler'),
]
