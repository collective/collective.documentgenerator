# -*- coding: utf-8 -*-

from Acquisition import aq_base

from collective.documentgenerator.testing import TEST_INSTALL_INTEGRATION
from collective.documentgenerator.testing import PODTemplateIntegrationBrowserTest

from plone import api

import unittest


class TestPODTemplate(unittest.TestCase):
    """
    Test PODTemplate content type.
    """

    layer = TEST_INSTALL_INTEGRATION

    def test_PODTemplate_portal_type_is_registered(self):
        portal_types = api.portal.get_tool('portal_types')
        registered_types = portal_types.listContentTypes()
        self.assertTrue('PODTemplate' in registered_types)


class TestPODTemplateFields(PODTemplateIntegrationBrowserTest):
    """
    Test schema fields declaration.
    """

    def test_class_registration(self):
        from collective.documentgenerator.content.pod_template import PODTemplate
        self.assertTrue(self.test_podtemplate.__class__ == PODTemplate)

    def test_schema_registration(self):
        portal_types = api.portal.get_tool('portal_types')
        podtemplate_type = portal_types.get(self.test_podtemplate.portal_type)
        self.assertTrue('IPODTemplate' in podtemplate_type.schema)

    def test_odt_file_attribute(self):
        test_podtemplate = aq_base(self.test_podtemplate)
        self.assertTrue(hasattr(test_podtemplate, 'odt_file'))

    def test_odt_file_field_display(self):
        self.browser.open(self.test_podtemplate.absolute_url())
        contents = self.browser.contents
        msg = "field 'odt_file' is not displayed"
        self.assertTrue('id="form-widgets-odt_file"' in contents, msg)
        msg = "field 'odt_file' is not translated"
        self.assertTrue('Document odt' in contents, msg)

    def test_odt_file_field_edit(self):
        self.browser.open(self.test_podtemplate.absolute_url() + '/edit')
        contents = self.browser.contents
        msg = "field 'odt_file' is not editable"
        self.assertTrue('Document odt' in contents, msg)

    def test_pod_permission_attribute(self):
        test_podtemplate = aq_base(self.test_podtemplate)
        self.assertTrue(hasattr(test_podtemplate, 'pod_permission'))

    def test_pod_permission_field_display(self):
        self.browser.open(self.test_podtemplate.absolute_url())
        contents = self.browser.contents
        msg = "field 'pod_permission' is not displayed"
        self.assertTrue('id="form-widgets-pod_permission"' in contents, msg)
        msg = "field 'pod_permission' is not translated"
        self.assertTrue('Permission' in contents, msg)

    def test_pod_permission_field_edit(self):
        self.browser.open(self.test_podtemplate.absolute_url() + '/edit')
        contents = self.browser.contents
        msg = "field 'pod_permission' is not editable"
        self.assertTrue('Permission' in contents, msg)

    def test_pod_expression_attribute(self):
        test_podtemplate = aq_base(self.test_podtemplate)
        self.assertTrue(hasattr(test_podtemplate, 'pod_expression'))

    def test_pod_expression_field_display(self):
        self.browser.open(self.test_podtemplate.absolute_url())
        contents = self.browser.contents
        msg = "field 'pod_expression' is not displayed"
        self.assertTrue('id="form-widgets-pod_expression"' in contents, msg)
        msg = "field 'pod_expression' is not translated"
        self.assertTrue('Expression TAL' in contents, msg)

    def test_pod_expression_field_edit(self):
        self.browser.open(self.test_podtemplate.absolute_url() + '/edit')
        contents = self.browser.contents
        msg = "field 'pod_expression' is not editable"
        self.assertTrue('Expression TAL' in contents, msg)
