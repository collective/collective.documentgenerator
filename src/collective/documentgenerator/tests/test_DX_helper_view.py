# -*- coding: utf-8 -*-
import DateTime

from zope.component import getUtility
from plone.app.testing import login

from plone import api
from plone.autoform.interfaces import READ_PERMISSIONS_KEY
from plone.behavior.interfaces import IBehavior

from collective.documentgenerator.testing import DexterityIntegrationTests


class TestDexterityHelperView(DexterityIntegrationTests):

    """Test Dexterity helper view."""

    def test_DX_helper_view_registration(self):
        """Test that when we query a IDocumentGenerationHelper adpater on an DX object, we get
        the DX implementation of DocumentGenerationHelperView."""
        from collective.documentgenerator.helper import DXDocumentGenerationHelperView

        helper_view = self.content.unrestrictedTraverse('@@document_generation_helper_view')
        msg = "The helper should have been an instance of DXDocumentGenerationHelperView"
        self.assertTrue(isinstance(helper_view, DXDocumentGenerationHelperView), msg)

    def test_DX_proxy_object_registration(self):
        """Test that when we query a IDocumentGenerationHelper adpater on an DX object, we get
        the DX implementation of DisplayProxyObject as context."""
        from collective.documentgenerator.helper import DXDisplayProxyObject

        helper_view = self.content.unrestrictedTraverse('@@document_generation_helper_view')
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
        helper_view = self.content.unrestrictedTraverse('@@document_generation_helper_view')
        proxy = helper_view.context

        proxy.display = lambda field_name: 'foobar'

        msg = "The proxy should have call proxy.display() method."
        self.assertTrue(proxy.fullname == 'foobar', msg)

        # description is in IBasic behavior
        self.assertTrue(proxy.description == 'foobar', msg)

        msg = "If we try to access the attribute value through the accessor, it should return \
               the real value stored on the schema's field."
        self.assertTrue(proxy.Description() != 'foobar', msg)


class TestDexterityHelperViewMethods(DexterityIntegrationTests):

    """Test Dexterity implementation of helper view's methods."""

    def setUp(self):
        super(TestDexterityHelperViewMethods, self).setUp()
        self.view = self.content.unrestrictedTraverse(
            '@@document_generation_helper_view')

    def test_display_method_on_text_field(self):
        field_name = 'fullname'
        expected = 'John Doe'
        self.content.fullname = expected
        result = self.view.display(field_name)
        self.assertEqual(expected, result)

    def test_display_method_on_multiselect_field(self):
        field_name = 'languages'
        to_set = ['en', 'fr']
        expected = u'English\nFrançais'
        self.content.languages = to_set
        result = self.view.display(field_name)
        self.assertEqual(expected, result)

    def test_display_method_on_datefield(self):
        field_name = 'birth_date'
        to_set = DateTime.DateTime('18/09/1986')
        expected = '18/09/1986 00:00'
        self.content.birth_date = to_set
        result = self.view.display(field_name)
        self.assertEqual(expected, result)

    def test_display_method_empty_value(self):
        displayed = self.view.display('amount', no_value='foobar')
        msg = "empty value display was expected to be 'foobar'"
        self.assertTrue(displayed == 'foobar', msg)

    def test_display_date_method(self):
        field_name = 'birth_date'
        self.content.birth_date = DateTime.DateTime('18/09/1986')

        # toLocalizedTime
        expected_date = u'Sep 18, 1986'
        result = self.view.display_date(field_name)
        expected_date = u'Sep 18, 1986 12:00 AM'
        result = self.view.display_date(field_name, long_format=True)
        expected_date = u'12:00 AM'
        result = self.view.display_date(field_name, time_only=True)

        # custom_format
        expected_date = '18 yolo 09 yolo 1986'
        result = self.view.display_date(field_name, custom_format='%d yolo %m yolo %Y')
        self.assertEqual(expected_date, result)

    def test_display_voc_method(self):
        field_name = 'languages'
        to_set = ('en', 'fr')
        expected = u'English|Français'
        self.content.languages = to_set
        result = self.view.display_voc(field_name, separator=u'|')
        self.assertEqual(expected, result)

    def test_check_permission(self):
        # test user has permission
        self.assertTrue(self.view.check_permission('amount', self.content))

        # new user that doesn't have permission
        api.user.create(username='foobar', email='foobar@example.com')
        login(self.portal, 'foobar')
        self.assertFalse(self.view.check_permission('amount', self.content))

        # manually set permission on a behavior's field
        schema = getUtility(
            IBehavior,
            "plone.app.dexterity.behaviors.metadata.IBasic").interface
        schema.setTaggedValue(
            READ_PERMISSIONS_KEY, {'description': 'cmf.ManagePortal'})

        self.assertFalse(self.view.check_permission('description', self.content))
