# -*- coding: utf-8 -*-
from collective.documentgenerator.content.pod_template import PODTemplate, IPODTemplate
from collective.documentgenerator.testing import PODTemplateIntegrationTest
from collective.documentgenerator.utils import translate as _
from plone import api


class TestCheckPodTemplatesView(PODTemplateIntegrationTest):

    """Test Dexterity helper view."""

    def setUp(self):
        super(TestCheckPodTemplatesView, self).setUp()

    def test_view_check_pod_tamplates_message(self):
        check_view = self.portal.restrictedTraverse('@@check-pod-templates')
        html_view = check_view()
        messages = check_view.messages

        self.assertEqual(len(messages), 6)
        self.assertEqual(len(check_view.left_to_verify), 0)
        self.assertListEqual(messages[_("check_pod_template_error")], check_view.error)
        self.assertListEqual(messages[_("check_pod_template_no_obj_found")], check_view.no_obj_found)
        self.assertListEqual(messages[_("check_pod_template_no_pod_portal_types")], check_view.no_pod_portal_types)
        self.assertListEqual(messages[_("check_pod_template_not_enabled")], check_view.not_enabled)
        self.assertListEqual(messages[_("check_pod_template_not_managed")], check_view.not_managed)
        self.assertListEqual(messages[_("check_pod_template_clean")], check_view.clean)

        self.assertEqual(len(check_view.error), 2)
        for error in check_view.error:
            self.assertEqual(len(error), 3)
            self.assertIsInstance(error[0], PODTemplate)
            self.assertNotIsInstance(error[1], PODTemplate)
            self.assertEqual(len(error[-1]), 2)
            self.assertEqual(error[-1][0], _("Error"))
            self.assertIsInstance(error[-1][1], str)

        self.assertEqual(len(check_view.no_obj_found), 0)
        self.assertEqual(len(check_view.no_pod_portal_types), 0)
        self.assertEqual(len(check_view.not_enabled), 0)
        self.assertEqual(len(check_view.not_managed), 0)

        self.assertEqual(len(check_view.clean), 8)
        for clean in check_view.clean:
            self.assertEqual(len(clean), 2)
            self.assertIsInstance(clean[0], PODTemplate)
            self.assertNotIsInstance(clean[1], PODTemplate)

        # assert every pod templates are checked at least once (SubTemplates may be referenced multiple times)
        catalog = api.portal.get_tool("portal_catalog")
        brains = catalog(object_provides=IPODTemplate.__identifier__)
        total_nb_checked = len(check_view.error) + len(check_view.clean)
        self.assertGreaterEqual(total_nb_checked, len(brains))



