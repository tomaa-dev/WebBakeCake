"""Forms for phone registration.

CONSENT_VERSION records which revision of static/privacy/pd.pdf the user
agreed to. That PDF is currently a draft written for the MVP, not a
document approved by the client: replace the file and bump this constant
when the real one lands. The version is stored alongside the consent in
the session, so old consents stay attributable to the text they covered.
"""

import re
from datetime import datetime

from django import forms
from django.utils import timezone
from phonenumber_field.formfields import PhoneNumberField

from .models import Berries, CakeForm, Decor, Level, Topping, User

CONSENT_VERSION = "1.0"


class PhoneForm(forms.Form):
    phone = PhoneNumberField(
        label="Номер телефона",
        region="RU",
        error_messages={"invalid": "Введите корректный российский номер телефона"},
        widget=forms.TextInput(attrs={"placeholder": "+7 999 123-45-67"}),
    )
    agree = forms.BooleanField(
        label="Согласие на обработку персональных данных",
        error_messages={"required": "Без согласия на обработку персональных данных регистрация невозможна"},
    )

    def clean_phone(self):
        phone = self.cleaned_data["phone"]
        if phone.country_code != 7:
            raise forms.ValidationError("Сайт принимает только российские номера, например +7 999 123-45-67")
        return phone


class OrderForm(forms.Form):
    LEVELS = forms.ModelChoiceField(Level.objects.all(), to_field_name="index_value", required=False)
    DECOR = forms.ModelChoiceField(Decor.objects.all(), to_field_name="index_value", required=False)
    BERRIES = forms.ModelChoiceField(Berries.objects.all(), to_field_name="index_value", required=False)
    TOPPING = forms.ModelChoiceField(Topping.objects.all(), to_field_name="index_value", required=False)
    FORM = forms.ModelChoiceField(CakeForm.objects.all(), to_field_name="index_value", required=False)
    WORDS = forms.CharField(required=False, max_length=50)
    COMMENTS = forms.CharField(required=False)

    NAME = forms.CharField(max_length=50)
    DATE = forms.DateField()
    TIME = forms.TimeField()
    ADDRESS = forms.CharField(max_length=100)
    EMAIL = forms.EmailField(max_length=50)
    PHONE = PhoneNumberField(region="RU")
    DELIVCOMMENTS = forms.CharField(required=False)

    def clean(self):
        cleaned_data = super().clean()

        date = cleaned_data.get("DATE")
        time = cleaned_data.get("TIME")
        if date and time:
            delivery_at = timezone.make_aware(datetime.combine(date, time))
            if delivery_at < timezone.now():
                self.add_error("DATE", "Введите корректную дату доставки!")

        constructor = (cleaned_data.get("LEVELS"), cleaned_data.get("FORM"), cleaned_data.get("TOPPING"))
        if not all(constructor):
            raise forms.ValidationError("Выберите все необходимые опции!")

        return cleaned_data


class CodeForm(forms.Form):
    code = forms.CharField(label="Код подтверждения", max_length=4, min_length=4)


class ProfileForm(forms.Form):
    name = forms.CharField(label="Имя", max_length=100)
    email = forms.EmailField(label="Почта", max_length=50)

    def clean_name(self):
        name = self.cleaned_data["name"]
        if not re.fullmatch(r"[a-zA-Zа-яА-я]+", name):
            raise forms.ValidationError("Имя может состоять только из букв")
        return name


def get_or_create_user(phone):
    user, created = User.objects.get_or_create(username=phone, defaults={"first_name": ""})
    return user, created
