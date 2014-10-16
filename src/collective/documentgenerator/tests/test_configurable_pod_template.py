# -*- coding: utf-8 -*-

from Acquisition import aq_base

from collective.documentgenerator.testing import TEST_INSTALL_INTEGRATION
from collective.documentgenerator.testing import ConfigurablePODTemplateIntegrationTest

from plone import api

import unittest


class TestConfigurablePODTemplate(unittest.TestCase):
    """
    Test ConfigurablePODTemplate content type.
    """

    layer = TEST_INSTALL_INTEGRATION

    def test_ConfigurablePODTemplate_portal_type_is_registered(self):
        portal_types = api.portal.get_tool('portal_types')
        registered_types = portal_types.listContentTypes()
        self.assertTrue('ConfigurablePODTemplate' in registered_types)


class TestConfigurablePODTemplateFields(ConfigurablePODTemplateIntegrationTest):
    """
    Test schema fields declaration.
    """

    def test_class_registration(self):
        from collective.documentgenerator.content.pod_template import ConfigurablePODTemplate
        self.assertTrue(self.test_podtemplate.__class__ == ConfigurablePODTemplate)

    def test_schema_registration(self):
        portal_types = api.portal.get_tool('portal_types')
        podtemplate_type = portal_types.get(self.test_podtemplate.portal_type)
        self.assertTrue('IConfigurablePODTemplate' in podtemplate_type.schema)

    def test_pod_portal_type_attribute(self):
        test_podtemplate = aq_base(self.test_podtemplate)
        self.assertTrue(hasattr(test_podtemplate, 'pod_portal_type'))

    def test_pod_portal_type_field_display(self):
        self.browser.open(self.test_podtemplate.absolute_url())
        contents = self.browser.contents
        msg = "field 'pod_portal_type' is not displayed"
        self.assertTrue('id="form-widgets-pod_portal_type"' in contents, msg)
        msg = "field 'pod_portal_type' is not translated"
        self.assertTrue('Types de contenu autorisés' in contents, msg)

    def test_pod_portal_type_field_edit(self):
        self.browser.open(self.test_podtemplate.absolute_url() + '/edit')
        contents = self.browser.contents
        msg = "field 'pod_portal_type' is not editable"
        self.assertTrue('Types de contenu autorisés' in contents, msg)

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

    def test_enabled_attribute(self):
        test_podtemplate = aq_base(self.test_podtemplate)
        self.assertTrue(hasattr(test_podtemplate, 'enabled'))

    def test_enabled_field_display(self):
        self.browser.open(self.test_podtemplate.absolute_url())
        contents = self.browser.contents
        msg = "field 'enabled' is not displayed"
        self.assertTrue('id="form-widgets-enabled"' in contents, msg)
        msg = "field 'enabled' is not translated"
        self.assertTrue('Activé' in contents, msg)

    def test_enabled_field_edit(self):
        self.browser.open(self.test_podtemplate.absolute_url() + '/edit')
        contents = self.browser.contents
        msg = "field 'enabled' is not editable"
        self.assertTrue('Activé' in contents, msg)


class TestConfigurablePODTemplateIntegration(ConfigurablePODTemplateIntegrationTest):
    """
    Test ConfigurablePODTemplate methods.
    """

    def test_check_pod_portal_type(self):
        context = self.portal
        pod_template = self.test_podtemplate
        is_pt = pod_template.check_pod_good_pt(context)
        self.assertTrue(is_pt)

        pod_template.pod_portal_type = ('Event',)
        is_pt = pod_template.check_pod_good_pt(context)
        msg = "check_pod_portal_type() should return False: Event isn't in selected portal_type"
        self.assertTrue(not is_pt, msg)

    def test_evaluate_pod_condition(self):
        pod_template = self.test_podtemplate
        condition_result = pod_template.evaluate_pod_condition()
        self.assertTrue(condition_result is True)

        pod_template.pod_expression = 'python: "yolo" and "fo shizzle" or "ncha"'

        condition_result = pod_template.evaluate_pod_condition()
        self.assertTrue(condition_result == 'fo shizzle')

    def test_evaluate_pod_condition_with_wrong_TAL_expression(self):
        """
        evaluate_pod_condition() should throw an Exception when TAL expression is wrong.
        """
        pod_template = self.test_podtemplate
        condition_result = pod_template.evaluate_pod_condition()
        self.assertTrue(condition_result is True)

        pod_template.pod_expression = 'something wrong'

        exception_raised = False
        try:
            condition_result = pod_template.evaluate_pod_condition()
        except:
            exception_raised = True

        msg = 'evaluate_pod_condition() on wrong TAL expression shoul throw an exception'
        self.assertTrue(exception_raised, msg)

    def test_can_be_generated(self):
        """
        can_be_generated() should be the evaluation of:
        actived AND check_pod_good_pt() AND evaluate_pod_condition()

        Assign negative values to each of the terms and check the result.
        """
        context = self.portal
        pod_template = self.test_podtemplate
        can_be_generated = pod_template.can_be_generated(context)
        # case 0 (default) : True and ... and ...
        self.assertTrue(can_be_generated is True)

        pod_template.enabled = False
        can_be_generated = pod_template.can_be_generated(context)
        # case 1: False and ... and ...
        self.assertTrue(can_be_generated is False)
        pod_template.enabled = True
        pod_template.pod_portal_type = ('Event',)
        can_be_generated = pod_template.can_be_generated(context)
        # case 2: True and False and ... (Portal type isn't in selected list)
        self.assertTrue(can_be_generated is False)
        pod_template.pod_portal_type = ('Plone Site',)
        can_be_generated = pod_template.can_be_generated(context)
        # case 2 bis: True and True and ... (Portal type is in selected list)
        self.assertTrue(can_be_generated is True)
        pod_template.pod_portal_type = ()
        can_be_generated = pod_template.can_be_generated(context)
        # case 2 ter: True and True and ... (No selected list)
        self.assertTrue(can_be_generated is True)

        pod_template.enabled = lambda x: True
        pod_template.check_pod_good_pt = lambda x: []
        can_be_generated = pod_template.can_be_generated(context)
        # case 3: True and True and []
        self.assertTrue(can_be_generated == [])
