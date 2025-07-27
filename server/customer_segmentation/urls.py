from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_page, name='login_page'),  # Default landing page
    path('register/', views.register_page, name='register_page'),
    path('home/', views.home, name='home'),         # Upload CSV
    path('result/', views.result, name='result'),   # Output page
    path('logout/', views.logout_user, name='logout'),  # Optional
    
]
