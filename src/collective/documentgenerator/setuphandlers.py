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

    # Create some test content
    style_template_id = 'test_style_template'
    if not hasattr(pod_folder, style_template_id):
        api.content.create(
            type='StyleTemplate',
            id=style_template_id,
            title='Styles',
            odt_file=NamedBlobFile(
                data=context.readDataFile('templates/styles.odt'),
                contentType='applications/odt',
                filename=u'styles.odt',
            ),
            container=pod_folder,
            excludeFromNav=True
        )
    style_template = getattr(pod_folder, style_template_id)

    style_template_id = 'test_style_template_2'
    if not hasattr(pod_folder, style_template_id):
        api.content.create(
            type='StyleTemplate',
            id=style_template_id,
            title=_(u'Styles n°2'),
            odt_file=NamedBlobFile(
                data=context.readDataFile('templates/styles_2.odt'),
                contentType='applications/odt',
                filename=u'styles_2.odt',
            ),
            container=pod_folder,
            excludeFromNav=True
        )

    sub_template_id = 'sub_template'
    if not hasattr(pod_folder, sub_template_id):
        api.content.create(
            type='SubTemplate',
            id=sub_template_id,
            title=_(u'Header'),
            odt_file=NamedBlobFile(
                data=context.readDataFile('templates/sub_template.odt'),
                contentType='applications/odt',
                filename=u'sub_template.odt',
            ),
            container=pod_folder,
            excludeFromNav=True
        )
    sub_template = getattr(pod_folder, sub_template_id)

    if not hasattr(pod_folder, 'test_template'):
        api.content.create(
            type='PODTemplate',
            id='test_template',
            title=_(u"General template"),
            odt_file=NamedBlobFile(
                data=context.readDataFile('templates/modele_general.odt'),
                contentType='applications/odt',
                filename=u'modele_general.odt',
            ),
            container=pod_folder,
            excludeFromNav=True
        )

    if not hasattr(pod_folder, 'test_template_multiple'):
        api.content.create(
            type='ConfigurablePODTemplate',
            id='test_template_multiple',
            title=_(u"Multiple format template"),
            odt_file=NamedBlobFile(
                data=context.readDataFile('templates/modele_general.odt'),
                contentType='applications/odt',
                filename=u'modele_general.odt',
            ),
            container=pod_folder,
            excludeFromNav=True,
            pod_formats=['odt', 'pdf', ],
            pod_portal_types=['Document'],
            style_template=[style_template.UID()],
            merge_templates=[
                {
                    'template': sub_template.UID(),
                    'pod_context_name': 'header',
                }
            ],
        )

    if not hasattr(pod_folder, 'test_template_bis'):
        api.content.create(
            type='ConfigurablePODTemplate',
            id='test_template_bis',
            title=_(u"Collection template"),
            odt_file=NamedBlobFile(
                data=context.readDataFile('templates/modele_collection.odt'),
                contentType='applications/odt',
                filename=u'modele_collection.odt',
            ),
            container=pod_folder,
            excludeFromNav=True,
            pod_formats=['odt', 'pdf', ],
            pod_portal_types=['Collection'],
            style_template=[style_template.UID()],
            merge_templates=[
                {
                    'template': sub_template.UID(),
                    'pod_context_name': 'header',
                }
            ],
        )
