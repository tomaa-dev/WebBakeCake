from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    AdLink,
    Berries,
    Decor,
    Form,
    Level,
    Order,
    PromoCode,
    Topping,
    User,
)


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


@admin.register(Form)
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
    list_display = (
        "id",
        "client_name",
        "phone_number",
        "delivery_date",
        "price",
        "user",
        "created_at",
    )
    list_filter = ("delivery_date", "created_at", "user")
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
                    "form",
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
                "fields": ("price", "created_at"),
            },
        ),
    )


@admin.register(AdLink)
class AdLinkAdmin(admin.ModelAdmin):
    list_display = ("name", "tag", "short_url", "visits")
    search_fields = ("name", "tag")


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "discount_percent",
        "valid_from",
        "valid_until",
        "is_active",
        "used_count",
        "max_uses",
    )
    list_filter = ("is_active",)
    search_fields = ("code",)
