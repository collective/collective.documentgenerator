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

    # Create some test content
    template_path = '{}/templates/styles.odt'.format(demo_profile.get('path'))
    template_file = file(template_path, 'rb').read()
    blob_file = NamedBlobFile(data=template_file, contentType='applications/odt')
    style_template_id = 'test_style_template'

    if not hasattr(portal.podtemplates, style_template_id):
        api.content.create(
            type='StyleTemplate',
            id=style_template_id,
            title='Styles',
            odt_file=blob_file,
            container=portal.podtemplates,
            excludeFromNav=True
        )
    style_template = getattr(portal.podtemplates, style_template_id)

    template_path = '{}/templates/modele_general.odt'.format(demo_profile.get('path'))
    template_file = file(template_path, 'rb').read()
    blob_file = NamedBlobFile(data=template_file, contentType='applications/odt')

    if not hasattr(portal.podtemplates, 'test_template'):
        api.content.create(
            type='PODTemplate',
            id='test_template',
            title='Modèle general',
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
            title='Modèle collection',
            odt_file=blob_file,
            container=portal.podtemplates,
            excludeFromNav=True,
            pod_portal_type=['Collection'],
            style_template=[style_template.UID()],
        )
