from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class ConsentRequiredTests(TestCase):
    """Согласие на ПД обязательно на обоих шагах регистрации."""

    def test_phone_step_blocked_without_consent(self):
        resp = self.client.post("/reg/", {"step": "phone", "phone": "9991234567", "agree": ""})
        self.assertEqual(resp.status_code, 302)
        self.assertIn("phone-error", resp["Location"])
        self.assertFalse(User.objects.filter(username="9991234567").exists())

    def test_consent_is_asked_only_on_the_phone_step(self):
        self.client.post("/reg/", {"step": "phone", "phone": "9991234567", "agree": "1"})
        code = self.client.session["reg_code"]
        resp = self.client.post("/reg/", {"step": "code", "code": code})
        self.assertEqual(resp["Location"], "/")
        self.assertIn("_auth_user_id", self.client.session)

    def test_code_step_rejected_when_phone_step_had_no_consent(self):
        session = self.client.session
        session["reg_phone"] = "9991234567"
        session["reg_code"] = "1234"
        session.save()
        resp = self.client.post("/reg/", {"step": "code", "code": "1234"})
        self.assertIn("phone-error", resp["Location"])
        self.assertFalse(User.objects.exists())

    def test_consent_is_stored_on_success(self):
        self.client.post("/reg/", {"step": "phone", "phone": "8 999 123-45-67", "agree": "1"})
        code = self.client.session["reg_code"]
        self.client.post("/reg/", {"step": "code", "code": code})

        user = User.objects.get(username="89991234567")
        self.assertEqual(str(user), "89991234567")
        self.assertIn("_auth_user_id", self.client.session)

        consent = self.client.session["pd_consent"]
        self.assertEqual(consent["version"], "1.0")
        self.assertEqual(consent["phone"], "89991234567")
        self.assertIn("at", consent)


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
        self.assertEqual(User.objects.filter(username="9991234567").count(), 1)

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

    def test_consent_checkbox_is_inside_the_vee_validate_form(self):
        body = self.client.get("/").content.decode()
        start = body.index("<v-form")
        end = body.index("</v-form>")
        checkbox = body.index('id="pdConsent"')
        opening_tag = body.rindex("<v-field", start, checkbox)
        self.assertLess(start, opening_tag)
        self.assertLess(checkbox, end)
        self.assertIn('name="agree"', body[opening_tag:checkbox])

    def test_consent_rule_lives_on_the_field_not_in_the_shared_schema(self):
        schema = self.client.get("/").content.decode()
        script = Path(settings.BASE_DIR / "static" / "js" / "registration.js").read_text(encoding="utf-8")
        self.assertNotIn("agree:", script)
        self.assertIn(":rules=", schema)


class HeaderAfterRegistrationTests(TestCase):
    def _register(self):
        self.client.post("/reg/", {"step": "phone", "phone": "8 999 123-45-67", "agree": "1"})
        code = self.client.session["reg_code"]
        return self.client.post("/reg/", {"step": "code", "code": code})

    def test_icon_opens_modal_for_anonymous_visitor(self):
        body = self.client.get("/").content.decode()
        self.assertIn('data-bs-toggle="modal"', body)
        self.assertNotIn("89991234567", body)

    def test_phone_replaces_icon_after_registration(self):
        self._register()
        body = self.client.get("/").content.decode()
        self.assertIn("89991234567", body)
        self.assertNotIn('data-bs-toggle="modal"', body)

    def test_logout_restores_the_icon(self):
        self._register()
        self.client.get("/logout/")
        body = self.client.get("/").content.decode()
        self.assertIn('data-bs-toggle="modal"', body)


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

    def test_order_page_is_closed_for_anonymous_visitor(self):
        resp = self.client.get("/lk-order/")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("reg=Number", resp["Location"])
        self.assertIn("next=/lk-order/", resp["Location"])

    def test_profile_is_taken_from_the_account(self):
        self._register()
        user = get_user_model().objects.get(username="89991234567")
        user.first_name = "Анна"
        user.email = "anna@example.com"
        user.save()
        body = self.client.get("/lk/").content.decode()
        self.assertIn('data-name="Анна"', body)
        self.assertIn('data-phone="89991234567"', body)
        self.assertIn('data-email="anna@example.com"', body)

    def test_mockup_profile_is_gone_from_both_templates(self):
        self._register()
        for url in ("/lk/", "/lk-order/"):
            with self.subTest(url=url):
                body = self.client.get(url).content.decode()
                self.assertNotIn("Ирина", body)
                self.assertNotIn("nyam@gmail.com", body)

    def test_profile_is_read_from_the_mount_element(self):
        script = Path(settings.BASE_DIR / "static" / "js" / "lk.js").read_text(encoding="utf-8")
        self.assertNotIn("nyam@gmail.com", script)
        self.assertIn("mount.dataset.name", script)
        self.assertIn("mount.dataset.phone", script)
        self.assertIn("mount.dataset.email", script)

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
        user = get_user_model().objects.get(username="89991234567")
        self.assertEqual(user.first_name, "Анна")
        self.assertEqual(user.email, "anna@example.com")

    def test_phone_survives_an_attempt_to_change_it(self):
        self._register()
        self.client.post("/lk/profile/", {"name": "Анна", "email": "a@b.ru", "phone": "8000000000"})
        self.assertTrue(get_user_model().objects.filter(username="89991234567").exists())
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
        self.assertEqual(get_user_model().objects.get(username="89991234567").first_name, "")

    def test_bad_email_is_rejected_server_side(self):
        self._register()
        self.client.post("/lk/profile/", {"name": "Анна", "email": "не-почта"})
        self.assertEqual(get_user_model().objects.get(username="89991234567").first_name, "")

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
        self.assertIn(">89991234567</a>", body)
