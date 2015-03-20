# -*- coding: utf-8 -*-

from collective.documentgenerator.config import POD_TEMPLATE_TYPES
from collective.documentgenerator.utils import translate as _

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
            title=_(u'POD Templates'),
            id='podtemplates',
            container=portal,
            excludeFromNav=True
        )
        templates_folder.setTitle('POD Templates')
        templates_folder.reindexObject()

    pod_folder = getattr(portal, 'podtemplates')
    pod_folder.setConstrainTypesMode(1)
    pod_folder.setLocallyAllowedTypes(POD_TEMPLATE_TYPES.keys())
    pod_folder.setImmediatelyAddableTypes(POD_TEMPLATE_TYPES.keys())

    setup_tool = api.portal.get_tool('portal_setup')
    demo_profile = setup_tool.getProfileInfo('collective.documentgenerator:demo')

    # Create some test content
    template_path = '{}/templates/styles.odt'.format(demo_profile.get('path'))
    template_file = file(template_path, 'rb').read()
    blob_file = NamedBlobFile(data=template_file, contentType='applications/odt')
    style_template_id = 'test_style_template'

    if not hasattr(pod_folder, style_template_id):
        api.content.create(
            type='StyleTemplate',
            id=style_template_id,
            title='Styles',
            odt_file=blob_file,
            container=pod_folder,
            excludeFromNav=True
        )
    style_template = getattr(pod_folder, style_template_id)

    template_path = '{}/templates/styles_2.odt'.format(demo_profile.get('path'))
    template_file = file(template_path, 'rb').read()
    blob_file = NamedBlobFile(data=template_file, contentType='applications/odt')
    style_template_id = 'test_style_template_2'

    if not hasattr(pod_folder, style_template_id):
        api.content.create(
            type='StyleTemplate',
            id=style_template_id,
            title=_(u'Styles n°2'),
            odt_file=blob_file,
            container=pod_folder,
            excludeFromNav=True
        )

    sub_template_id = 'sub_template'
    template_path = '{}/templates/sub_template.odt'.format(demo_profile.get('path'))
    template_file = file(template_path, 'rb').read()
    blob_file = NamedBlobFile(data=template_file, contentType='applications/odt')

    if not hasattr(pod_folder, sub_template_id):
        api.content.create(
            type='SubTemplate',
            id=sub_template_id,
            title=_(u'Header'),
            odt_file=blob_file,
            container=pod_folder,
            excludeFromNav=True
        )
    sub_template = getattr(pod_folder, sub_template_id)

    template_path = '{}/templates/modele_general.odt'.format(demo_profile.get('path'))
    template_file = file(template_path, 'rb').read()
    blob_file = NamedBlobFile(data=template_file, contentType='applications/odt')

    if not hasattr(pod_folder, 'test_template'):
        api.content.create(
            type='PODTemplate',
            id='test_template',
            title=_(u"General template"),
            odt_file=blob_file,
            container=pod_folder,
            excludeFromNav=True
        )

    template_path = '{}/templates/modele_collection.odt'.format(demo_profile.get('path'))
    template_file = file(template_path, 'rb').read()
    blob_file = NamedBlobFile(data=template_file, contentType='applications/odt')

    if not hasattr(pod_folder, 'test_template_bis'):
        api.content.create(
            type='ConfigurablePODTemplate',
            id='test_template_bis',
            title=_(u"Collection template"),
            odt_file=blob_file,
            container=pod_folder,
            excludeFromNav=True,
            pod_portal_type=['Collection'],
            style_template=[style_template.UID()],
            merge_templates=[
                {
                    'template': sub_template.UID(),
                    'pod_context_name': 'header',
                }
            ],
        )
