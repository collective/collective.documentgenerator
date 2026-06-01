# -*- coding: utf-8 -*-

from collective.documentgenerator.testing import POD_TEMPLATE_INTEGRATION

import unittest


class TestSubTemplatesUsageView(unittest.TestCase):
    """Test the 'sub-templates-usage' view.

    The demo profile creates a single 'sub_template' used by
    'test_template_multiple' and 'test_template_bis', both in 'podtemplates'.
    """

    layer = POD_TEMPLATE_INTEGRATION

    def setUp(self):
        self.view = self.layer["portal"].restrictedTraverse("@@sub-templates-usage")

    def test_sub_templates_usage(self):
        entries = self.view.sub_templates_usage()
        # one entry per sub-template (here the single demo 'sub_template')
        self.assertEqual([e["sub_template"].getId for e in entries], ["sub_template"])
        # both using templates share the same folder -> one group, sorted by title
        groups = entries[0]["groups"]
        self.assertEqual(len(groups), 1)
        self.assertEqual([t.getId() for t in groups[0]["templates"]], ["test_template_bis", "test_template_multiple"])
