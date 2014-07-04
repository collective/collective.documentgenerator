# -*- coding: utf-8 -*-
"""Base module for unittesting."""

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


class TestInstallDocumentgeneratorLayer(NakedPloneLayer):

    def setUpPloneSite(self, portal):
        """Set up Plone."""
        # Install into Plone site using portal_setup
        applyProfile(portal, 'collective.documentgenerator:testing')

        # Login and create some test content
        setRoles(portal, TEST_USER_ID, ['Manager'])
        login(portal, TEST_USER_NAME)

        # Commit so that the test browser sees these objects
        import transaction
        transaction.commit()


TEST_INSTALL_FIXTURE = TestInstallDocumentgeneratorLayer(
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


class ExamplePODTemplateLayer(TestInstallDocumentgeneratorLayer):

    def setUpPloneSite(self, portal):
        super(ExamplePODTemplateLayer, self).setUpPloneSite(portal)

        # Create some test content
        api.content.create(
            type='PODTemplate',
            id='test_podtemplate',
            container=portal,
        )

        # Commit so that the test browser sees these objects
        import transaction
        transaction.commit()


EXAMPLE_POD_TEMPLATE_FIXTURE = ExamplePODTemplateLayer(
    name="EXAMPLE_POD_TEMPLATE_FIXTURE"
)

EXAMPLE_POD_TEMPLATE_INTEGRATION = IntegrationTesting(
    bases=(EXAMPLE_POD_TEMPLATE_FIXTURE,),
    name="EXAMPLE_POD_TEMPLATE_INTEGRATION"
)


class PODTemplateIntegrationBrowserTest(BrowserTest):
    """Base class for integration tests."""

    layer = EXAMPLE_POD_TEMPLATE_INTEGRATION

    def setUp(self):
        super(PODTemplateIntegrationBrowserTest, self).setUp()
        self.test_podtemplate = self.portal.get('test_podtemplate')
        self.browser_login(TEST_USER_NAME, TEST_USER_PASSWORD)


class ExampleConfigurablePODTemplateLayer(TestInstallDocumentgeneratorLayer):

    def setUpPloneSite(self, portal):
        super(ExampleConfigurablePODTemplateLayer, self).setUpPloneSite(portal)

        # Create some test content
        api.content.create(
            type='ConfigurablePODTemplate',
            id='test_podtemplate',
            container=portal,
        )

        # Commit so that the test browser sees these objects
        import transaction
        transaction.commit()


EXAMPLE_CONFIGURABLE_POD_TEMPLATE_FIXTURE = ExampleConfigurablePODTemplateLayer(
    name="EXAMPLE_CONFIGURABLE_POD_TEMPLATE_FIXTURE"
)

EXAMPLE_CONFIGURABLE_POD_TEMPLATE_INTEGRATION = IntegrationTesting(
    bases=(EXAMPLE_CONFIGURABLE_POD_TEMPLATE_FIXTURE,),
    name="EXAMPLE_CONFIGURABLE_POD_TEMPLATE_INTEGRATION"
)


class ConfigurablePODTemplateIntegrationBrowserTest(BrowserTest):
    """Base class for integration tests."""

    layer = EXAMPLE_CONFIGURABLE_POD_TEMPLATE_INTEGRATION

    def setUp(self):
        super(ConfigurablePODTemplateIntegrationBrowserTest, self).setUp()
        self.test_podtemplate = self.portal.get('test_podtemplate')
        self.browser_login(TEST_USER_NAME, TEST_USER_PASSWORD)
