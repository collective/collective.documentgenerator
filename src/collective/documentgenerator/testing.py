# -*- coding: utf-8 -*-
"""Base module for unittesting."""

from plone import api

from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import login
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import TEST_USER_PASSWORD
from plone.testing import z2

import collective.documentgenerator

import transaction

import unittest


class NakedPloneLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        """Set up Zope."""
        # Load ZCML
        self.loadZCML(package=collective.documentgenerator,
                      name='testing.zcml')
        z2.installProduct(app, 'collective.documentgenerator')

    def tearDownZope(self, app):
        """Tear down Zope."""
        z2.uninstallProduct(app, 'collective.documentgenerator')

NAKED_PLONE_FIXTURE = NakedPloneLayer(
    name="NAKED_PLONE_FIXTURE"
)

NAKED_PLONE_INTEGRATION = IntegrationTesting(
    bases=(NAKED_PLONE_FIXTURE,),
    name="NAKED_PLONE_INTEGRATION"
)


class DocumentgeneratorLayer(NakedPloneLayer):

    def setUpPloneSite(self, portal):
        """Set up Plone."""
        # Install into Plone site using portal_setup
        applyProfile(portal, 'collective.documentgenerator:default')

        # Login and create some test content
        setRoles(portal, TEST_USER_ID, ['Manager'])
        login(portal, TEST_USER_NAME)

        # Commit so that the test browser sees these objects
        transaction.commit()


TEST_INSTALL_FIXTURE = DocumentgeneratorLayer(
    name="TEST_INSTALL_FIXTURE"
)

TEST_INSTALL_INTEGRATION = IntegrationTesting(
    bases=(TEST_INSTALL_FIXTURE,),
    name="TEST_INSTALL_INTEGRATION"
)


TEST_INSTALL_FUNCTIONAL = FunctionalTesting(
    bases=(TEST_INSTALL_FIXTURE,),
    name="TEST_INSTALL_FUNCTIONAL"
)


class ExamplePODTemplateLayer(DocumentgeneratorLayer):

    def setUpPloneSite(self, portal):
        super(ExamplePODTemplateLayer, self).setUpPloneSite(portal)

        applyProfile(portal, 'collective.documentgenerator:demo')
        applyProfile(portal, 'collective.documentgenerator:testing')

        # Commit so that the test browser sees these objects
        transaction.commit()


EXAMPLE_POD_TEMPLATE_FIXTURE = ExamplePODTemplateLayer(
    name="EXAMPLE_POD_TEMPLATE_FIXTURE"
)

EXAMPLE_POD_TEMPLATE_INTEGRATION = IntegrationTesting(
    bases=(EXAMPLE_POD_TEMPLATE_FIXTURE,),
    name="EXAMPLE_POD_TEMPLATE_INTEGRATION"
)

EXAMPLE_POD_TEMPLATE_FUNCTIONAL = FunctionalTesting(
    bases=(EXAMPLE_POD_TEMPLATE_FIXTURE,),
    name="EXAMPLE_POD_TEMPLATE_FUNCTIONAL"
)


ACCEPTANCE = FunctionalTesting(
    bases=(
        EXAMPLE_POD_TEMPLATE_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        z2.ZSERVER_FIXTURE
    ),
    name="ACCEPTANCE"
)


class BaseTest(unittest.TestCase):
    """
    Helper class for tests.
    """

    def setUp(self):
        self.portal = self.layer['portal']


class BrowserTest(BaseTest):
    """
    Helper class for Browser tests.
    """

    def setUp(self):
        super(BrowserTest, self).setUp()
        self.browser = z2.Browser(self.portal)
        self.browser.handleErrors = False

    def browser_login(self, user, password):
        login(self.portal, user)
        self.browser.open(self.portal.absolute_url() + '/logout')
        self.browser.open(self.portal.absolute_url() + "/login_form")
        self.browser.getControl(name='__ac_name').value = user
        self.browser.getControl(name='__ac_password').value = password
        self.browser.getControl(name='submit').click()


class PODTemplateIntegrationTest(BrowserTest):
    """Base class for integration browser tests."""

    layer = EXAMPLE_POD_TEMPLATE_INTEGRATION

    def setUp(self):
        super(PODTemplateIntegrationTest, self).setUp()
        self.test_podtemplate = self.portal.podtemplates.get('test_template')
        self.browser_login(TEST_USER_NAME, TEST_USER_PASSWORD)


class PODTemplateFunctionalTest(BrowserTest):
    """Base class for functional browser tests."""

    layer = EXAMPLE_POD_TEMPLATE_FUNCTIONAL

    def setUp(self):
        super(PODTemplateFunctionalTest, self).setUp()
        self.test_podtemplate = self.portal.podtemplates.get('test_template_bis')
        self.browser_login(TEST_USER_NAME, TEST_USER_PASSWORD)


class ConfigurablePODTemplateIntegrationTest(BrowserTest):
    """Base class for integration tests."""

    layer = EXAMPLE_POD_TEMPLATE_INTEGRATION

    def setUp(self):
        super(ConfigurablePODTemplateIntegrationTest, self).setUp()
        self.test_podtemplate = self.portal.podtemplates.get('test_template_bis')
        self.browser_login(TEST_USER_NAME, TEST_USER_PASSWORD)


class ArchetypesIntegrationTests(BaseTest):
    """Base class for Archetypes implementation tests."""

    layer = EXAMPLE_POD_TEMPLATE_INTEGRATION

    def setUp(self):
        super(ArchetypesIntegrationTests, self).setUp()

        # allow AT Topic creation anywhere on the site
        portal_types = api.portal.get_tool('portal_types')
        portal_types.Topic.global_allow = True

        # create our AT test object: a Topic
        AT_topic = api.content.create(
            type='Topic',
            id='AT_topic',
            container=self.portal
        )
        self.AT_topic = AT_topic


class ArchetypesFunctionnalTests(ArchetypesIntegrationTests):
    """Base class for Archetypes functional tests."""

    layer = EXAMPLE_POD_TEMPLATE_FUNCTIONAL


class DexterityIntegrationTests(BaseTest):

    """Base class for Dexterity implementation tests."""

    layer = EXAMPLE_POD_TEMPLATE_INTEGRATION

    def setUp(self):
        super(DexterityIntegrationTests, self).setUp()

        # create a test content type
        self.content = api.content.create(
            container=self.portal, id='johndoe', type="member")


class DexterityFunctionnalTests(DexterityIntegrationTests):
    """Base class for Dexterity functional tests."""

    layer = EXAMPLE_POD_TEMPLATE_FUNCTIONAL
