from django.contrib import admin
from django.urls import include, path
from care.views import home, caregiver, presentation, manager_login, manager_logout, manager_dashboard

urlpatterns = [path("admin/", admin.site.urls), path("api/", include("care.urls")), path("", home, name="home"), path("login/", manager_login, name="manager_login"), path("logout/", manager_logout, name="manager_logout"), path("central/", manager_dashboard, name="manager_dashboard"), path("caregiver/", caregiver, name="caregiver"), path("apresentacao/", presentation, name="presentation")]
