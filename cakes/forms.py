"""Forms for phone registration.

CONSENT_VERSION records which revision of static/privacy/pd.pdf the user
agreed to. That PDF is currently a draft written for the MVP, not a
document approved by the client: replace the file and bump this constant
when the real one lands. The version is stored alongside the consent in
the session, so old consents stay attributable to the text they covered.
"""

import re

from django import forms

from .models import User

CONSENT_VERSION = "1.0"


class PhoneForm(forms.Form):
    phone = forms.CharField(
        label="Номер телефона",
        max_length=20,
        widget=forms.TextInput(attrs={"placeholder": "+7 999 123-45-67"}),
    )
    agree = forms.BooleanField(
        label="Согласие на обработку персональных данных",
        error_messages={"required": "Без согласия на обработку персональных данных регистрация невозможна"},
    )

    def clean_phone(self):
        phone = "".join(ch for ch in self.cleaned_data["phone"] if ch.isdigit())
        if len(phone) not in (10, 11):
            raise forms.ValidationError("Введите номер полностью, например +7 999 123-45-67")
        return phone

    def clean_agree(self):
        return True


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
