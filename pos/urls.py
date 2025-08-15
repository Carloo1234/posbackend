from . import views
from django.urls import path
from django.contrib.auth.views import LoginView

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.Login.as_view(), name='login'),
    path('logout/', views.Logout.as_view(), name='logout'),
    path('home/', views.home, name='home'),
    path('home/owned-shops/', views.owned_shops, name='owned_shops'),
    path('home/managed-shops/', views.managed_shops, name='managed_shops'),
    path('home/manager-invites/', views.manager_invites, name='manager_invites'),
    path('create_shop/', views.create_shop, name='create_shop'),
    path('shops/<str:slug>/dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('shops/<str:slug>/products/', views.ProductView.as_view(), name='products'),
]