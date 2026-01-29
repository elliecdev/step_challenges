from django import forms
from django.template import Context
from django.test import RequestFactory, TestCase

from steps.templatetags.form_tags import add_class
from steps.templatetags.nav_active import nav_active


class AddClassFilterTest(TestCase):
    def test_add_class_returns_widget_with_class(self):
        # In templates the filter receives a BoundField (form["field"])
        class F(forms.Form):
            name = forms.CharField()
        form = F()
        bound_field = form["name"]
        result = add_class(bound_field, "my-class")
        self.assertIn('class="my-class"', str(result))


class NavActiveTagTest(TestCase):
    def test_nav_active_returns_is_active_for_current_url(self):
        factory = RequestFactory()
        request = factory.get("/add-entry/")
        request.resolver_match = type("ResolverMatch", (), {"url_name": "steps-add-entry"})()
        context = Context({"request": request})
        result = nav_active(context, "steps-add-entry")
        self.assertEqual(result, "is-active")

    def test_nav_active_returns_empty_for_other_url(self):
        factory = RequestFactory()
        request = factory.get("/leaderboard/")
        request.resolver_match = type("ResolverMatch", (), {"url_name": "steps-leaderboard"})()
        context = Context({"request": request})
        result = nav_active(context, "steps-add-entry")
        self.assertEqual(result, "")
