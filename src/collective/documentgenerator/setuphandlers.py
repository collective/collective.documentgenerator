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
    portal = context.getSite()


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

    if not hasattr(portal.podtemplates, 'modele_general'):
        api.content.create(
            type='PODTemplate',
            id='modele_general',
            title='Modèle général',
            odt_file=blob_file,
            container=portal.podtemplates,
            excludeFromNav=True
        )

    template_path = '{}/templates/modele_collection.odt'.format(demo_profile.get('path'))
    template_file = file(template_path, 'rb').read()
    blob_file = NamedBlobFile(data=template_file, contentType='applications/odt')

    if not hasattr(portal.podtemplates, 'modele_collection'):
        api.content.create(
            type='ConfigurablePODTemplate',
            id='modele_collection',
            title='Modèle collection',
            odt_file=blob_file,
            container=portal.podtemplates,
            excludeFromNav=True,
            pod_portal_type=['Collection'],
        )
