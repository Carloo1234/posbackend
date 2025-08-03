from . import views
from django.urls import path
from django.contrib.auth.views import LoginView

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.Login.as_view(), name='login'),
    path('shops/', views.shops, name='shops'),
]