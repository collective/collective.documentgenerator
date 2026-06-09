# -*- coding: utf-8 -*-

from collective.documentgenerator.testing import PODTemplateIntegrationTest
from plone import api
from Products.CMFPlone.utils import _createObjectByType


class TestSubTemplatesUsageView(PODTemplateIntegrationTest):
    """Test the 'sub-templates-usage' view.

    The demo profile creates a single 'sub_template' (title 'Header') in
    'podtemplates', used by 'test_template_multiple' and 'test_template_bis'.
    """

    def setUp(self):
        super(TestSubTemplatesUsageView, self).setUp()
        self.view = self.portal.restrictedTraverse("@@sub-templates-usage")

    def test_sub_templates_usage(self):
        entries = self.view.sub_templates_usage()
        # one entry per sub-template (here the single demo 'sub_template')
        self.assertEqual([e["sub_template"].getId for e in entries], ["sub_template"])
        # the only sub-template defines the whole common path -> empty rel_path
        self.assertEqual(entries[0]["rel_path"], u"")
        # both using templates share the same folder -> one group, sorted by title
        groups = entries[0]["groups"]
        self.assertEqual(len(groups), 1)
        self.assertEqual([t.getId() for t in groups[0]["templates"]], ["test_template_bis", "test_template_multiple"])

    def test_rel_path_strips_common_part(self):
        # add two more sub-templates in distinct sub-folders of 'podtemplates'
        pod = self.portal.podtemplates
        # following escape disallowed !
        folder_z = _createObjectByType("Folder", pod, "folder_z", title=u"Zeta")
        folder_a = _createObjectByType("Folder", pod, "folder_a", title=u"Alpha")
        api.content.create(type="SubTemplate", id="st_z", title=u"In Zeta", container=folder_z)
        api.content.create(type="SubTemplate", id="st_a", title=u"In Alpha", container=folder_a)

        entries = self.view.sub_templates_usage()
        rel_paths = [e["rel_path"] for e in entries]
        # 'podtemplates' is common to every sub-template and is stripped away;
        # the demo sub-template sits directly in 'podtemplates' -> empty rel_path.
        self.assertEqual(rel_paths, [u"", u"Alpha", u"Zeta"])
        # entries are ordered by the first-column path (rel_path) then by title
        self.assertEqual(
            [e["sub_template"].getId for e in entries],
            ["sub_template", "st_a", "st_z"],
        )
        # the common 'podtemplates' segment never appears in the displayed path
        pod_title = pod.Title()
        self.assertFalse(any(pod_title in rel_path for rel_path in rel_paths))
