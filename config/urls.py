"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# config/urls.py (o como se llame tu proyecto)

from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Login / Logout explícitos
    path(
        'login/',
        auth_views.LoginView.as_view(
            template_name='gestion_gmexpress/login.html',  # el login.html que ya hicimos
        ),
        name='login',
    ),
    path(
        'logout/',
        auth_views.LogoutView.as_view(
            next_page='login',  # después de cerrar sesión te manda al login
        ),
        name='logout',
    ),

    # App principal
    path('', include('gestion_gmexpress.urls')),
]
