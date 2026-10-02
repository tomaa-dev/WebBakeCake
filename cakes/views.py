import secrets

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import CONSENT_VERSION, CodeForm, OrderForm, PhoneForm, ProfileForm, get_or_create_user
from .models import AdLink, Cake, Order


def index(request):
    tag = request.GET.get("start")
    if tag and request.session.get("utm") != tag:
        updated = AdLink.objects.filter(tag=tag).update(visits=F("visits") + 1)
        if updated:
            request.session["utm"] = tag  # подсчёт кликов

    reg = request.GET.get("reg", "")
    step = {"code": "Code", "code-error": "Code", "phone-error": "Number"}.get(reg, "Number")
    phone = request.session.get("reg_phone", "") if reg else ""
    context = {"reg_step": step, "reg_open": reg != "", "reg_phone": phone, "cakes": Cake.objects.all()}
    return render(request, "index.html", context)


@login_required
def lk(request):
    context = {
        "name": request.user.first_name,
        "email": request.user.email,
        "edit": request.GET.get("edit") == "1",
    }
    return render(request, "lk.html", context)


@login_required
def lk_profile(request):
    form = ProfileForm(request.POST)
    if not form.is_valid():
        for error in form.errors.values():
            messages.error(request, "; ".join(error))
        return render(
            request, "lk.html", {"name": form.data.get("name", ""), "email": form.data.get("email", ""), "edit": True}
        )
    request.user.first_name = form.cleaned_data["name"]
    request.user.email = form.cleaned_data["email"]
    request.user.save()
    messages.success(request, "Профиль обновлён")
    return redirect("cakes:lk")


@login_required
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

    phone = str(form.cleaned_data["phone"])
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


# Принятие заказа


@require_POST
def order(request):
    form = OrderForm(request.POST)
    if not form.is_valid():
        for errors in form.errors.values():
            messages.error(request, " ".join(errors))
        return redirect("cakes:index")
    data = form.cleaned_data
    order = Order(
        user=request.user if request.user.is_authenticated else None,
        utm=request.session.get("utm", ""),
        client_name=data["NAME"],
        phone_number=data["PHONE"],
        email=data["EMAIL"],
        address=data["ADDRESS"],
        delivery_date=data["DATE"],
        delivery_time=data["TIME"],
        delivery_comment=data["DELIVCOMMENTS"],
        level=data["LEVELS"],
        cake_form=data["FORM"],
        topping=data["TOPPING"],
        berry=data["BERRIES"],
        decor=data["DECOR"],
        inscription=data["WORDS"],
        cake_comment=data["COMMENTS"],
    )
    order.set_price()
    order.save()

    messages.success(request, "Заказ принят!")
    return redirect("cakes:index")  # создадим список заказа - редирект лучше туда наверное сделать
