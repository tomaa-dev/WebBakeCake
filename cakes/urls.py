from django.urls import path

from . import views

app_name = "cakes"


urlpatterns = [
    path("", views.index, name="index"),
    path("lk/", views.lk, name="lk"),
    path("lk-order/", views.lk_order, name="lk_order"),
]
