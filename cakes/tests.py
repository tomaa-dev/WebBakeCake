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

    def test_code_step_blocked_without_consent(self):
        self.client.post("/reg/", {"step": "phone", "phone": "9991234567", "agree": "1"})
        code = self.client.session["reg_code"]
        resp = self.client.post("/reg/", {"step": "code", "code": code, "agree": ""})
        self.assertIn("code-error", resp["Location"])
        self.assertFalse(User.objects.filter(username="9991234567").exists())

    def test_consent_is_stored_on_success(self):
        self.client.post("/reg/", {"step": "phone", "phone": "8 999 123-45-67", "agree": "1"})
        code = self.client.session["reg_code"]
        self.client.post("/reg/", {"step": "code", "code": code, "agree": "1"})

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
        agree = body.index('name="agree"', body.index('<v-field v-model="Agree"'))
        self.assertLess(start, agree)
        self.assertLess(agree, end)
