from datetime import date, time, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase

from .forms import PhoneForm
from .models import (
    INSCRIPTION_PRICE,
    URGENT_PERCENT_PRICE_INCREASE,
    Cake,
    CakeForm,
    Level,
    Order,
)

User = get_user_model()


class PhoneTests(TestCase):
    def test_spellings(self):
        for raw in (
            "+7 999 123-45-67",
            "8 999 123-45-67",
            "8(999)123-45-67",
            "79991234567",
            "9991234567",
        ):
            with self.subTest(raw=raw):
                form = PhoneForm({"phone": raw, "agree": "1"})
                self.assertTrue(form.is_valid())
                self.assertEqual(str(form.cleaned_data["phone"]), "+79991234567")

    def test_bad_input(self):
        for raw in ("", "не телефон", "+7 999 123-45-6"):
            with self.subTest(raw=raw):
                self.assertFalse(PhoneForm({"phone": raw, "agree": "1"}).is_valid())

    def test_foreign_rejected(self):
        for raw in ("+1 202 555 0147", "+49 151 12345678", "+375 29 1234567"):
            with self.subTest(raw=raw):
                self.assertFalse(PhoneForm({"phone": raw, "agree": "1"}).is_valid())

    def test_foreign_not_saved(self):
        self.client.post("/reg/", {"step": "phone", "phone": "+1 202 555 0147", "agree": "1"})
        self.assertNotIn("reg_phone", self.client.session)
        self.assertFalse(User.objects.exists())


class ConsentRequiredTests(TestCase):
    """Согласие на ПД обязательно на обоих шагах регистрации."""

    def test_phone_step_blocked_without_consent(self):
        resp = self.client.post("/reg/", {"step": "phone", "phone": "9991234567", "agree": ""})
        self.assertEqual(resp.status_code, 302)
        self.assertIn("phone-error", resp["Location"])
        self.assertFalse(User.objects.filter(username="+79991234567").exists())

    def test_consent_is_stored_on_success(self):
        self.client.post("/reg/", {"step": "phone", "phone": "8 999 123-45-67", "agree": "1"})
        code = self.client.session["reg_code"]
        self.client.post("/reg/", {"step": "code", "code": code})

        user = User.objects.get(username="+79991234567")
        self.assertEqual(str(user), "+79991234567")
        self.assertIn("_auth_user_id", self.client.session)
        self.assertIsNotNone(user.pd_consent_at)


class RegistrationFlowTests(TestCase):
    def test_code_is_generated_and_step_advanced(self):
        resp = self.client.post("/reg/", {"step": "phone", "phone": "8 999 123-45-67", "agree": "1"})
        self.assertIn("?reg=code", resp["Location"])
        code = self.client.session["reg_code"]
        self.assertEqual(len(code), 4)
        self.assertTrue(code.isdigit())

    def test_wrong_code_is_rejected(self):
        self.client.post("/reg/", {"step": "phone", "phone": "9991234567", "agree": "1"})
        resp = self.client.post("/reg/", {"step": "code", "code": "0000", "agree": "1"})
        self.assertIn("code-error", resp["Location"])
        self.assertFalse(User.objects.exists())

    def test_invalid_phone_is_rejected(self):
        resp = self.client.post("/reg/", {"step": "phone", "phone": "abc", "agree": "1"})
        self.assertIn("phone-error", resp["Location"])

    def test_repeated_registration_reuses_single_user(self):
        for _ in range(2):
            self.client.post("/reg/", {"step": "phone", "phone": "9991234567", "agree": "1"})
            code = self.client.session["reg_code"]
            self.client.post("/reg/", {"step": "code", "code": code, "agree": "1"})
        self.assertEqual(User.objects.filter(username="+79991234567").count(), 1)

    def test_logout_clears_session(self):
        self.client.post("/reg/", {"step": "phone", "phone": "9991234567", "agree": "1"})
        code = self.client.session["reg_code"]
        self.client.post("/reg/", {"step": "code", "code": code, "agree": "1"})

        self.client.get("/logout/")
        self.assertNotIn("_auth_user_id", self.client.session)


class IndexTemplateTests(TestCase):
    def test_registration_form_is_wired(self):
        body = self.client.get("/").content.decode()
        self.assertIn('action="/reg/"', body)
        self.assertIn("csrfmiddlewaretoken", body)
        self.assertIn('name="phone"', body)
        self.assertIn('name="code"', body)
        self.assertIn('name="step"', body)
        self.assertIn('name="agree"', body)

    def test_consent_link_points_to_pdf(self):
        body = self.client.get("/").content.decode()
        self.assertIn("privacy/pd.pdf", body)

    def test_step_reaches_modal(self):
        self.assertIn('data-init-step="Number"', self.client.get("/").content.decode())
        self.assertIn('data-init-step="Code"', self.client.get("/?reg=code").content.decode())

    def test_modal_stays_closed_on_plain_index(self):
        self.assertIn('data-init-open="false"', self.client.get("/").content.decode())

    def test_modal_reopens_on_every_registration_redirect(self):
        for flag in ("code", "code-error", "phone-error"):
            with self.subTest(flag=flag):
                body = self.client.get(f"/?reg={flag}").content.decode()
                self.assertIn('data-init-open="true"', body)


class PersonalCabinetTests(TestCase):
    def _register(self):
        self.client.post("/reg/", {"step": "phone", "phone": "8 999 123-45-67", "agree": "1"})
        code = self.client.session["reg_code"]
        self.client.post("/reg/", {"step": "code", "code": code})

    def test_anonymous_visitor_is_sent_to_registration(self):
        resp = self.client.get("/lk/")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("reg=Number", resp["Location"])
        self.assertIn("next=/lk/", resp["Location"])

    def test_profile_is_taken_from_the_account(self):
        self._register()
        user = get_user_model().objects.get(username="+79991234567")
        user.first_name = "Анна"
        user.email = "anna@example.com"
        user.save()
        body = self.client.get("/lk/").content.decode()
        self.assertIn('data-name="Анна"', body)
        self.assertIn('data-phone="+79991234567"', body)
        self.assertIn('data-email="anna@example.com"', body)

    def test_exit_button_leads_to_logout(self):
        self._register()
        body = self.client.get("/lk/").content.decode()
        self.assertIn('href="/logout/"', body)


class ProfileSavingTests(TestCase):
    def _register(self):
        self.client.post("/reg/", {"step": "phone", "phone": "8 999 123-45-67", "agree": "1"})
        code = self.client.session["reg_code"]
        self.client.post("/reg/", {"step": "code", "code": code})

    def test_name_and_email_are_saved(self):
        self._register()
        self.client.post("/lk/profile/", {"name": "Анна", "email": "anna@example.com"})
        user = get_user_model().objects.get(username="+79991234567")
        self.assertEqual(user.first_name, "Анна")
        self.assertEqual(user.email, "anna@example.com")

    def test_phone_survives_an_attempt_to_change_it(self):
        self._register()
        self.client.post("/lk/profile/", {"name": "Анна", "email": "a@b.ru", "phone": "8000000000"})
        self.assertTrue(get_user_model().objects.filter(username="+79991234567").exists())
        self.assertFalse(get_user_model().objects.filter(username="8000000000").exists())

    def test_phone_field_is_read_only_and_absent_from_the_submit_form(self):
        self._register()
        body = self.client.get("/lk/").content.decode()
        self.assertIn(':readonly="true"', body)
        self.assertNotIn('name="phone"', body)

    def test_bad_name_keeps_edit_mode_and_the_typed_value(self):
        self._register()
        resp = self.client.post("/lk/profile/", {"name": "Анна123", "email": "anna@example.com"})
        body = resp.content.decode()
        self.assertIn('data-init-edit="true"', body)
        self.assertIn('data-name="Анна123"', body)
        self.assertEqual(get_user_model().objects.get(username="+79991234567").first_name, "")

    def test_bad_email_is_rejected_server_side(self):
        self._register()
        self.client.post("/lk/profile/", {"name": "Анна", "email": "не-почта"})
        self.assertEqual(get_user_model().objects.get(username="+79991234567").first_name, "")

    def test_profile_endpoint_is_closed_for_anonymous_visitor(self):
        resp = self.client.post("/lk/profile/", {"name": "Анна", "email": "a@b.ru"})
        self.assertEqual(resp.status_code, 302)
        self.assertIn("reg=Number", resp["Location"])

    def test_header_shows_the_name_when_it_is_known(self):
        self._register()
        self.client.post("/lk/profile/", {"name": "Анна", "email": "anna@example.com"})
        self.assertIn(">Анна</a>", self.client.get("/lk/").content.decode())
        self.assertIn(">Анна</a>", self.client.get("/").content.decode())

    def test_header_falls_back_to_the_phone_when_there_is_no_name(self):
        self._register()
        body = self.client.get("/lk/").content.decode()
        self.assertIn(">+79991234567</a>", body)


class OrderPriceTests(TestCase):
    def setUp(self):
        self.cake = Cake.objects.create(name="Медовик", price=2000)
        self.level = Level.objects.create(name="Два уровня", price=1000, index_value=2)
        self.form = CakeForm.objects.create(name="Круг", price=500, index_value=1)

    def test_ready_cake_costs_its_own_price(self):
        order = Order(cake=self.cake, delivery_date=date.today() + timedelta(days=5), delivery_time=time(12))
        order.set_price()
        self.assertEqual(order.price, 2000)

    def test_ready_cake_ignores_options(self):
        order = Order(
            cake=self.cake,
            level=self.level,
            cake_form=self.form,
            inscription="Х",
            delivery_date=date.today() + timedelta(days=5),
            delivery_time=time(12),
        )
        order.set_price()
        self.assertEqual(order.price, 2000)

    def test_options_and_inscription_are_summed(self):
        order = Order(
            level=self.level,
            cake_form=self.form,
            inscription="Х",
            delivery_date=date.today() + timedelta(days=5),
            delivery_time=time(12),
        )
        order.set_price()
        self.assertEqual(order.price, 1000 + 500 + INSCRIPTION_PRICE)

    def test_urgent_delivery_adds_surcharge(self):
        soon = date.today() + timedelta(hours=1)
        order = Order(cake=self.cake, delivery_date=soon, delivery_time=time(12))
        order.set_price()
        self.assertEqual(order.price, 2000 + 2000 * URGENT_PERCENT_PRICE_INCREASE // 100)

    def test_late_delivery_has_no_surcharge(self):
        order = Order(cake=self.cake, delivery_date=date.today() + timedelta(days=5), delivery_time=time(12))
        order.set_price()
        self.assertFalse(order.is_urgent())


class OrderHistoryTests(TestCase):
    def setUp(self):
        self.client.post("/reg/", {"step": "phone", "phone": "8 999 123-45-67", "agree": "1"})
        code = self.client.session["reg_code"]
        self.client.post("/reg/", {"step": "code", "code": code})
        self.user = get_user_model().objects.get(username="+79991234567")
        self.cake = Cake.objects.create(name="Медовик", price=2000)

    def _order(self, **kwargs):
        data = {
            "user": self.user,
            "cake": self.cake,
            "client_name": "Анна",
            "phone_number": "+79991234567",
            "email": "anna@example.com",
            "address": "ул. Тестовая 1",
            "delivery_date": date.today() + timedelta(days=5),
            "delivery_time": time(12),
        }
        data.update(kwargs)
        order = Order.objects.create(price=0, **data)
        return order

    def test_empty_history_shows_the_placeholder(self):
        body = self.client.get("/lk/").content.decode()
        self.assertIn("У вас еще нет заказов", body)

    def test_order_appears_in_history(self):
        self._order()
        body = self.client.get("/lk/").content.decode()
        self.assertIn("Медовик", body)
        self.assertIn("2000", body)

    def test_history_shows_status_and_delivery_time(self):
        self._order(status=Order.Status.DELIVERING)
        body = self.client.get("/lk/").content.decode()
        self.assertIn("У курьера", body)
        self.assertNotIn("Время доставки: ?", body)

    def test_only_own_orders_are_listed(self):
        self._order()
        other = get_user_model().objects.create_user(username="+79997654321", password="x")
        Order.objects.create(
            user=other,
            client_name="Чужой",
            phone_number="+79997654321",
            email="other@example.com",
            address="ул. Чужая 2",
            delivery_date=date.today(),
            delivery_time=time(12),
            price=500,
        )
        body = self.client.get("/lk/").content.decode()
        self.assertNotIn("Чужой", body)

    def test_newest_order_comes_first(self):
        self._order(cake=Cake.objects.create(name="Первый", price=100))
        self._order(cake=Cake.objects.create(name="Второй", price=200))
        body = self.client.get("/lk/").content.decode()
        self.assertLess(body.index("Второй"), body.index("Первый"))


class OrderRegistrationTests(TestCase):
    def setUp(self):
        self.cake = Cake.objects.create(name="Медовик", price=2000)
        self.cake.image = "Cake.png"
        self.cake.save()
        self.data = {
            "CAKE": self.cake.pk,
            "NAME": "Анна",
            "PHONE": "+7 999 123-45-67",
            "EMAIL": "anna@example.com",
            "ADDRESS": "ул. Тестовая 1",
            "DATE": date.today() + timedelta(days=5),
            "TIME": "12:00",
        }

    def _register(self):
        self.client.post("/reg/", {"step": "phone", "phone": "8 999 123-45-67", "agree": "1"})
        self.client.post("/reg/", {"step": "code", "code": self.client.session["reg_code"]})

    def test_anonymous_cannot_place_an_order(self):
        resp = self.client.post("/order/", self.data)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Order.objects.count(), 0)

    def test_anonymous_is_sent_to_registration(self):
        resp = self.client.post("/order/", self.data)
        self.assertIn("reg=Number", resp["Location"])

    def test_registered_user_places_an_order(self):
        self._register()
        self.client.post("/order/", self.data)
        order = Order.objects.get()
        self.assertEqual(order.user.username, "+79991234567")

    def test_page_warns_before_registration(self):
        body = self.client.get("/").content.decode()
        self.assertIn("Для оформления заказа необходимо зарегистрироваться", body)
        self.assertEqual(body.count("alert alert-danger"), 2)
        self.assertIn('id="auth-data" type="application/json">false<', body)

    def test_auth_flag_is_true_for_a_user(self):
        self._register()
        body = self.client.get("/").content.decode()
        self.assertIn('id="auth-data" type="application/json">true<', body)
