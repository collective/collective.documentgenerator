# -*- coding: utf-8 -*-
from Acquisition import aq_base
from collective.documentgenerator.content.pod_template import IConfigurablePODTemplate
from collective.documentgenerator.content.pod_template import PodFormatsValidator
from collective.documentgenerator.interfaces import IPODTemplateCondition
from collective.documentgenerator.testing import ConfigurablePODTemplateIntegrationTest
from collective.documentgenerator.testing import TEST_INSTALL_INTEGRATION
from plone import api
from zope.component import queryMultiAdapter
from zope.i18n import translate
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
        contents = self._edit_object(self.test_podtemplate)
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
        contents = self._edit_object(self.test_podtemplate)
        msg = "field 'style_template' is not editable"
        self.assertTrue('Modèle de style' in contents, msg)

    def test_merge_templates_attribute(self):
        test_podtemplate = aq_base(self.test_podtemplate)
        self.assertTrue(hasattr(test_podtemplate, 'merge_templates'))

    def test_merge_templates_field_display(self):
        self.browser.open(self.test_podtemplate.absolute_url())
        contents = self.browser.contents
        msg = "field 'merge_templates' is not displayed"
        self.assertTrue('id="form-widgets-merge_templates"' in contents, msg)
        msg = "field 'merge_templates' is not translated"
        self.assertTrue('Modèles à fusionner' in contents, msg)

    def test_merge_templates_field_edit(self):
        contents = self._edit_object(self.test_podtemplate)
        msg = "field 'merge_templates' is not editable"
        self.assertTrue('Modèles à fusionner' in contents, msg)


class TestConfigurablePODTemplateIntegration(ConfigurablePODTemplateIntegrationTest):
    """
    Test ConfigurablePODTemplate methods.
    """

    def test_get_file(self):
        msg = "Accessor 'get_file' does not return odt_file field value."

        reusable_template = self.portal.podtemplates.get('test_template_reusable')
        self.test_podtemplate.pod_template_to_use = reusable_template.UID()

        # template uses odt file from another
        self.assertEqual(self.test_podtemplate.get_file(), reusable_template.odt_file, msg)
        # template uses odt file from another
        self.test_podtemplate.odt_file = None
        self.assertEqual(self.test_podtemplate.get_file(), reusable_template.odt_file, msg)
        self.assertEqual(reusable_template.get_file(), reusable_template.odt_file, msg)
        # basic case without reuse
        self.test_podtemplate.pod_template_to_use = None
        self.assertEqual(self.test_podtemplate.get_file(), self.test_podtemplate.odt_file, msg)

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
        data = Dummy(
            merge_templates=[{'pod_context_name': u'det', 'value': u'1'}, {'pod_context_name': u'det', 'value': u'1'}])
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
        data = Dummy(merge_templates=[{'pod_context_name': u'same', 'value': u'1'},
                                      {'pod_context_name': u'same', 'value': u'1'}],
                     context_variables=[{'name': u'random1', 'value': u'1'}, {'name': u'random2', 'value': u'1'}])
        self.assertRaises(Invalid, fct, data)
        # revert
        data = Dummy(context_variables=[{'name': u'same', 'value': u'1'}, {'name': u'same', 'value': u'1'}],
                     merge_templates=[{'pod_context_name': u'random1', 'value': u'1'},
                                      {'pod_context_name': u'random2', 'value': u'1'}])
        self.assertRaises(Invalid, fct, data)
        # duplicate in both lists
        data = Dummy(
            merge_templates=[{'pod_context_name': u'det', 'value': u'1'}, {'pod_context_name': u'det', 'value': u'1'}],
            context_variables=[{'name': u'det', 'value': u'1'}, {'name': u'det', 'value': u'1'}])
        self.assertRaises(Invalid, fct, data)
        # duplicate 1 in each list
        data = Dummy(merge_templates=[{'pod_context_name': u'same', 'value': u'1'},
                                      {'pod_context_name': u'random1', 'value': u'1'}],
                     context_variables=[{'name': u'same', 'value': u'1'}, {'name': u'random2', 'value': u'1'}])
        self.assertRaises(Invalid, fct, data)
        # no exception
        data = Dummy(merge_templates=[{'pod_context_name': u'det', 'value': u'1'}],
                     context_variables=[{'name': u'something else', 'value': u'1'}])
        self.assertIsNone(fct(data))

    def test_validate_pod_file(self):
        class Dummy(object):
            def __init__(self, odt_file=None, pod_template_to_use=None):
                self.odt_file = odt_file
                self.pod_template_to_use = pod_template_to_use

        fct = IConfigurablePODTemplate.getTaggedValue('invariants')[1]

        # check no odt_file and no pod_template_to_use
        self.assertRaises(Invalid, fct, Dummy())
        Dummy(odt_file=self.test_podtemplate.odt_file)
        Dummy(pod_template_to_use=self.test_podtemplate.pod_template_to_use)
        Dummy(odt_file=self.test_podtemplate.odt_file, pod_template_to_use=self.test_podtemplate.pod_template_to_use)

    def test_validate_pod_template_to_use(self):
        class Dummy(object):
            def __init__(self, odt_file=None, pod_template_to_use=None, is_reusable=None):
                self.odt_file = odt_file
                self.pod_template_to_use = pod_template_to_use
                self.is_reusable = is_reusable

        fct = IConfigurablePODTemplate.getTaggedValue('invariants')[2]

        Dummy(odt_file=self.test_podtemplate.odt_file)
        Dummy(odt_file=self.test_podtemplate.odt_file, is_reusable=True)
        Dummy(odt_file=self.test_podtemplate.odt_file, is_reusable=False)
        Dummy(is_reusable=True)
        Dummy(is_reusable=False)

        data = Dummy(odt_file=self.test_podtemplate.odt_file, pod_template_to_use="test")
        self.assertRaises(Invalid, fct, data)

        data = Dummy(odt_file=self.test_podtemplate.odt_file, is_reusable=True, pod_template_to_use="test")
        self.assertRaises(Invalid, fct, data)

        data = Dummy(odt_file=self.test_podtemplate.odt_file, is_reusable=False, pod_template_to_use="test")
        self.assertRaises(Invalid, fct, data)

        data = Dummy(is_reusable=True, pod_template_to_use="test")
        self.assertRaises(Invalid, fct, data)

        Dummy(pod_template_to_use="test", is_reusable=False)

    def test_children_pod_template_content_provider(self):
        """Test how children_pod_template ContentProvider is rendered."""
        mother_template = self.portal.podtemplates.test_template_reusable
        child_template = self.portal.podtemplates.test_template_reuse
        self.assertTrue(child_template in mother_template.get_children_pod_template())
        # link to child is displayed in the mother view by the content provider
        self.assertTrue(child_template.absolute_url() in mother_template())

        # content provider is displayed in the view as well as in the edit form
        # view
        view_form = mother_template.restrictedTraverse('view')
        view_form.update()
        view_content_provider_widget = view_form.widgets['children_pod_template']
        rendered_view_form = view_form()
        rendered_view_widget = view_content_provider_widget.render()
        self.assertTrue(child_template.absolute_url() in view_form())
        self.assertTrue(rendered_view_widget in rendered_view_form)
        # edit
        edit_form = mother_template.restrictedTraverse('edit')
        edit_form.update()
        edit_content_provider_widget = edit_form.widgets['children_pod_template']
        rendered_edit_form = edit_form()
        rendered_edit_widget = view_content_provider_widget.render()
        self.assertTrue(child_template.absolute_url() in edit_form())
        self.assertTrue(rendered_edit_widget in rendered_edit_form)

        # we added convenient methods on the provider so it is displayed correctly
        # on forms calling widget.name, widget.value
        self.assertEqual(view_content_provider_widget.label, '')
        self.assertEqual(edit_content_provider_widget.label, '')
        self.assertEqual(view_content_provider_widget.name, 'children_pod_template')
        self.assertEqual(edit_content_provider_widget.name, 'children_pod_template')
        self.assertEqual(view_content_provider_widget.value, rendered_view_widget)
        self.assertEqual(edit_content_provider_widget.value, rendered_edit_widget)


class TestConfigurablePODTemplateValidator(ConfigurablePODTemplateIntegrationTest):
    def test_add_bad_formats_and_get_errormessage(self):
        pod_template = self.test_podtemplate
        pod_template.pod_formats.append('xls')
        view = pod_template.restrictedTraverse('edit')
        view.update()
        validator = PodFormatsValidator(pod_template,
                                        pod_template.REQUEST,
                                        view,
                                        IConfigurablePODTemplate['pod_formats'],
                                        view.widgets['pod_formats'])
        msg = translate(u"element_not_valid",
                        default=u"Element ${elem} is not valid for .${extension} template : \"${template}\"",
                        mapping={u"elem": "Microsoft Excel (.xls)",
                                 u"extension": "odt",
                                 u"template": pod_template.odt_file.filename})
        with self.assertRaises(Invalid) as cm:
            validator.validate(pod_template.pod_formats)
        self.assertEqual(msg, translate(cm.exception.message))
