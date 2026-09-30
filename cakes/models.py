from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    username = models.CharField("Номер телефона", max_length=20, unique=True)
    first_name = models.CharField("Имя", max_length=100, blank=True)
    email = models.EmailField("Почта", max_length=50, blank=True)

    class Meta:
        verbose_name = "пользователь"
        verbose_name_plural = "пользователи"

    def __str__(self):
        return self.username


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


class Form(CakeOption):
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
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Покупатель", on_delete=models.SET_NULL, null=True, blank=True
    )

    client_name = models.CharField("Имя клиента", max_length=50)
    phone_number = models.CharField("Номер телефона", max_length=20)
    email = models.EmailField("Почта", max_length=50)

    address = models.CharField("Адрес", max_length=100)
    delivery_date = models.DateField("Дата доставки")  # хз в каком формате приходит, возможно придётся отформатировать
    delivery_time = models.TimeField("Время доставки")

    delivery_comment = models.TextField("Комментарий курьеру", blank=True)

    level = models.ForeignKey(Level, verbose_name="Уровни", on_delete=models.PROTECT)
    form = models.ForeignKey(Form, verbose_name="Форма", on_delete=models.PROTECT)
    topping = models.ForeignKey(Topping, verbose_name="Топпинг", on_delete=models.PROTECT)
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


# ниже просто взял со self_storage, если что уберём


class AdLink(models.Model):
    name = models.CharField("Название целевого сервиса", max_length=50)
    tag = models.CharField("Тег", max_length=10, unique=True)
    short_url = models.URLField("Короткая ссылка", blank=True)
    visits = models.PositiveIntegerField("Переходы", default=0)

    def __str__(self):
        return f"{self.name} ({self.tag})"


class PromoCode(models.Model):
    code = models.CharField("Промокод", max_length=50, unique=True)
    discount_percent = models.PositiveIntegerField("Скидка %")
    valid_from = models.DateTimeField("Действует с")
    valid_until = models.DateTimeField("Действует до")
    is_active = models.BooleanField("Активен", default=True)
    max_uses = models.PositiveIntegerField("Максимум использований", default=1)
    used_count = models.PositiveIntegerField("Количество использований", default=0)

    def __str__(self):
        return f"{self.code} – {self.discount_percent}%"
