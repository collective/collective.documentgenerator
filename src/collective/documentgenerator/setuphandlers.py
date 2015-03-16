# -*- coding: utf-8 -*-

from plone import api
from plone.namedfile.file import NamedBlobFile

import logging

logger = logging.getLogger('collective.documentgenerator')


def isNotCurrentProfile(context):
    return context.readDataFile("collectivedocumentgenerator_marker.txt") is None


def post_install(context):
    """Post install script"""
    if isNotCurrentProfile(context):
        return


def install_demo(context):
    """ """
    portal = api.portal.get()

    if not hasattr(portal, 'podtemplates'):
        templates_folder = api.content.create(
            type='Folder',
            title='POD Templates',
            id='podtemplates',
            container=portal,
            excludeFromNav=True
        )
        templates_folder.setTitle('POD Templates')
        templates_folder.reindexObject()

    setup_tool = api.portal.get_tool('portal_setup')
    demo_profile = setup_tool.getProfileInfo('collective.documentgenerator:demo')
    template_path = '{}/templates/modele_general.odt'.format(demo_profile.get('path'))
    # Create some test content
    template_file = file(template_path, 'rb').read()
    blob_file = NamedBlobFile(data=template_file, contentType='applications/odt')

    if not hasattr(portal.podtemplates, 'test_template'):
        api.content.create(
            type='PODTemplate',
            id='test_template',
            title='Modele general',
            odt_file=blob_file,
            container=portal.podtemplates,
            excludeFromNav=True
        )

    template_path = '{}/templates/modele_collection.odt'.format(demo_profile.get('path'))
    template_file = file(template_path, 'rb').read()
    blob_file = NamedBlobFile(data=template_file, contentType='applications/odt')

    if not hasattr(portal.podtemplates, 'test_template_bis'):
        api.content.create(
            type='ConfigurablePODTemplate',
            id='test_template_bis',
            title='Modele collection',
            odt_file=blob_file,
            container=portal.podtemplates,
            excludeFromNav=True,
            pod_portal_type=['Collection'],
        )

    template_path = '{}/templates/styles.odt'.format(demo_profile.get('path'))
    # Create some test content
    template_file = file(template_path, 'rb').read()
    blob_file = NamedBlobFile(data=template_file, contentType='applications/odt')

    if not hasattr(portal.podtemplates, 'test_style_template'):
        api.content.create(
            type='StyleTemplate',
            id='test_style_template',
            title='Styles',
            odt_file=blob_file,
            container=portal.podtemplates,
            excludeFromNav=True
        )
