from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import FrontendLoginView, StepEntryCreateView, StepEntryListView


urlpatterns = [
    path('', views.home, name='steps-home'),
    path('leaderboard', views.leaderboard, name='steps-leaderboard'),
    path("login/", FrontendLoginView.as_view(), name="steps-login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="/login"), name="steps-logout"),
    path("add-entry/", StepEntryCreateView.as_view(), name="steps-add-entry"),
    path("my-entries/", StepEntryListView.as_view(), name="steps-my-entries"),

]
