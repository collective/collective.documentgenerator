# -*- coding: utf-8 -*-

from plone import api
from plone.namedfile.file import NamedBlobFile

def isNotCurrentProfile(context):
    return context.readDataFile("collectivedocumentgenerator_marker.txt") is None


def post_install(context):
    """Post install script"""
    if isNotCurrentProfile(context): return
    portal = context.getSite()


def install_demo(context):
    """ """
    portal = api.portal.get()

    if not hasattr(portal, 'podtemplates'):
        templates_folder = api.content.create(
            type='Folder',
            title='podtemplates',
            container=portal,
            excludeFromNav=True
        )

    setup_tool = api.portal.get_tool('portal_setup')
    demo_profile = setup_tool.getProfileInfo('collective.documentgenerator:demo')
    template_path = '{}/templates/document.odt'.format(demo_profile.get('path'))
    # Create some test content
    template_file = file(template_path, 'rb').read()
    blob_file = NamedBlobFile(data=template_file, contentType='applications/odt')

    if not hasattr(portal.podtemplates, 'test_template'):
        demo_template = api.content.create(
            type='PODTemplate',
            title='test_template',
            odt_file=blob_file,
            container=portal.podtemplates,
            excludeFromNav=True
        )
