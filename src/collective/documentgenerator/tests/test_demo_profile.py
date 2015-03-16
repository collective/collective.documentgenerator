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

        applyProfile(site, 'collective.documentgenerator:demo')

        msg = 'Pod templates folder should be unique'
        self.assertTrue(not hasattr(site, 'podtemplates-1'), msg)

    def test_PODTemplate_folder_out_of_navigation(self):
        site = api.portal.get()

        applyProfile(site, 'collective.documentgenerator:demo')

        msg = 'Pod templates folder should be out of navigation'
        self.assertTrue(site.podtemplates.exclude_from_nav(), msg)

    def test_PODTemplateModel_creation(self):
        site = api.portal.get()

        applyProfile(site, 'collective.documentgenerator:demo')

        msg = 'Test podtemplate doesn\'t exist'
        self.assertTrue(hasattr(site.podtemplates, 'test_template'), msg)
        self.assertTrue(site.podtemplates.test_template.portal_type == 'PODTemplate')

        msg = 'The second podtemplate doesn\'t exist'
        self.assertTrue(hasattr(site.podtemplates, 'test_template_bis'), msg)
        self.assertTrue(site.podtemplates.test_template_bis.portal_type == 'ConfigurablePODTemplate')

        applyProfile(site, 'collective.documentgenerator:demo')

        msg = 'Test pod templates should be unique'
        self.assertTrue(not hasattr(site.podtemplates, 'test_template-1'), msg)
        self.assertTrue(not hasattr(site.podtemplates, 'test_template_bis-1'), msg)

    def test_PODTemplateModel_out_of_navigation(self):
        site = api.portal.get()

        applyProfile(site, 'collective.documentgenerator:demo')

        msg = 'Test pod templates should be out of navigation'
        self.assertTrue(site.podtemplates.test_template.exclude_from_nav(), msg)

    def test_StyleTemplate_creation(self):
        site = api.portal.get()

        applyProfile(site, 'collective.documentgenerator:demo')

        msg = 'Test style template doesn\'t exist'
        self.assertTrue(hasattr(site.podtemplates, 'test_style_template'), msg)
        self.assertTrue(site.podtemplates.test_style_template.portal_type == 'StyleTemplate')

        applyProfile(site, 'collective.documentgenerator:demo')

        msg = 'Test style templates should be unique'
        self.assertTrue(not hasattr(site.podtemplates, 'test_style_template-1'), msg)

    def test_StyleTemplate_out_of_navigation(self):
        site = api.portal.get()

        applyProfile(site, 'collective.documentgenerator:demo')

        msg = 'Test style templates should be out of navigation'
        self.assertTrue(site.podtemplates.test_style_template.exclude_from_nav(), msg)
