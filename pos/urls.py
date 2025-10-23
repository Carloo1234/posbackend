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
    path('shops/<str:slug>/product/<int:pk>/', views.ProductDetailView.as_view(), name='product_details'),
    path('shops/<str:slug>/product/<int:pk>/edit/', views.ProductUpdateView.as_view(), name='product_update'),
    path('shops/<str:slug>/product/<int:pk>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),
    path('shops/<str:slug>/products/create/', views.ProductCreateView.as_view(), name='product_create'),
    path('shops/<str:slug>/product/<int:pk>/barcode_download/', views.ProductBarcodeDownloadView.as_view(), name="download_barcode")
]