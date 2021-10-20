# -*- coding: utf-8 -*-
"""Base module for unittesting."""

from collective.documentgenerator.config import HAS_PLONE_5
from collective.documentgenerator.config import HAS_PLONE_5_2
from imio.pyutils.system import runCommand
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
from plone.protect.authenticator import createToken
from plone.testing import z2
from zope.globalrequest import setLocal

import collective.documentgenerator
import os
import tempfile
import transaction
import unittest
import zipfile


if HAS_PLONE_5_2:
    import sys
    from zope.deprecation import deprecation
    sys.modules['collective.documentgenerator.tests.ArchetypesIntegrationTests'] = \
        deprecation.deprecated(deprecation, 'Archetypes was removed from Plone 5.2.')
    sys.modules['collective.documentgenerator.tests.ArchetypesFunctionnalTests'] = \
        deprecation.deprecated(deprecation, 'Archetypes was removed from Plone 5.2.')


class NakedPloneLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        """Set up Zope."""
        # Load ZCML
        self.loadZCML(package=collective.documentgenerator,
                      name='testing.zcml')
        (stdout, stderr, st) = runCommand('%s/bin/soffice.sh restart' % os.getenv('PWD'))

    def setUpPloneSite(self, portal):
        """ Setup Plone
        """

        # Default workflow
        wftool = portal['portal_workflow']
        wftool.setDefaultChain('simple_publication_workflow')

        # Add default Plone content
        try:
            applyProfile(portal, 'plone.app.contenttypes:plone-content')
            # portal.portal_workflow.setDefaultChain(
            #     'simple_publication_workflow')
        except KeyError:
            # BBB Plone 4
            # Products.ATContentTypes is installed by default in Plone4's tests
            pass

    def tearDownZope(self, app):
        """Tear down Zope."""
        if HAS_PLONE_5_2:
            from plone.testing import zope
            zope.uninstallProduct(app, 'collective.documentgenerator')
        else:
            z2.uninstallProduct(app, 'collective.documentgenerator')
        (stdout, stderr, st) = runCommand('%s/bin/soffice.sh stop' % os.getenv('PWD'))


NAKED_PLONE_FIXTURE = NakedPloneLayer(
    name='NAKED_PLONE_FIXTURE'
)

NAKED_PLONE_INTEGRATION = IntegrationTesting(
    bases=(NAKED_PLONE_FIXTURE,),
    name='NAKED_PLONE_INTEGRATION'
)


class DocumentgeneratorLayer(NakedPloneLayer):

    def setUpPloneSite(self, portal):
        """Set up Plone."""
        super(DocumentgeneratorLayer, self).setUpPloneSite(portal)

        # Set tests in 'fr'
        if HAS_PLONE_5:
            api.portal.set_registry_record('plone.available_languages', ['en', 'fr'])
            api.portal.set_registry_record('plone.default_language', 'fr')

        # Install into Plone site using portal_setup
        applyProfile(portal, 'collective.documentgenerator:testing')

        # Install plone-content for Plone 4 so front-page is available
        if not HAS_PLONE_5:
            applyProfile(portal, 'Products.CMFPlone:plone-content')

        # Login and create some test content
        setRoles(portal, TEST_USER_ID, ['Manager'])
        login(portal, TEST_USER_NAME)

        # Commit so that the test browser sees these objects
        transaction.commit()


TEST_INSTALL_FIXTURE = DocumentgeneratorLayer(
    name='TEST_INSTALL_FIXTURE'
)

TEST_INSTALL_INTEGRATION = IntegrationTesting(
    bases=(TEST_INSTALL_FIXTURE,),
    name='TEST_INSTALL_INTEGRATION'
)


TEST_INSTALL_FUNCTIONAL = FunctionalTesting(
    bases=(TEST_INSTALL_FIXTURE,),
    name='TEST_INSTALL_FUNCTIONAL'
)


class ExamplePODTemplateLayer(DocumentgeneratorLayer):

    def setUpPloneSite(self, portal):
        super(ExamplePODTemplateLayer, self).setUpPloneSite(portal)

        applyProfile(portal, 'collective.documentgenerator:demo')
        applyProfile(portal, 'collective.documentgenerator:testing')

        # Commit so that the test browser sees these objects
        transaction.commit()


POD_TEMPLATE_FIXTURE = ExamplePODTemplateLayer(
    name='POD_TEMPLATE_FIXTURE'
)

POD_TEMPLATE_INTEGRATION = IntegrationTesting(
    bases=(POD_TEMPLATE_FIXTURE,),
    name='POD_TEMPLATE_INTEGRATION'
)

POD_TEMPLATE_FUNCTIONAL = FunctionalTesting(
    bases=(POD_TEMPLATE_FIXTURE,),
    name='POD_TEMPLATE_FUNCTIONAL'
)


ACCEPTANCE = FunctionalTesting(
    bases=(
        POD_TEMPLATE_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        z2.ZSERVER_FIXTURE
    ),
    name='ACCEPTANCE'
)


class BaseTest(unittest.TestCase):
    """
    Helper class for tests.
    """

    def setUp(self):
        self.portal = self.layer['portal']
        if not HAS_PLONE_5:
            ltool = self.portal.portal_languages
            defaultLanguage = 'fr'
            supportedLanguages = ['en', 'fr']
            ltool.manage_setLanguageSettings(defaultLanguage, supportedLanguages,
                                             setUseCombinedLanguageCodes=False)
            self.portal.portal_languages.setLanguageBindings()

    def get_odt_content_xml(self, generated_doc):
        """Return content.xml from a generated doc binary."""
        tmp_dir = tempfile.gettempdir()
        tmp_file = open(os.path.join(tmp_dir, 'tmp_file.zip'), 'w')
        tmp_file.write(generated_doc)
        tmp_file.close()
        zfile = zipfile.ZipFile(tmp_file.name, 'r')
        content_xml = zfile.read('content.xml')
        zfile.close()
        os.remove(tmp_file.name)
        return content_xml


class BrowserTest(BaseTest):
    """
    Helper class for Browser tests.
    """

    def setUp(self):
        super(BrowserTest, self).setUp()
        if HAS_PLONE_5_2:
            from plone.testing import zope
            self.browser = zope.Browser(self.portal)
        else:
            self.browser = z2.Browser(self.portal)
        self.browser.handleErrors = False

    def browser_login(self, user, password):
        login(self.portal, user)
        self.browser.open(self.portal.absolute_url() + '/logout')
        self.browser.open(self.portal.absolute_url() + '/login_form')
        self.browser.getControl(name='__ac_name').value = user
        self.browser.getControl(name='__ac_password').value = password
        if HAS_PLONE_5_2:
            self.browser.getControl(name='buttons.login').click()
        else:
            self.browser.getControl(name='submit').click()

    def _edit_object(self, obj):
        token = createToken()
        self.browser.open('{}/?_authenticator={}'.format(obj.absolute_url(), token))
        contents = self.browser.contents
        return contents


class PODTemplateIntegrationTest(BrowserTest):
    """Base class for integration browser tests."""

    layer = POD_TEMPLATE_INTEGRATION

    def setUp(self):
        super(PODTemplateIntegrationTest, self).setUp()
        self.test_podtemplate = self.portal.podtemplates.get('test_template')
        self.browser_login(TEST_USER_NAME, TEST_USER_PASSWORD)
        setLocal('request', self.portal.REQUEST)


class PODTemplateFunctionalTest(BrowserTest):
    """Base class for functional browser tests."""

    layer = POD_TEMPLATE_FUNCTIONAL

    def setUp(self):
        super(PODTemplateFunctionalTest, self).setUp()
        self.test_podtemplate = self.portal.podtemplates.get('test_template_bis')
        self.browser_login(TEST_USER_NAME, TEST_USER_PASSWORD)
        setLocal('request', self.portal.REQUEST)


class ConfigurablePODTemplateIntegrationTest(BrowserTest):
    """Base class for integration tests."""

    layer = POD_TEMPLATE_INTEGRATION

    def setUp(self):
        super(ConfigurablePODTemplateIntegrationTest, self).setUp()
        self.test_podtemplate = self.portal.podtemplates.get('test_template_bis')
        self.browser_login(TEST_USER_NAME, TEST_USER_PASSWORD)
        setLocal('request', self.portal.REQUEST)


class ArchetypesIntegrationTests(BaseTest):
    """Base class for Archetypes implementation tests."""

    layer = POD_TEMPLATE_INTEGRATION

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

        AT_doc = api.content.create(
            type='Document',
            id='AT_doc',
            container=self.portal
        )
        self.AT_doc = AT_doc
        setLocal('request', self.portal.REQUEST)


class ArchetypesFunctionnalTests(ArchetypesIntegrationTests):
    """Base class for Archetypes functional tests."""

    layer = POD_TEMPLATE_FUNCTIONAL


class DexterityIntegrationTests(BaseTest):

    """Base class for Dexterity implementation tests."""

    layer = POD_TEMPLATE_INTEGRATION

    def setUp(self):
        super(DexterityIntegrationTests, self).setUp()

        # create a test content type
        self.content = api.content.create(
            container=self.portal, id='johndoe', type='member')

        doc = api.content.create(
            type='Document',
            id='doc',
            container=self.portal
        )
        self.doc = doc


class DexterityFunctionnalTests(DexterityIntegrationTests):
    """Base class for Dexterity functional tests."""

    layer = POD_TEMPLATE_FUNCTIONAL
