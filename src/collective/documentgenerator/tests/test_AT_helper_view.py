# -*- coding: utf-8 -*-

from collective.documentgenerator.config import HAS_PLONE_5
from collective.documentgenerator.testing import ArchetypesIntegrationTests

from plone import api
from plone.app.testing import login

import DateTime
import unittest


@unittest.skipIf(HAS_PLONE_5, "Do not launch AT specific tests on Plone 5")
class TestArchetypesHelperView(ArchetypesIntegrationTests):
    """
    Test Archetypes helper view.
    """

    def test_AT_helper_view_registration(self):
        """
        Test that when we query a IDocumentGenerationHelper adpater on an AT object, we get
        the AT implementation of DocumentGenerationHelperView.
        """
        from collective.documentgenerator.helper import ATDocumentGenerationHelperView

        helper_view = self.AT_topic.unrestrictedTraverse('@@document_generation_helper_view')
        msg = 'The helper should have been an instance of ATDocumentGenerationHelperView'
        self.assertTrue(isinstance(helper_view, ATDocumentGenerationHelperView), msg)

    def test_AT_proxy_object_registration(self):
        """
        Test that when we query a IDocumentGenerationHelper adpater on an AT object, we get
        the AT implementation of DocumentGenerationHelperView.
        """
        from collective.documentgenerator.helper import ATDisplayProxyObject

        helper_view = self.AT_topic.unrestrictedTraverse('@@document_generation_helper_view')
        proxy = helper_view.context
        msg = 'The proxy object should have been an instance of ATDisplayProxyObject'
        self.assertTrue(isinstance(proxy, ATDisplayProxyObject), msg)

    def test_AT_proxy_object_behaviour(self):
        """
        When trying to access an attribute attr_name on the object, the proxy should return
        display(attr_name) if the attribute is a field of the object schema.
        If attr_name is not a schema's field, it should delegate its access to the real object.

        eg: proxy.title -> proxy.display(field_name='title', context=real_object)
            proxy.some_method() -> real_object.some_method()
        """
        helper_view = self.AT_topic.unrestrictedTraverse('@@document_generation_helper_view')
        proxy = helper_view.context

        proxy.display = lambda field_name: 'yolo'

        msg = "The proxy should have call proxy.display() method as 'title' is a schema's field."
        self.assertTrue(proxy.description == 'yolo', msg)

        msg = ("If we try to access the attribute value through the accessor, it should return the real value "
               "stored on the schema's field.")
        self.assertTrue(proxy.Title() != 'yolo', msg)


@unittest.skipIf(HAS_PLONE_5, "Do not launch AT specific tests on Plone 5")
class TestArchetypesHelperViewMethods(ArchetypesIntegrationTests):
    """
    Test Archetypes implementation of helper view's methods.
    """

    def setUp(self):
        super(TestArchetypesHelperViewMethods, self).setUp()
        self.view = self.AT_topic.unrestrictedTraverse('@@document_generation_helper_view')

    def _test_display(self, field_name, expected, result):
        msg = "Expected display of field '{}' to be '{}' but got '{}'".format(
            field_name,
            expected,
            result
        )
        self.assertTrue(expected == result, msg)

    def _test_display_method(self, field_name, expected, to_set=None):
        if to_set is None:
            to_set = expected

        field = self.AT_topic.getField(field_name)
        field.set(self.AT_topic, to_set)

        result = self.view.display(field_name)
        self._test_display(field_name, expected, result)

    def test_display_method_on_unauthorized_field(self):
        field_name = 'description'
        to_set = 'Yolo!'
        expected_text = ''

        # hack the checkPermission method to always return False
        description_field = self.AT_topic.getField(field_name)
        description_field.checkPermission = lambda permission, context: False

        self._test_display_method(field_name, expected_text, to_set)

    def test_display_method_on_text_field(self):
        field_name = 'description'
        expected_text = 'Yolo!'
        self._test_display_method(field_name, expected_text)

    def test_display_method_on_multiselect_field(self):
        field_name = 'customViewFields'
        to_set = ['Title', 'Description', 'EffectiveDate']
        expected_text = 'Title, Description, Effective Date'
        self._test_display_method(field_name, expected_text, to_set)

    def test_display_method_on_datefield(self):
        field_name = 'effectiveDate'
        date_to_set = DateTime.DateTime('23/06/1975')
        expected_date = '23/06/1975 00:00'
        self._test_display_method(field_name, expected_date, date_to_set)

    def test_display_method_empty_value(self):
        displayed = self.view.display('effectiveDate', no_value='yolo')
        msg = "empty value display was expected to be 'yolo'"
        self.assertTrue(displayed == 'yolo', msg)

    def test_display_date_method(self):
        effective_field_name = 'effectiveDate'
        date_to_set = DateTime.DateTime('18/09/1986')

        field = self.AT_topic.getField(effective_field_name)
        field.set(self.AT_topic, date_to_set)

        # toLocalizedTime
        expected_date = u'Sep 18, 1986'
        result = self.view.display_date(field_name=effective_field_name)
        self.assertEqual(expected_date, result)
        result = self.view.display_date(date=date_to_set)
        self.assertEqual(expected_date, result)

        expected_date = u'Sep 18, 1986 12:00 AM'
        result = self.view.display_date(field_name=effective_field_name, long_format=True)
        self.assertEqual(expected_date, result)
        result = self.view.display_date(date=date_to_set, long_format=True)
        self.assertEqual(expected_date, result)

        expected_date = u'12:00 AM'
        result = self.view.display_date(field_name=effective_field_name, time_only=True)
        self.assertEqual(expected_date, result)
        result = self.view.display_date(date=date_to_set, time_only=True)
        self.assertEqual(expected_date, result)

        # custom_format
        expected_date = '18 yolo 09 yolo 1986'
        result = self.view.display_date(field_name=effective_field_name, custom_format='%d yolo %m yolo %Y')
        self.assertEqual(expected_date, result)
        result = self.view.display_date(date=date_to_set, custom_format='%d yolo %m yolo %Y')
        self.assertEqual(expected_date, result)

    def test_display_voc_method(self):
        field_name = 'customViewFields'
        to_set = ['Title', 'Description', 'EffectiveDate']
        expected_text = 'Title swag Description swag Effective Date'

        field = self.AT_topic.getField(field_name)
        field.set(self.AT_topic, to_set)

        result = self.view.display_voc(field_name, separator=' swag ')

        self._test_display(field_name, expected_text, result)

    def test_display_list_method(self):
        field_name = 'customViewFields'
        to_set = ['Title', 'Description', 'EffectiveDate']
        expected_text = 'Title ; Description ; EffectiveDate'

        field = self.AT_topic.getField(field_name)
        field.set(self.AT_topic, to_set)

        result = self.view.display_list(field_name, separator=' ; ')

        self._test_display(field_name, expected_text, result)

    def test_list_method(self):
        field_name = 'customViewFields'
        expected = ['Title', 'Description', 'EffectiveDate']

        field = self.AT_topic.getField(field_name)
        field.set(self.AT_topic, expected)

        result = list(self.view.list(field_name))

        self._test_display(field_name, expected, result)

    def test_display_text_as_html_method(self):
        actual_field_name = 'description'
        to_set = 'My description\r\nMy life\r\nhttp://www.imio.be'
        expected = 'My description<br />My life<br /><a href="http://www.imio.be" rel="nofollow">http://www.imio.be</a>'

        field = self.AT_topic.getField(actual_field_name)
        field.set(self.AT_topic, to_set)

        result = self.view.display_text_as_html(field_name=actual_field_name)
        self.assertEqual(result, expected)

        result = self.view.display_text_as_html(text=to_set)
        self.assertEqual(result, expected)

        result = self.view.display_text_as_html()
        self.assertFalse(result, "Expected result to be None or '' but is " + result)

    def test_display_html_as_text_method(self):
        # use title because description does not allow mimetype text/html
        actual_field_name = 'title'
        to_set = '<p>My description<br />My life<br /><a href="http://www.imio.be" ' \
                 'rel="nofollow">http://www.imio.be</a></p>'
        expected = 'My description\nMy life\nhttp://www.imio.be'

        field = self.AT_topic.getField(actual_field_name)
        field.set(self.AT_topic, to_set)

        result = self.view.display_html_as_text(field_name=actual_field_name)
        self.assertEqual(result, expected)

        result = self.view.display_html_as_text(html=to_set)
        self.assertEqual(result, expected)

        result = self.view.display_html_as_text()
        self.assertFalse(result, "Expected result to be None or '' but is " + result)

    def test_render_xhtml_method_without_appy_renderer(self):
        field_name = 'description'
        to_set = 'Yolo!'
        expected = ''

        field = self.AT_topic.getField(field_name)
        field.set(self.AT_topic, to_set)

        result = self.view.render_xhtml(field_name)
        self._test_display(field_name, expected, result)

    def test_check_permission(self):
        # test user has permission
        self.assertTrue(self.view.check_permission('description'))

        # set field read permission to higher stuff
        field = self.AT_topic.getField('description')
        field.read_permission = 'Modify portal content'
        # new user that doesn't have permission
        api.user.create(username='foobar', email='foobar@example.com')
        login(self.portal, 'foobar')
        self.assertFalse(self.view.check_permission('description'))
