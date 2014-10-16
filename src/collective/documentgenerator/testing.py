# -*- coding: utf-8 -*-
"""Base module for unittesting."""

from imio.helpers.test_helpers import BaseTest
from imio.helpers.test_helpers import BrowserTest

from plone import api

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

        # Commit so that the test browser sees these objects
        transaction.commit()


EXAMPLE_POD_TEMPLATE_FIXTURE = ExamplePODTemplateLayer(
    name="EXAMPLE_POD_TEMPLATE_FIXTURE"
)

EXAMPLE_POD_TEMPLATE_INTEGRATION = IntegrationTesting(
    bases=(EXAMPLE_POD_TEMPLATE_FIXTURE,),
    name="EXAMPLE_POD_TEMPLATE_INTEGRATION"
)

EXAMPLE_POD_TEMPLATE_FUNCTIONNAL = FunctionalTesting(
    bases=(EXAMPLE_POD_TEMPLATE_FIXTURE,),
    name="EXAMPLE_POD_TEMPLATE_INTEGRATION"
)


class PODTemplateIntegrationTest(BrowserTest):
    """Base class for integration tests."""

    layer = EXAMPLE_POD_TEMPLATE_INTEGRATION

    def setUp(self):
        super(PODTemplateIntegrationTest, self).setUp()
        self.test_podtemplate = self.portal.podtemplates.get('test_template')
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
    """Base class for Archetypes functionnal tests."""

    layer = EXAMPLE_POD_TEMPLATE_FUNCTIONNAL
