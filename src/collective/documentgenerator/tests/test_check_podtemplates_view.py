# -*- coding: utf-8 -*-
from collective.documentgenerator.content.pod_template import IPODTemplate
from collective.documentgenerator.content.pod_template import PODTemplate
from collective.documentgenerator.testing import PODTemplateIntegrationTest
from collective.documentgenerator.utils import translate as _
from plone import api
from plone.namedfile import NamedBlobFile

import os


class TestCheckPodTemplatesView(PODTemplateIntegrationTest):
    """Test Dexterity helper view."""

    def setUp(self):
        super(TestCheckPodTemplatesView, self).setUp()

    def _assert_messages_format(
        self,
        check_view,
        nb_clean,
        nb_error=0,
        nb_no_obj_found=0,
        nb_no_pod_portal_types=0,
        nb_not_enabled=0,
        nb_not_managed=0,
    ):
        def _assert_fmt(lst, length, var_name):
            if length > 0:
                true_lst = lst["/plone/podtemplates"]
                self.assertEqual(
                    len(true_lst),
                    length,
                    "{} should have {} element, not {}".format(
                        var_name, length, len(true_lst)
                    ),
                )
                for element in true_lst:
                    self.assertGreaterEqual(len(element), 2)
                    self.assertIsInstance(element[0], PODTemplate)
                    self.assertNotIsInstance(element[1], PODTemplate)
                    self.assertEqual(len(element), 3)
                    if element[-1]:
                        self.assertEqual(len(element[-1]), 2)
                        self.assertEqual(element[-1][0], _("Error"))
                        self.assertIsInstance(element[-1][1], str)
            else:
                self.assertEqual(len(lst), 0, "{} should be empty".format(var_name))

        messages = check_view.messages
        self.assertEqual(len(messages), 6)
        self.assertEqual(len(check_view.left_to_verify), 0)
        self.assertDictEqual(messages["check_pod_template_error"], check_view.error)
        self.assertDictEqual(
            messages["check_pod_template_no_obj_found"], check_view.no_obj_found
        )
        self.assertDictEqual(
            messages["check_pod_template_no_pod_portal_types"],
            check_view.no_pod_portal_types,
        )
        self.assertDictEqual(
            messages["check_pod_template_not_enabled"], check_view.not_enabled
        )
        self.assertDictEqual(
            messages["check_pod_template_not_managed"], check_view.not_managed
        )
        self.assertDictEqual(messages["check_pod_template_clean"], check_view.clean)

        _assert_fmt(check_view.clean, nb_clean, "clean")
        _assert_fmt(check_view.error, nb_error, "error")
        _assert_fmt(check_view.no_obj_found, nb_no_obj_found, "no_obj_found")
        _assert_fmt(
            check_view.no_pod_portal_types,
            nb_no_pod_portal_types,
            "no_pod_portal_types",
        )
        _assert_fmt(check_view.not_enabled, nb_not_enabled, "not_enabled")
        _assert_fmt(check_view.not_managed, nb_not_managed, "not_managed")

    def add_failing_template(self):
        current_path = os.path.dirname(__file__)
        failing_template_data = open(
            os.path.join(current_path, "failing_template.odt"), "r"
        ).read()
        self.failing_template = api.content.create(
            type="ConfigurablePODTemplate",
            id="failing_template",
            title=_(u"Failing template"),
            odt_file=NamedBlobFile(
                data=failing_template_data,
                contentType="application/vnd.oasis.opendocument.text",
                filename=u"modele_general.odt",
            ),
            pod_formats=["odt"],
            container=self.portal.podtemplates,
            exclude_from_nav=True,
        )
        self.failing_template.reindexObject()

    def test_view_check_pod_templates_message(self):
        # assert every pod templates are checked at least once (SubTemplates may be referenced multiple times)
        catalog = api.portal.get_tool("portal_catalog")
        brains = catalog(object_provides=IPODTemplate.__identifier__)
        pod_templates = []
        for brain in brains:
            pod_templates.append(brain.getObject())
        self.assertEqual(len(brains), 9)

        check_view = self.portal.restrictedTraverse("@@check-pod-templates")
        check_view()
        # default everything should be clean
        self._assert_messages_format(check_view, 10)

        self.add_failing_template()
        # test no_pod_portal_types
        check_view()
        self._assert_messages_format(check_view, 10, nb_no_pod_portal_types=1)
        # test error
        self.failing_template.pod_portal_types = ["Folder"]
        check_view()
        self._assert_messages_format(check_view, 10, nb_error=1)
        # test no_obj_found
        self.failing_template.pod_portal_types = ["News Item"]
        check_view()
        self._assert_messages_format(check_view, 10, nb_no_obj_found=1)
        # test not_enabled
        self.failing_template.enabled = False
        check_view()
        self._assert_messages_format(check_view, 10, nb_not_enabled=1)

        # test not_managed

        def exclude_more_pod_portal_types():
            return ["StyleTemplate", "PODTemplate"]

        check_view.excluded_pod_portal_types = exclude_more_pod_portal_types
        check_view()
        self._assert_messages_format(check_view, 9, nb_not_managed=1, nb_not_enabled=1)
