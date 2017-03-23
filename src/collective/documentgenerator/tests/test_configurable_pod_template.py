# -*- coding: utf-8 -*-

from Acquisition import aq_base

from collective.documentgenerator.content.pod_template import IConfigurablePODTemplate
from collective.documentgenerator.interfaces import IPODTemplateCondition
from collective.documentgenerator.testing import ConfigurablePODTemplateIntegrationTest
from collective.documentgenerator.testing import TEST_INSTALL_INTEGRATION

from plone import api

from zope.component import queryMultiAdapter
from zope.interface import Invalid

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

    def test_pod_portal_types_attribute(self):
        test_podtemplate = aq_base(self.test_podtemplate)
        self.assertTrue(hasattr(test_podtemplate, 'pod_portal_types'))

    def test_pod_portal_types_field_display(self):
        self.browser.open(self.test_podtemplate.absolute_url())
        contents = self.browser.contents
        msg = "field 'pod_portal_types' is not displayed"
        self.assertTrue('id="form-widgets-pod_portal_types"' in contents, msg)
        msg = "field 'pod_portal_types' is not translated"
        self.assertTrue('Types de contenu autorisés' in contents, msg)

    def test_pod_portal_types_field_edit(self):
        self.browser.open(self.test_podtemplate.absolute_url() + '/edit')
        contents = self.browser.contents
        msg = "field 'pod_portal_types' is not editable"
        self.assertTrue('Types de contenu autorisés' in contents, msg)

    def test_style_template_attribute(self):
        test_podtemplate = aq_base(self.test_podtemplate)
        self.assertTrue(hasattr(test_podtemplate, 'style_template'))

    def test_style_template_field_display(self):
        self.browser.open(self.test_podtemplate.absolute_url())
        contents = self.browser.contents
        msg = "field 'style_template' is not displayed"
        self.assertTrue('id="form-widgets-style_template"' in contents, msg)
        msg = "field 'style_template' is not translated"
        self.assertTrue('Modèle de style' in contents, msg)

    def test_style_template_field_edit(self):
        self.browser.open(self.test_podtemplate.absolute_url() + '/edit')
        contents = self.browser.contents
        msg = "field 'style_template' is not editable"
        self.assertTrue('Modèle de style' in contents, msg)

    def test_merge_templates_attribute(self):
        test_podtemplate = aq_base(self.test_podtemplate)
        self.assertTrue(hasattr(test_podtemplate, 'merge_templates'))

    def test_merge_templates_field_display(self):
        self.browser.open(self.test_podtemplate.absolute_url())
        contents = self.browser.contents
        msg = "field 'merge_templates' is not displayed"
        self.assertTrue('for="form-widgets-merge_templates"' in contents, msg)
        msg = "field 'merge_templates' is not translated"
        self.assertTrue('Modèles à fusionner' in contents, msg)

    def test_merge_templates_field_edit(self):
        self.browser.open(self.test_podtemplate.absolute_url() + '/edit')
        contents = self.browser.contents
        msg = "field 'merge_templates' is not editable"
        self.assertTrue('Modèles à fusionner' in contents, msg)


class TestConfigurablePODTemplateIntegration(ConfigurablePODTemplateIntegrationTest):
    """
    Test ConfigurablePODTemplate methods.
    """

    def test_generation_condition_registration(self):
        from collective.documentgenerator.content.condition import ConfigurablePODTemplateCondition

        context = self.portal
        condition_obj = queryMultiAdapter(
            (self.test_podtemplate, context),
            IPODTemplateCondition,
        )

        self.assertTrue(isinstance(condition_obj, ConfigurablePODTemplateCondition))

    def test_can_be_generated(self):
        self.test_podtemplate.pod_portal_types = []
        self.assertTrue(self.test_podtemplate.can_be_generated(self.portal))

        # Disable the template.
        self.test_podtemplate.enabled = False
        msg = 'disabled template should not be generated'
        self.assertTrue(not self.test_podtemplate.can_be_generated(self.portal), msg)
        # may be generated if enabled
        self.test_podtemplate.enabled = True
        self.assertTrue(self.test_podtemplate.can_be_generated(self.portal))

        # Restrict allowed types to 'File'.
        self.test_podtemplate.enabled = True
        self.test_podtemplate.pod_portal_types = ['File']
        msg = 'disabled template should not be generated'
        self.assertTrue(not self.test_podtemplate.can_be_generated(self.portal), msg)
        # may be generated on right context
        self.test_podtemplate.pod_portal_types = ['Plone Site']
        self.assertTrue(self.test_podtemplate.can_be_generated(self.portal))

        # Use a tal_condition, moreover test extra_expr_ctx
        # context/here is the element we generate the template from, here self.portal
        self.test_podtemplate.tal_condition = "python: context.portal_type == 'Document'"
        self.assertFalse(self.test_podtemplate.can_be_generated(self.portal))
        self.test_podtemplate.tal_condition = "python: context.portal_type == 'Plone Site'"
        self.assertTrue(self.test_podtemplate.can_be_generated(self.portal))
        self.test_podtemplate.tal_condition = "python: here.portal_type == 'Plone Site'"
        self.assertTrue(self.test_podtemplate.can_be_generated(self.portal))
        # we have also 'template' as extra_expr_ctx
        self.test_podtemplate.tal_condition = "python: template.getId() == 'wrong_id'"
        self.assertFalse(self.test_podtemplate.can_be_generated(self.portal))
        self.test_podtemplate.tal_condition = "python: template.getId() == 'test_template_bis'"
        self.assertTrue(self.test_podtemplate.can_be_generated(self.portal))

    def test_get_style_template(self):
        style_template = self.portal.podtemplates.test_style_template
        pod_template = self.test_podtemplate
        self.assertTrue(pod_template.get_style_template() == style_template)

    def test_get_templates_to_merge(self):
        pod_template = self.test_podtemplate

        # empty the field
        pod_template.merge_templates = []
        to_merge = pod_template.get_templates_to_merge()
        self.assertTrue(len(to_merge) == 0)

        # set the field 'merge_templates' with some value
        pod_template.merge_templates = [
            {
                'template': pod_template.UID(),
                'pod_context_name': 'hello',
                'do_rendering': False,
            }
        ]
        to_merge = pod_template.get_templates_to_merge()
        self.assertTrue(len(to_merge) == 1)
        self.assertTrue(to_merge['hello'] == (pod_template, False))

    def test_get_available_formats(self):
        self.assertEqual(self.test_podtemplate.get_available_formats(), self.test_podtemplate.pod_formats)

    def test_get_context_variables(self):
        self.assertDictEqual(self.test_podtemplate.get_context_variables(), {'details': '1'})

    def test_validate_context_variables(self):
        class Dummy(object):
            def __init__(self, context_variables=None, merge_templates=None):
                self.context_variables = context_variables
                self.merge_templates = merge_templates

        fct = IConfigurablePODTemplate.getTaggedValue('invariants')[0]
        # check no sub template and no variable
        self.assertIsNone(fct(Dummy()))

        # check no sub template but variables present
        # check forbidden name
        data = Dummy(context_variables=[{'name': u'uids', 'value': u'1'}])
        self.assertRaises(Invalid, fct, data)
        # check duplicated name
        data = Dummy(context_variables=[{'name': u'det', 'value': u'1'}, {'name': u'det', 'value': u'1'}])
        self.assertRaises(Invalid, fct, data)
        # no exception
        data = Dummy(context_variables=[{'name': u'det', 'value': u'1'}])
        self.assertIsNone(fct(data))

        # check no variables but sub template present
        # check forbidden name
        data = Dummy(merge_templates=[{'pod_context_name': u'uids', 'value': u'1'}])
        self.assertRaises(Invalid, fct, data)
        # check duplicated name
        data = Dummy(merge_templates=[{'pod_context_name': u'det', 'value': u'1'}, {'pod_context_name': u'det', 'value': u'1'}])
        self.assertRaises(Invalid, fct, data)
        # no exception
        data = Dummy(merge_templates=[{'pod_context_name': u'det', 'value': u'1'}])
        self.assertIsNone(fct(data))

        # check both variables but sub template present
        # check forbidden name
        data = Dummy(context_variables=[{'name': u'det', 'value': u'1'}],
                     merge_templates=[{'pod_context_name': u'uids', 'value': u'1'}])
        self.assertRaises(Invalid, fct, data)
        # revert
        data = Dummy(merge_templates=[{'pod_context_name': u'det', 'value': u'1'}],
                     context_variables=[{'name': u'self', 'value': u'1'}])
        self.assertRaises(Invalid, fct, data)
        # check duplicated name
        data = Dummy(merge_templates=[{'pod_context_name': u'same', 'value': u'1'}, {'pod_context_name': u'same', 'value': u'1'}],
                     context_variables=[{'name': u'random1', 'value': u'1'}, {'name': u'random2', 'value': u'1'}])
        self.assertRaises(Invalid, fct, data)
        # revert
        data = Dummy(context_variables=[{'name': u'same', 'value': u'1'}, {'name': u'same', 'value': u'1'}],
                     merge_templates=[{'pod_context_name': u'random1', 'value': u'1'}, {'pod_context_name': u'random2', 'value': u'1'}])
        self.assertRaises(Invalid, fct, data)
        # duplicate in both lists
        data = Dummy(merge_templates=[{'pod_context_name': u'det', 'pod_context_name': u'1'}, {'pod_context_name': u'det', 'value': u'1'}],
                     context_variables=[{'name': u'det', 'value': u'1'}, {'name': u'det', 'value': u'1'}])
        self.assertRaises(Invalid, fct, data)
        # duplicate 1 in each list
        data = Dummy(merge_templates=[{'pod_context_name': u'same', 'value': u'1'}, {'pod_context_name': u'random1', 'value': u'1'}],
                     context_variables=[{'name': u'same', 'value': u'1'}, {'name': u'random2', 'value': u'1'}])
        self.assertRaises(Invalid, fct, data)
        # no exception
        data = Dummy(merge_templates=[{'pod_context_name': u'det', 'value': u'1'}],
                     context_variables=[{'name': u'something else', 'value': u'1'}])
        self.assertIsNone(fct(data))
