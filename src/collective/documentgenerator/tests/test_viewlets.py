# -*- coding: utf-8 -*-

from collective.documentgenerator.testing import POD_TEMPLATE_INTEGRATION
from collective.documentgenerator.viewlets.sub_template_usage import SubTemplateUsageViewlet

import unittest


class TestSubTemplateUsageViewlet(unittest.TestCase):
    """Test the 'sub-template-usage' viewlet on a SubTemplate.

    The demo profile creates a 'sub_template' used by 'test_template_multiple'
    and 'test_template_bis', both in the 'podtemplates' folder.
    """

    layer = POD_TEMPLATE_INTEGRATION

    def setUp(self):
        portal = self.layer['portal']
        sub_template = portal.podtemplates.sub_template
        self.viewlet = SubTemplateUsageViewlet(sub_template, portal.REQUEST, None, None)

    def test_available_and_using_templates_grouped_by_path(self):
        self.assertTrue(self.viewlet.available())
        groups = self.viewlet.get_using_templates_by_path()
        # both templates live in the same folder -> a single group, sorted by title
        self.assertEqual(len(groups), 1)
        self.assertEqual([t.getId() for t in groups[0]['templates']],
                         ['test_template_bis', 'test_template_multiple'])
