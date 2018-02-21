# -*- coding: utf-8 -*-
from collective.documentgenerator.events.styles_events import _update_template_styles
from collective.documentgenerator.events.styles_events import update_styles_of_all_PODtemplate
from collective.documentgenerator.testing import PODTemplateIntegrationTest
from plone import api
from zExceptions import Redirect


class TestEvents(PODTemplateIntegrationTest):
    """
    Test events methods.
    """

    def test_update_styles_of_all_PODtemplate(self):
        # we use a ConfigurablePODTemplate to test style modification
        style_template = self.portal.podtemplates.get('test_style_template')
        # just call the function to pass on code
        update_styles_of_all_PODtemplate(style_template, None)

    def test__update_template_styles(self):
        # style update is already tested in test_utils.py
        # this is done to check error management
        template = self.portal.podtemplates.get('test_template_multiple')
        self.assertRaises(Redirect, _update_template_styles, template, None)

    def _get_new_template_reusing_another(self, id='test_template_reuse_temp', reuse_other=True):
        uid = None
        if reuse_other:
            uid = self.portal.podtemplates.get('test_template_reusable').UID()

        portal = api.portal.get()
        pod_folder = getattr(portal, 'podtemplates')
        api.content.create(
            pod_template_to_use=uid,
            type='ConfigurablePODTemplate',
            id=id,
            title=u'Temporary Reuse Test Template',
            container=pod_folder,
            exclude_from_nav=True,
            pod_formats=['odt', 'pdf', 'doc', 'docx'],
            pod_portal_types=['Document'],
        )
        return getattr(pod_folder, id)

    def test_crud_configurable_template_reusing_another(self):
        reusable_template = self.portal.podtemplates.get('test_template_reusable')
        template_reuse = self.portal.podtemplates.get('test_template_reuse')
        self.assertSetEqual(reusable_template.get_children_pod_template(), {template_reuse})

        temp_template = self._get_new_template_reusing_another()
        self.assertSetEqual(reusable_template.get_children_pod_template(), {temp_template, template_reuse})

        temp_template.pod_template_to_use = None
        self.assertSetEqual(reusable_template.get_children_pod_template(), {template_reuse})

        temp_template.pod_template_to_use = reusable_template.UID()
        self.assertSetEqual(reusable_template.get_children_pod_template(), {temp_template, template_reuse})

        api.content.delete(temp_template)
        self.assertEqual(reusable_template.get_children_pod_template(), {template_reuse})
