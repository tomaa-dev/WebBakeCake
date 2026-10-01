from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField

INSCRIPTION_PRICE = 500
URGENT_HOURS = 24
URGENT_PERCENT_PRICE_INCREASE = 20


class User(AbstractUser):
    username = PhoneNumberField("Номер телефона", max_length=20, region="RU", unique=True)
    first_name = models.CharField("Имя", max_length=100, blank=True)
    email = models.EmailField("Почта", max_length=50, blank=True)
    pd_consent_at = models.DateTimeField("Согласие на обработку ПД", null=True, blank=True)

    class Meta:
        verbose_name = "пользователь"
        verbose_name_plural = "пользователи"

    def __str__(self):
        return str(self.username)


class Cake(models.Model):
    name = models.CharField("Название", max_length=50)
    price = models.PositiveIntegerField("Цена", default=0)

    class Meta:
        verbose_name = "готовый торт"
        verbose_name_plural = "готовые торты"

    def __str__(self):
        return self.name


class CakeOption(models.Model):
    name = models.CharField("Название", max_length=50)
    price = models.PositiveIntegerField("Цена", default=0)
    index_value = models.PositiveIntegerField("Номер с фронта", unique=True)

    class Meta:
        abstract = True
        ordering = ["index_value"]

    def __str__(self):
        return self.name


class Level(CakeOption):
    class Meta(CakeOption.Meta):
        verbose_name = "количество уровней"
        verbose_name_plural = "количества уровней"


class CakeForm(CakeOption):
    class Meta(CakeOption.Meta):
        verbose_name = "форма"
        verbose_name_plural = "формы"


class Topping(CakeOption):
    class Meta(CakeOption.Meta):
        verbose_name = "топпинг"
        verbose_name_plural = "топпинги"


class Berries(CakeOption):
    class Meta(CakeOption.Meta):
        verbose_name = "ягоды"
        verbose_name_plural = "ягоды"


class Decor(CakeOption):
    class Meta(CakeOption.Meta):
        verbose_name = "декор"
        verbose_name_plural = "декор"


class Order(models.Model):
    class Status(models.TextChoices):
        CREATED = "CREATED", "Не обработан"
        PREPARING = "PREPARING", "Готовится"
        DELIVERING = "DELIVERING", "У курьера"
        COMPLETED = "COMPLETED", "Доставлен"
        CANCELLED = "CANCELLED", "Отменён"

    status = models.CharField(
        "статус",
        max_length=15,
        choices=Status.choices,
        default=Status.CREATED,
        db_index=True,
    )

    FINISHED_STATUSES = [Status.COMPLETED, Status.CANCELLED]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Покупатель", on_delete=models.SET_NULL, null=True, blank=True
    )
    utm = models.CharField("Рекламная метка", max_length=50, blank=True)

    client_name = models.CharField("Имя клиента", max_length=50)
    phone_number = PhoneNumberField("Номер телефона", max_length=20, region="RU", db_index=True)
    email = models.EmailField("Почта", max_length=50)

    address = models.CharField("Адрес", max_length=100)
    delivery_date = models.DateField("Дата доставки")  # хз в каком формате приходит, возможно придётся отформатировать
    delivery_time = models.TimeField("Время доставки")

    delivery_comment = models.TextField("Комментарий курьеру", blank=True)

    cake = models.ForeignKey(Cake, verbose_name="Готовый торт", on_delete=models.PROTECT, null=True, blank=True)

    level = models.ForeignKey(
        Level, verbose_name="Уровни", on_delete=models.PROTECT, null=True, blank=True
    )  # null=true потому что теперь есть готовые торты
    cake_form = models.ForeignKey(CakeForm, verbose_name="Форма", on_delete=models.PROTECT, null=True, blank=True)
    topping = models.ForeignKey(Topping, verbose_name="Топпинг", on_delete=models.PROTECT, null=True, blank=True)
    berry = models.ForeignKey(
        Berries, verbose_name="Ягоды", on_delete=models.PROTECT, null=True, blank=True
    )  # там в хтмльках нет возможность "отжать" кнопку, поправит надо бы
    decor = models.ForeignKey(Decor, verbose_name="Декор", on_delete=models.PROTECT, null=True, blank=True)

    inscription = models.CharField("Надпись", max_length=50, blank=True)  # сколько вместится на торт?
    cake_comment = models.TextField("Комментарий к заказу", blank=True)

    price = models.PositiveIntegerField("Общая цена")
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        verbose_name = "заказ"
        verbose_name_plural = "заказы"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Заказ от {self.created_at}"

    def is_urgent(self):
        delivery_at = timezone.make_aware(datetime.combine(self.delivery_date, self.delivery_time))
        return delivery_at - timezone.now() < timedelta(hours=URGENT_HOURS)

    def set_price(self):
        if self.cake:
            price = self.cake.price
        else:
            options = (self.level, self.cake_form, self.topping, self.berry, self.decor)
            price = sum(option.price for option in options if option)
            if self.inscription:
                price += INSCRIPTION_PRICE
        if self.is_urgent():
            price += price * URGENT_PERCENT_PRICE_INCREASE // 100
        self.price = price


# ниже просто взял со self_storage, если что уберём


class AdLink(models.Model):
    name = models.CharField("Название целевого сервиса", max_length=50)
    tag = models.CharField("Тег", max_length=10, unique=True)
    visits = models.PositiveIntegerField("Переходы", default=0)

    def __str__(self):
        return f"{self.name} ({self.tag})"
