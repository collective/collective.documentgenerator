# -*- coding: utf-8 -*-

from collective.documentgenerator.testing import DexterityIntegrationTests
from plone import api
from plone.app.testing import login
from plone.app.testing import logout
from plone.app.textfield.value import RichTextValue
from plone.autoform.interfaces import READ_PERMISSIONS_KEY
from plone.behavior.interfaces import IBehavior
from Products.CMFPlone.utils import safe_unicode
from z3c.form.interfaces import NO_VALUE
from zope.component import getUtility

import datetime


class TestDexterityHelperView(DexterityIntegrationTests):

    """Test Dexterity helper view."""

    def test_DX_helper_view_registration(self):
        """Test that when we query a IDocumentGenerationHelper adpater on an DX object, we get
        the DX implementation of DocumentGenerationHelperView."""
        from collective.documentgenerator.helper import DXDocumentGenerationHelperView

        helper_view = self.content.unrestrictedTraverse(
            "@@document_generation_helper_view"
        )
        msg = (
            "The helper should have been an instance of DXDocumentGenerationHelperView"
        )
        self.assertTrue(isinstance(helper_view, DXDocumentGenerationHelperView), msg)

    def test_DX_proxy_object_registration(self):
        """Test that when we query a IDocumentGenerationHelper adpater on an DX object, we get
        the DX implementation of DisplayProxyObject as context."""
        from collective.documentgenerator.helper import DXDisplayProxyObject

        helper_view = self.content.unrestrictedTraverse(
            "@@document_generation_helper_view"
        )
        proxy = helper_view.context
        msg = "The proxy object should have been an instance of DXDisplayProxyObject"
        self.assertTrue(isinstance(proxy, DXDisplayProxyObject), msg)

    def test_DX_proxy_object_behaviour(self):
        """When trying to access an attribute attr_name on the object, the proxy should return
        display(attr_name) if the attribute is a field of the object schema.
        If attr_name is not a schema's field, it should delegate its access to the real object.

        eg: proxy.title -> proxy.display(field_name='title', context=real_object)
            proxy.some_method() -> real_object.some_method()
        """
        helper_view = self.content.unrestrictedTraverse(
            "@@document_generation_helper_view"
        )
        proxy = helper_view.context

        proxy.display = lambda field_name: "foobar"

        msg = "The proxy should have call proxy.display() method."
        self.assertTrue(proxy.fullname == "foobar", msg)

        # description is in IBasic behavior
        self.assertTrue(proxy.description == "foobar", msg)

        msg = (
            "If we try to access the attribute value through the accessor, it should return the real value "
            "stored on the schema's field."
        )
        self.assertTrue(proxy.Description() != "foobar", msg)

        wrapped = helper_view.real_context
        msg = " __repr__ and __str__ should return the same result as the wrapped object: {} != {}"
        self.assertEqual(
            str(proxy),
            str(helper_view.real_context),
            msg.format(str(proxy), str(wrapped)),
        )
        msg = u" __unicode__ should return the same result as the wrapped object: {} != {}"
        self.assertEqual(
            str(proxy),
            str(helper_view.real_context),
            msg.format(str(proxy), str(wrapped)),
        )


class TestDexterityHelperViewMethods(DexterityIntegrationTests):

    """Test Dexterity implementation of helper view's methods."""

    def setUp(self):
        super(TestDexterityHelperViewMethods, self).setUp()
        self.view = self.content.unrestrictedTraverse(
            "@@document_generation_helper_view"
        )
        self.doc_view = self.doc.unrestrictedTraverse(
            "@@document_generation_helper_view"
        )

    def test_display_method_on_text_field(self):
        field_name = "fullname"
        expected = "John Doe"
        self.content.fullname = expected
        result = self.view.display(field_name)
        self.assertEqual(expected, result)

    def test_display_method_on_multiselect_field(self):
        field_name = "languages"
        to_set = ["en", "fr"]
        expected = u"English\nFrançais"
        self.content.languages = to_set
        result = self.view.display(field_name)
        self.assertEqual(expected, result)

    def test_display_method_on_datefield(self):
        field_name = "birth_date"
        to_set = datetime.date(1986, 9, 18)
        expected = u"18/09/1986"
        self.content.birth_date = to_set
        result = self.view.display(field_name)
        self.assertEqual(expected, result)

    def test_display_method_on_datetimefield(self):
        field_name = "birth_datetime"
        to_set = datetime.datetime(1986, 9, 18, 10, 0)
        expected = u"18/09/1986 10:00"
        self.content.birth_datetime = to_set
        result = self.view.display(field_name)
        self.assertEqual(expected, result)

    def test_display_method_empty_value(self):
        displayed = self.view.display("amount", no_value="foobar")
        msg = "empty value display was expected to be 'foobar'"
        self.assertTrue(displayed == "foobar", msg)

        displayed = self.doc_view.display("text", no_value="yolo")

        self.assertIsNone(self.doc.text)

        self.assertTrue(displayed == "yolo", msg)

        self.doc.text = RichTextValue("")
        displayed = self.doc_view.display("text", no_value="yolo")
        self.assertEqual("", self.doc_view.real_context.text.output)
        self.assertTrue(displayed == "yolo", msg)

    def test_display_method_bypass_check_permission(self):
        self.content.amount = 20
        self.assertFalse(api.user.is_anonymous())
        self.assertEqual(self.view.display("amount", bypass_check_permission=False), 20)
        self.assertEqual(self.view.display("amount", bypass_check_permission=True), 20)
        logout()
        self.assertTrue(api.user.is_anonymous())
        self.assertEqual(
            self.view.display("amount", bypass_check_permission=False), u""
        )
        self.assertEqual(self.view.display("amount", bypass_check_permission=True), 20)

    def test_display_date_method(self):
        effective_field_name = "birth_datetime"
        self.content.birth_datetime = datetime.datetime(1986, 9, 18, 10, 0)

        # toLocalizedTime in 'fr'
        expected_date = u"18/09/1986"
        result = self.view.display_date(field_name=effective_field_name)
        self.assertEqual(expected_date, result)
        result = self.view.display_date(date=self.content.birth_datetime)
        self.assertEqual(expected_date, result)

        expected_date = u"18/09/1986 10:00"
        result = self.view.display_date(
            field_name=effective_field_name, long_format=True
        )
        self.assertEqual(expected_date, result)
        result = self.view.display_date(
            date=self.content.birth_datetime, long_format=True
        )
        self.assertEqual(expected_date, result)

        expected_date = u"10:00"
        result = self.view.display_date(field_name=effective_field_name, time_only=True)
        self.assertEqual(expected_date, result)
        result = self.view.display_date(
            date=self.content.birth_datetime, time_only=True
        )
        self.assertEqual(expected_date, result)

        # custom_format
        expected_date = "18 yolo 09 yolo 1986"
        result = self.view.display_date(
            field_name=effective_field_name, custom_format="%d yolo %m yolo %Y"
        )
        self.assertEqual(expected_date, result)
        result = self.view.display_date(
            date=self.content.birth_datetime, custom_format="%d yolo %m yolo %Y"
        )
        self.assertEqual(expected_date, result)

        # translation format has changed in Plone5.1+
        expected_date = u"jeu. 18 sept. 1986"
        result = self.view.display_date(
            field_name=effective_field_name,
            custom_format="%a %d %b %Y",
            target_language="fr",
        )
        self.assertEqual(expected_date, result)

        expected_date = u"jeudi 18 Septembre 1986"
        result = self.view.display_date(
            field_name=effective_field_name,
            custom_format="%A %d %B %Y",
            target_language="fr",
            month_lc=False,
        )
        self.assertEqual(expected_date, result)

        expected_date = u"%Jeudi 18 %B 1986"
        result = self.view.display_date(
            field_name=effective_field_name,
            custom_format="%%%A %d %%B %Y",
            target_language="fr",
            day_lc=False,
        )
        self.assertEqual(expected_date, result)

        # date
        self.content.birth_datetime = datetime.date(1986, 9, 18)
        expected_date = u"18/09/1986"
        result = self.view.display_date(field_name=effective_field_name)
        self.assertEqual(expected_date, result)
        result = self.view.display_date(date=self.content.birth_datetime)
        self.assertEqual(expected_date, result)

        expected_date = u"18/09/1986 00:00"
        result = self.view.display_date(
            field_name=effective_field_name, long_format=True
        )
        self.assertEqual(expected_date, result)
        result = self.view.display_date(
            date=self.content.birth_datetime, long_format=True
        )
        self.assertEqual(expected_date, result)

        expected_date = u"00:00"
        result = self.view.display_date(field_name=effective_field_name, time_only=True)
        self.assertEqual(expected_date, result)
        result = self.view.display_date(
            date=self.content.birth_datetime, time_only=True
        )
        self.assertEqual(expected_date, result)

        # custom_format
        expected_date = "18 yolo 09 yolo 1986"
        result = self.view.display_date(
            field_name=effective_field_name, custom_format="%d yolo %m yolo %Y"
        )
        self.assertEqual(expected_date, result)
        result = self.view.display_date(
            date=self.content.birth_datetime, custom_format="%d yolo %m yolo %Y"
        )
        self.assertEqual(expected_date, result)

    def test_display_voc_method(self):
        field_name = "languages"
        to_set = ("en", "fr")
        expected = u"English|Français"
        self.content.languages = to_set
        result = self.view.display_voc(field_name, separator=u"|")
        self.assertEqual(expected, result)

    def test_display_list_method(self):
        field_name = "languages"
        to_set = ("en", "fr")
        expected = u"en|fr"
        self.content.languages = to_set
        result = self.view.display_list(field_name, separator=u"|")
        self.assertEqual(expected, result)

    def test_list_method(self):
        field_name = "languages"
        expected = ("en", "fr")
        self.content.languages = expected
        result = self.view.list(field_name)
        self.assertEqual(expected, result)

    def test_display_text_as_html_method(self):
        actual_field_name = "description"
        to_set = "My description\r\nMy life\r\nhttp://www.imio.be"
        expected = 'My description<br />My life<br /><a href="http://www.imio.be" rel="nofollow">http://www.imio.be</a>'

        self.content.description = to_set
        result = self.view.display_text_as_html(field_name=actual_field_name)
        self.assertEqual(expected, result)

        result = self.view.display_text_as_html(text=to_set)
        self.assertEqual(expected, result)

        result = self.view.display_text_as_html()
        self.assertFalse(result, "Expected result to be None or '' but is " + result)

    def test_display_html_as_text_method(self):
        actual_field_name = "description"
        to_set = (
            '<p>My description<br />My life<br /><a href="http://www.imio.be" '
            'rel="nofollow">http://www.imio.be</a></p>'
        )
        expected = "My description\nMy life\nhttp://www.imio.be"

        self.content.description = to_set
        result = self.view.display_html_as_text(field_name=actual_field_name)
        self.assertEqual(expected, result)

        result = self.view.display_html_as_text(html=to_set)
        self.assertEqual(expected, result)

        result = self.view.display_html_as_text()
        self.assertFalse(result, "Expected result to be None or '' but is " + result)

    def test_render_xhtml_method_without_appy_renderer(self):
        field_name = "fullname"
        to_set = "John Doe"
        expected = ""
        self.content.fullname = to_set
        result = self.view.render_xhtml(field_name)
        self.assertEqual(expected, result)

    def test_display_widget_method(self):
        field_name = "subscription"
        to_set = "gold"
        self.content.subscription = to_set
        # simple call
        result = self.view.display_widget(field_name)
        expected = (
            '\n<span class="select-widget choice-field" id="form-widgets-subscription">'
            '<span class="selected-option">gold</span></span>\n'
        )
        self.assertEqual(result, expected)
        # call without cleaning
        result = self.view.display_widget(field_name, clean=False)
        expected = (
            b'\n<span id="form-widgets-subscription" class="select-widget choice-field">'
            b'<span class="selected-option">gold</span></span>\n\n'
        )
        self.assertEqual(result, expected)
        # call with soup
        result = self.view.display_widget(field_name, soup=True)
        expected = '<span class="selected-option">gold</span>'
        self.assertEqual(str(result.find("span", class_="selected-option")), expected)
        self.assertEqual(result.find("span", class_="selected-option").text, u"gold")

    def test_check_permission(self):
        # test user has permission
        self.assertTrue(self.view.check_permission("amount"))

        # new user that doesn't have permission
        api.user.create(username="foobar", email="foobar@example.com")
        login(self.portal, "foobar")
        self.assertFalse(self.view.check_permission("amount"))

        # manually set permission on a behavior's field
        schema = getUtility(
            IBehavior, "plone.app.dexterity.behaviors.metadata.IBasic"
        ).interface
        schema.setTaggedValue(READ_PERMISSIONS_KEY, {"description": "cmf.ManagePortal"})

        self.assertFalse(self.view.check_permission("description"))

    def test_get_value(self):
        # default obj or given one
        self.assertEqual(self.view.get_value("id"), "johndoe")
        self.assertEqual(self.view.get_value("id", obj=self.doc), "doc")
        # test unknown field name (a behavior field by example, that can be activated or not)
        self.assertEqual(self.view.get_value("unknown", strict=False), None)
        self.assertEqual(
            self.view.get_value("unknown", default="aa", strict=False), "aa"
        )
        self.assertRaises(AttributeError, self.view.get_value, "unknown")
        # test None value
        self.assertIsNone(self.content.amount)
        self.assertEqual(self.view.get_value("amount"), None)
        self.assertEqual(self.view.get_value("amount", default="aa"), "aa")
        # check NO_VALUE
        self.content.subscription = NO_VALUE
        self.assertEqual(self.content.subscription, NO_VALUE)
        self.assertEqual(self.view.get_value("subscription", default="aa"), "aa")
        # check RichText
        self.content.biography = RichTextValue(
            raw=safe_unicode("<h1>Hello</h1>"),
            mimeType="text/html",
            outputMimeType="text/html",
            encoding="utf-8",
        )
        self.assertEqual(self.view.get_value("biography"), "<h1>Hello</h1>")
        # check utf8
        self.content.title = u"héhé"
        self.assertEqual(self.view.get_value("title"), u"héhé")
        self.assertEqual(self.view.get_value("title", as_utf8=True), "héhé")
