# -*- coding: utf-8 -*-

from collective.documentgenerator.testing import TEST_INSTALL_INTEGRATION

from plone import api
from plone.app.testing import applyProfile

import unittest


class TestDemoProfile(unittest.TestCase):

    layer = TEST_INSTALL_INTEGRATION

    def test_demo_profile_is_registered(self):
        portal_setup = api.portal.get_tool(name='portal_setup')
        demo_profile_name = u'collective.documentgenerator:demo'
        profile_ids = [info['id'] for info in portal_setup.listProfileInfo()]
        msg = 'demo profile is not registered'
        self.assertTrue(demo_profile_name in profile_ids, msg)

    def test_PODTemplate_folder_creation(self):
        site = api.portal.get()

        msg = 'Pod templates folder should not exist'
        self.assertTrue(not hasattr(site, 'podtemplates'), msg)

        applyProfile(site, 'collective.documentgenerator:demo')

        msg = 'Pod templates folder doesn\'t exist'
        self.assertTrue(hasattr(site, 'podtemplates'), msg)
        self.assertTrue(site.podtemplates.portal_type == 'Folder')
