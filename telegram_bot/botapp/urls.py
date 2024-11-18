from django.urls import path
from .views import home

app_name = 'botapp'

urlpatterns = [
    path('', home, name="home"),
]