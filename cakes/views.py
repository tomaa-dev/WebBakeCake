import secrets

from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render
from django.utils import timezone

from .forms import CONSENT_VERSION, CodeForm, PhoneForm, get_or_create_user


def index(request):
    reg = request.GET.get("reg", "")
    step = {"code": "Code", "code-error": "Code", "phone-error": "Number"}.get(reg, "Number")
    phone = request.session.get("reg_phone", "") if reg else ""
    return render(request, "index.html", {"reg_step": step, "reg_open": reg != "", "reg_phone": phone})


def lk(request):
    return render(request, "lk.html")


def lk_order(request):
    return render(request, "lk-order.html")


def _fail(request, flag, form=None):
    if form is not None:
        for errors in form.errors.values():
            messages.error(request, "; ".join(errors))
    return redirect(f"/?reg={flag}")


def reg(request):
    step = request.POST.get("step", "phone")

    if step == "code":
        form = CodeForm(request.POST)
        if not form.is_valid():
            return _fail(request, "code-error", form)

        expected = request.session.get("reg_code")
        if not expected or form.cleaned_data["code"] != expected:
            messages.error(request, "Неверный код подтверждения, запросите новый")
            return _fail(request, "code-error")

        phone = request.session.pop("reg_phone", None)
        request.session.pop("reg_code", None)
        consent = request.session.pop("reg_consent", None)
        if not phone:
            return _fail(request, "phone-error")
        if not consent or consent["phone"] != phone:
            messages.error(request, "Подтвердите согласие на обработку персональных данных")
            return _fail(request, "phone-error")

        user, _ = get_or_create_user(phone)
        request.session["pd_consent"] = consent
        login(request, user)
        messages.success(request, f"Готово, вы зарегистрированы как {phone}")
        return redirect("/")

    form = PhoneForm(request.POST)
    if not form.is_valid():
        return _fail(request, "phone-error", form)

    phone = form.cleaned_data["phone"]
    code = f"{secrets.randbelow(9000) + 1000:04d}"
    request.session["reg_phone"] = phone
    request.session["reg_code"] = code
    request.session["reg_consent"] = {
        "phone": phone,
        "at": timezone.now().isoformat(),
        "version": CONSENT_VERSION,
    }
    messages.info(request, f"Демо-режим: код подтверждения — {code}. Введите его в окне.")
    return redirect("/?reg=code")


def logout(request):
    request.session.flush()
    return redirect("/")
