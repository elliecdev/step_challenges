from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='steps-home'),
    path('leaderboard', views.leaderboard, name='steps-leaderboard'),
]
