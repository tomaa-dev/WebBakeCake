from django.urls import path

from . import views

app_name = "cakes"


urlpatterns = [
    path("", views.index, name="index"),
    path("lk/", views.lk, name="lk"),
    path("lk/profile/", views.lk_profile, name="lk_profile"),
    path("reg/", views.reg, name="reg"),
    path("logout/", views.logout, name="logout"),
    path("order/", views.order, name="order"),
]
