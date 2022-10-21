# -*- coding: utf-8 -*-

from collective.documentgenerator.events.styles_events import _update_template_styles
from collective.documentgenerator.events.styles_events import update_styles_of_all_PODtemplate
from collective.documentgenerator.testing import PODTemplateIntegrationTest
from plone import api
from plone.namedfile.file import NamedBlobFile
from zExceptions import Redirect
from zope.event import notify
from zope.interface import Interface
from zope.lifecycleevent import Attributes
from zope.lifecycleevent import ObjectModifiedEvent

import os


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

    def test_clean_notes(self):
        """When PODTemplate created or modified, the "odt_file" note are cleaned."""
        # original template_to_clean.odt holds dirty note
        filename = u'template_to_clean.odt'
        dirty_note = 'from xhtml(self.getMotivation() + </text:span>' \
            '<text:span text:style-name="T1">self.getDecision())</text:span>'
        cleaned_note = 'from xhtml(self.getMotivation() + self.getDecision())'
        current_path = os.path.dirname(__file__)
        dirty_data = open(os.path.join(current_path, filename), 'r').read()
        dirty_content_xml = self.get_odt_content_xml(dirty_data)
        self.assertTrue(dirty_note in dirty_content_xml)
        self.assertFalse(cleaned_note in dirty_content_xml)

        # create a new pod template it will be cleaned
        pod_template = api.content.create(
            type='ConfigurablePODTemplate',
            id='template_to_clean',
            title=u'Template to clean',
            odt_file=NamedBlobFile(
                data=dirty_data,
                contentType='application/vnd.oasis.opendocument.text',
                filename=filename,
            ),
            pod_formats=['odt'],
            container=self.portal.podtemplates
        )
        cleaned_content_xml = self.get_odt_content_xml(pod_template.odt_file.data)
        self.assertFalse(dirty_note in cleaned_content_xml)
        self.assertTrue(cleaned_note in cleaned_content_xml)
        # same behavior than style modification: template is considered unchanged
        self.assertFalse(pod_template.has_been_modified())

        # when updating file, new file is cleaned as well
        pod_template.odt_file = NamedBlobFile(
            data=dirty_data,
            contentType='application/vnd.oasis.opendocument.text',
            filename=filename,
        )
        self.assertTrue(pod_template.has_been_modified())  # template is manually changed
        notify(ObjectModifiedEvent(pod_template, Attributes(Interface, 'odt_file')))
        cleaned_content_xml = self.get_odt_content_xml(pod_template.odt_file.data)
        self.assertFalse(dirty_note in cleaned_content_xml)
        self.assertTrue(cleaned_note in cleaned_content_xml)

    def test_default_page_style_for_mailing(self):
        """When a mailing PODTemplate created or modified, set a default page style on it."""
        filename = u'template_without_style_page.odt'
        current_path = os.path.dirname(__file__)
        odt_data = open(os.path.join(current_path, filename), 'r').read()
        # activate the auto page style option
        api.portal.set_registry_record(
            'collective.documentgenerator.browser.controlpanel.'
            'IDocumentGeneratorControlPanelSchema.force_default_page_style_for_mailing',
            True
        )
        pod_template = api.content.create(
            type='ConfigurablePODTemplate',
            id='template_to_style',
            title=u'Template to clean',
            odt_file=NamedBlobFile(
                data=odt_data,
                contentType='application/vnd.oasis.opendocument.text',
                filename=filename,
            ),
            pod_formats=['odt'],
            container=self.portal.podtemplates,
            mailing_loop_template=1,
        )
        notify(ObjectModifiedEvent(pod_template))
        # the page style should have been set -> odt contents are different
        self.assertNotEqual(odt_data, pod_template.odt_file.data)

    def test_default_page_style_for_mailing_disabled(self):
        """When a mailing PODTemplate created or modified, set a default page style on it
        only if the setting 'force_default_page_style_for_mailing' is set to True."""
        filename = u'template_without_style_page.odt'
        current_path = os.path.dirname(__file__)
        odt_data = open(os.path.join(current_path, filename), 'r').read()
        # activate the auto page style option
        api.portal.set_registry_record(
            'collective.documentgenerator.browser.controlpanel.'
            'IDocumentGeneratorControlPanelSchema.force_default_page_style_for_mailing',
            False
        )
        pod_template = api.content.create(
            type='ConfigurablePODTemplate',
            id='template_to_style',
            title=u'Template to clean',
            odt_file=NamedBlobFile(
                data=odt_data,
                contentType='application/vnd.oasis.opendocument.text',
                filename=filename,
            ),
            pod_formats=['odt'],
            container=self.portal.podtemplates,
            mailing_loop_template=1,
        )
        notify(ObjectModifiedEvent(pod_template))
        # no page style should have been set -> odt contents are still the same
        self.assertEqual(odt_data, pod_template.odt_file.data)
