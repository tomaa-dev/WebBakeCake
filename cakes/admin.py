from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import AdLink, Berries, Cake, CakeForm, Decor, Level, Order, Topping, User
from django.conf import settings


@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = ("username", "first_name", "email", "is_staff", "is_active")
    list_filter = ("is_staff", "is_active", "is_superuser")
    search_fields = ("username", "first_name", "email")
    ordering = ("username",)

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Личная информация", {"fields": ("first_name", "email")}),
        (
            "Права",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Даты", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "password1", "password2"),
            },
        ),
    )


@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "index_value")
    list_editable = ("price", "index_value")
    ordering = ("index_value",)


@admin.register(Cake)
class CakeAdmin(admin.ModelAdmin):
    list_display = ("name", "price")
    list_editable = ("price",)


@admin.register(CakeForm)
class FormAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "index_value")
    list_editable = ("price", "index_value")
    ordering = ("index_value",)


@admin.register(Topping)
class ToppingAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "index_value")
    list_editable = ("price", "index_value")
    ordering = ("index_value",)


@admin.register(Berries)
class BerriesAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "index_value")
    list_editable = ("price", "index_value")
    ordering = ("index_value",)


@admin.register(Decor)
class DecorAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "index_value")
    list_editable = ("price", "index_value")
    ordering = ("index_value",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "client_name", "phone_number", "delivery_date", "price", "user", "created_at", "status", "utm")
    list_filter = ("delivery_date", "created_at", "user", "status", "utm")
    search_fields = ("client_name", "phone_number", "email", "address")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)
    date_hierarchy = "delivery_date"

    fieldsets = (
        (
            "Клиент",
            {
                "fields": ("user", "client_name", "phone_number", "email"),
            },
        ),
        (
            "Доставка",
            {
                "fields": (
                    "address",
                    "delivery_date",
                    "delivery_time",
                    "delivery_comment",
                ),
            },
        ),
        (
            "Торт",
            {
                "fields": (
                    "level",
                    "cake_form",
                    "cake",
                    "topping",
                    "berry",
                    "decor",
                    "inscription",
                    "cake_comment",
                ),
            },
        ),
        (
            "Итог",
            {
                "fields": ("price", "created_at", "status", "utm"),
            },
        ),
    )


@admin.register(AdLink)
class AdLinkAdmin(admin.ModelAdmin):
    list_display = ("name", "tag", "visits", "ad_url")
    search_fields = ("name", "tag")
    readonly_fields = ("visits", "ad_url")

    @admin.display(description="Ссылка для рекламы")
    def ad_url(self, obj):
        if not obj.tag:
            return "--"
        return f"{settings.WEB_URL}/?start={obj.tag}"
