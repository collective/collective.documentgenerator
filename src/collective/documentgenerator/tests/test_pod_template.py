# -*- coding: utf-8 -*-

from Acquisition import aq_base

from collective.documentgenerator.content.condition import PODTemplateCondition
from collective.documentgenerator.content.merge_templates import TemplatesToMergeForPODTemplate
from collective.documentgenerator.content.pod_template import IPODTemplate
from collective.documentgenerator.interfaces import IPODTemplateCondition
from collective.documentgenerator.interfaces import ITemplatesToMerge
from collective.documentgenerator.testing import TEST_INSTALL_INTEGRATION
from collective.documentgenerator.testing import PODTemplateIntegrationTest

from plone import api
from plone.namedfile.file import NamedBlobFile

from zope.component import getGlobalSiteManager
from zope.component import queryAdapter
from zope.component import queryMultiAdapter
from zope.interface import Interface

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


class TestPODTemplateFields(PODTemplateIntegrationTest):
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

    def test_initial_md5_attribute(self):
        test_podtemplate = aq_base(self.test_podtemplate)
        self.assertTrue(hasattr(test_podtemplate, 'initial_md5'))

    def test_initial_md5_field_display(self):
        self.browser.open(self.test_podtemplate.absolute_url())
        contents = self.browser.contents
        msg = "field 'initial_md5' is displayed"
        self.assertTrue('id="form-widgets-initial_md5"' not in contents, msg)

    def test_initial_md5_field_edit(self):
        self.browser.open(self.test_podtemplate.absolute_url() + '/edit')
        contents = self.browser.contents
        msg = "field 'initial_md5' is editable"
        self.assertTrue('md5' not in contents, msg)

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


class TestPODTemplateIntegration(PODTemplateIntegrationTest):
    """
    Test PODTemplate methods.
    """

    def test_get_file(self):
        expected_file = self.test_podtemplate.odt_file

        self.test_podtemplate.odt_file = expected_file
        odt_file = self.test_podtemplate.get_file()
        msg = "Accessor 'get_file' does not return odt_file field value."
        self.assertTrue(odt_file == expected_file, msg)

    def test_default_generation_condition_registration(self):
        context = self.portal
        condition_obj = queryMultiAdapter(
            (self.test_podtemplate, context),
            IPODTemplateCondition,
        )

        self.assertTrue(isinstance(condition_obj, PODTemplateCondition))

    def test_can_be_generated(self):
        self.assertTrue(self.test_podtemplate.can_be_generated(self.portal))

        # Disable the template.
        self.test_podtemplate.enabled = False
        msg = 'disabled template should not be generated'
        self.assertTrue(not self.test_podtemplate.can_be_generated(self.portal), msg)

    def test_custom_generation_condition(self):
        """
        Register a custom condition and see if its taken into account by our test_podtemplate.
        """
        pod_template = self.test_podtemplate
        can_be_generated = pod_template.can_be_generated(self.portal)
        self.assertTrue(can_be_generated is True)

        class CustomCondition(PODTemplateCondition):
            def evaluate(self):
                return 'yolo'

        gsm = getGlobalSiteManager()
        gsm.registerAdapter(CustomCondition, (IPODTemplate, Interface), IPODTemplateCondition)

        can_be_generated = pod_template.can_be_generated(self.portal)
        self.assertTrue(can_be_generated == 'yolo')

        # finally, unregister our adapter...
        gsm.registerAdapter(PODTemplateCondition, (IPODTemplate, Interface), IPODTemplateCondition)

    def test_get_style_template(self):
        pod_template = self.test_podtemplate
        self.assertTrue(pod_template.get_style_template() is None)

    def test_default_merge_templates_registration(self):
        adapter = queryAdapter(self.test_podtemplate, ITemplatesToMerge)
        self.assertTrue(isinstance(adapter, TemplatesToMergeForPODTemplate))

    def test_template_has_been_modified_method(self):
        pod_template = self.test_podtemplate

        setup_tool = api.portal.get_tool('portal_setup')
        demo_profile = setup_tool.getProfileInfo('collective.documentgenerator:demo')
        template_path = '{}/templates/styles.odt'.format(demo_profile.get('path'))
        template_file = file(template_path, 'rb').read()
        blob_file = NamedBlobFile(data=template_file, contentType='applications/odt')

        pod_template.odt_file = blob_file

        self.assertTrue(pod_template.has_been_modified())

    def test_get_available_formats(self):
        self.assertEquals(self.test_podtemplate.get_available_formats(), ['odt', ])
