from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/',  admin.site.urls),
    path('led/',    include('led_app.urls')),
    path('accounts/login/',
         auth_views.LoginView.as_view(template_name='login.html'),
         name='login'),
    path('accounts/logout/',
         auth_views.LogoutView.as_view(next_page='/accounts/login/'),
         name='logout'),
    path('', RedirectView.as_view(url='/led/', permanent=False)),
]
