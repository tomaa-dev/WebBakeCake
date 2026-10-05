import secrets

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import CodeForm, OrderForm, PhoneForm, ProfileForm, get_or_create_user
from .models import AdLink, Berries, Cake, CakeForm, Decor, Level, Order, Topping


def index(request):
    tag = request.GET.get("start")
    if tag and request.session.get("utm") != tag:
        updated = AdLink.objects.filter(tag=tag).update(visits=F("visits") + 1)
        if updated:
            request.session["utm"] = tag

    reg = request.GET.get("reg", "")
    step = {"code": "Code", "code-error": "Code", "phone-error": "Number"}.get(reg, "Number")
    phone = request.session.get("reg_phone", "") if reg else ""
    context = {
        "reg_step": step,
        "reg_open": reg != "",
        "reg_phone": phone,
        "cakes": [
            {"pk": c.pk, "name": c.name, "price": c.price, "image": c.image.url if c.image else ""}
            for c in Cake.objects.all()
        ],
        "options": {
            "levels": list(Level.objects.values("index_value", "name", "price")),
            "forms": list(CakeForm.objects.values("index_value", "name", "price")),
            "toppings": list(Topping.objects.values("index_value", "name", "price")),
            "berries": list(Berries.objects.values("index_value", "name", "price")),
            "decors": list(Decor.objects.values("index_value", "name", "price")),
        },
    }
    return render(request, "index.html", context)


@login_required
def lk(request):
    context = {
        "name": request.user.first_name,
        "email": request.user.email,
        "edit": request.GET.get("edit") == "1",
        "orders": request.user.order_set.select_related("cake", "level", "cake_form", "topping", "berry", "decor"),
    }
    return render(request, "lk.html", context)


@login_required
def lk_profile(request):
    form = ProfileForm(request.POST)
    if not form.is_valid():
        for error in form.errors.values():
            messages.error(request, "; ".join(error))
        return render(
            request,
            "lk.html",
            {
                "name": form.data.get("name", ""),
                "email": form.data.get("email", ""),
                "edit": True,
                "orders": request.user.order_set.select_related(
                    "cake", "level", "cake_form", "topping", "berry", "decor"
                ),
            },
        )
    request.user.first_name = form.cleaned_data["name"]
    request.user.email = form.cleaned_data["email"]
    request.user.save()
    messages.success(request, "Профиль обновлён")
    return redirect("cakes:lk")


def _fail(request, flag, form=None):
    if form is not None:
        for errors in form.errors.values():
            messages.error(request, "; ".join(errors))
    return redirect(f"/?reg={flag}")


@require_POST
def reg(request):
    step = request.POST.get("step", "phone")

    if step == "code":
        form = CodeForm(request.POST)
        if not form.is_valid():
            return _fail(request, "code-error", form)

        expected = request.session.pop("reg_code", None)
        if not expected or form.cleaned_data["code"] != expected:
            messages.error(request, "Неверный код подтверждения, запросите новый")
            return _fail(request, "code-error")

        phone = request.session.pop("reg_phone", None)
        if not phone:
            return _fail(request, "phone-error")

        user, _ = get_or_create_user(phone)
        if user.pd_consent_at is None:
            user.pd_consent_at = timezone.now()
            user.save(update_fields=["pd_consent_at"])
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
    messages.info(request, f"Демо-режим: код подтверждения — {code}. Введите его в окне.")
    return redirect("/?reg=code")


@require_POST
def logout(request):
    auth_logout(request)
    return redirect("/")


@login_required
@require_POST
def order(request):
    form = OrderForm(request.POST)
    if not form.is_valid():
        for errors in form.errors.values():
            messages.error(request, " ".join(errors))
        return redirect("cakes:index")
    data = form.cleaned_data
    order = Order(
        user=request.user,
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
        cake=data["CAKE"],
    )
    order.set_price()
    order.save()

    messages.success(request, "Заказ принят!")
    return redirect("cakes:lk")
