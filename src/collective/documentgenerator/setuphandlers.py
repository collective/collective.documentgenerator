# -*- coding: utf-8 -*-
from collective.documentgenerator.config import set_use_stream
from collective.documentgenerator.content.pod_template import POD_TEMPLATE_TYPES
from collective.documentgenerator.utils import translate as _
from plone import api
from plone.namedfile.file import NamedBlobFile
from Products.CMFPlone import interfaces as Plone
from Products.CMFPlone.utils import safe_unicode
from Products.CMFQuickInstallerTool import interfaces as QuickInstaller
from zope.interface import implementer

import logging
import os


try:
    from Products.CMFPlone.interfaces.constrains import IConstrainTypes
except ImportError:
    # BBB Plone 4
    from Products.CMFPlone.interfaces import IConstrainTypes

logger = logging.getLogger('collective.documentgenerator')


def isNotCurrentProfile(context):
    return context.readDataFile('collectivedocumentgenerator_marker.txt') is None


def post_install(context):
    """Post install script"""
    if isNotCurrentProfile(context):
        return


def install_demo(context):
    """ """
    if context.readDataFile('collectivedocumentgenerator_demo_marker.txt') is None:
        return

    portal = api.portal.get()
    use_stream = os.getenv('USE_STREAM', False) == 'True'
    set_use_stream(use_stream)
    if not hasattr(portal, 'podtemplates'):
        templates_folder = api.content.create(
            type='Folder',
            title=_(u'POD Templates'),
            id='podtemplates',
            container=portal,
            exclude_from_nav=True
        )
        templates_folder.setTitle('POD Templates')
        templates_folder.reindexObject()

    pod_folder = getattr(portal, 'podtemplates')
    constrain_types = IConstrainTypes(pod_folder)
    constrain_types.setConstrainTypesMode(1)
    constrain_types.setLocallyAllowedTypes(POD_TEMPLATE_TYPES.keys())
    constrain_types.setImmediatelyAddableTypes(POD_TEMPLATE_TYPES.keys())

    # Create some test content
    style_template_id = 'test_style_template'
    if not hasattr(pod_folder, style_template_id):
        api.content.create(
            type='StyleTemplate',
            id=style_template_id,
            title='Styles',
            odt_file=NamedBlobFile(
                data=context.readDataFile('templates/styles.odt'),
                contentType='application/vnd.oasis.opendocument.text',
                filename=u'styles.odt',
            ),
            container=pod_folder,
            exclude_from_nav=True
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
                contentType='application/vnd.oasis.opendocument.text',
                filename=u'styles_2.odt',
            ),
            container=pod_folder,
            exclude_from_nav=True
        )

    sub_template_id = 'sub_template'
    if not hasattr(pod_folder, sub_template_id):
        api.content.create(
            type='SubTemplate',
            id=sub_template_id,
            title=_(u'Header'),
            odt_file=NamedBlobFile(
                data=context.readDataFile('templates/sub_template.odt'),
                contentType='application/vnd.oasis.opendocument.text',
                filename=u'sub_template.odt',
            ),
            container=pod_folder,
            exclude_from_nav=True,
            style_template=[style_template.UID()],
        )
    sub_template = getattr(pod_folder, sub_template_id)

    if not hasattr(pod_folder, 'loop_template'):
        api.content.create(
            type='MailingLoopTemplate',
            id='loop_template',
            title=_(u'Mailing loop template'),
            odt_file=NamedBlobFile(
                data=context.readDataFile('templates/mailing.odt'),
                contentType='application/vnd.oasis.opendocument.text',
                filename=u'mailing.odt',
            ),
            container=pod_folder,
            exclude_from_nav=True,
            style_template=[style_template.UID()],
        )
    loop_template = getattr(pod_folder, 'loop_template')

    if not hasattr(pod_folder, 'test_template'):
        api.content.create(
            type='PODTemplate',
            id='test_template',
            title=_(u'General template'),
            odt_file=NamedBlobFile(
                data=context.readDataFile('templates/modele_general.odt'),
                contentType='application/vnd.oasis.opendocument.text',
                filename=u'modele_general.odt',
            ),
            container=pod_folder,
            exclude_from_nav=True,
        )

    if not hasattr(pod_folder, 'test_template_multiple'):
        api.content.create(
            type='ConfigurablePODTemplate',
            id='test_template_multiple',
            title=_(u'Multiple format template'),
            odt_file=NamedBlobFile(
                data=context.readDataFile('templates/modele_general.odt'),
                contentType='application/vnd.oasis.opendocument.text',
                filename=u'modele_general.odt',
            ),
            container=pod_folder,
            exclude_from_nav=True,
            pod_formats=['odt', 'pdf', 'doc', 'docx'],
            pod_portal_types=['Document'],
            style_template=[style_template.UID()],
            merge_templates=[
                {
                    'template': sub_template.UID(),
                    'pod_context_name': 'header',
                    'do_rendering': True,
                }
            ],
        )

    if not hasattr(pod_folder, 'test_template_bis'):
        api.content.create(
            type='ConfigurablePODTemplate',
            id='test_template_bis',
            title=_(u'Collection template'),
            odt_file=NamedBlobFile(
                data=context.readDataFile(safe_unicode('templates/modèle_collection.odt')),
                contentType='application/vnd.oasis.opendocument.text',
                filename=u'modèle_collection.odt',
            ),
            container=pod_folder,
            exclude_from_nav=True,
            pod_formats=['odt', 'pdf', ],
            pod_portal_types=['Collection', 'Folder'],
            style_template=[style_template.UID()],
            merge_templates=[
                {
                    'template': sub_template.UID(),
                    'pod_context_name': 'header',
                    'do_rendering': False,
                }
            ],
            context_variables=[
                {
                    'name': 'details',
                    'value': '1',
                }
            ],
        )

    if not hasattr(pod_folder, 'test_ods_template'):
        api.content.create(
            type='ConfigurablePODTemplate',
            id='test_ods_template',
            title=_(u'Spreadsheet template'),
            odt_file=NamedBlobFile(
                data=context.readDataFile('templates/modele_general.ods'),
                contentType='application/vnd.oasis.opendocument.spreadsheet',
                filename=u'modele_general.ods',
            ),
            container=pod_folder,
            exclude_from_nav=True,
            pod_formats=['ods', 'xls', ],
            pod_portal_types=['Collection', 'Folder'],
            style_template=[style_template.UID()],
        )

    if not hasattr(pod_folder, 'test_template_possibly_mailed'):
        api.content.create(
            type='ConfigurablePODTemplate',
            id='test_template_possibly_mailed',
            title=_(u'Possibly mailed template'),
            odt_file=NamedBlobFile(
                data=context.readDataFile('templates/possibly_mailed_model.odt'),
                contentType='application/vnd.oasis.opendocument.text',
                filename=u'possibly_mailed_model.odt',
            ),
            container=pod_folder,
            exclude_from_nav=True,
            pod_formats=['odt'],
            pod_portal_types=['Folder'],
            mailing_loop_template=loop_template.UID(),
            context_variables=[
                {
                    'name': 'details',
                    'value': '1',
                }
            ],
        )

    if not hasattr(pod_folder, 'test_template_reusable'):
        api.content.create(
            type='ConfigurablePODTemplate',
            id='test_template_reusable',
            title=_(u'Reusable template'),
            odt_file=NamedBlobFile(
                data=context.readDataFile('templates/modele_general.odt'),
                contentType='application/vnd.oasis.opendocument.text',
                filename=u'modele_general.odt',
            ),
            is_reusable=True,
            container=pod_folder,
            pod_formats=['odt'],
            pod_portal_types=['Folder'],
            exclude_from_nav=True
        )

    reusable_template = getattr(pod_folder, 'test_template_reusable')

    if not hasattr(pod_folder, 'test_template_reuse'):
        api.content.create(
            type='ConfigurablePODTemplate',
            id='test_template_reuse',
            title=_(u'Reuse Test Template'),
            container=pod_folder,
            exclude_from_nav=True,
            pod_formats=['odt', 'pdf', 'doc', 'docx'],
            pod_portal_types=['Document'],
            pod_template_to_use=reusable_template.UID()
        )


@implementer(Plone.INonInstallable)
class HiddenProfiles(object):
    def getNonInstallableProfiles(self):
        """Do not show on Plone's list of installable profiles."""
        return [
            u'collective.documentgenerator:install-base',
        ]


@implementer(QuickInstaller.INonInstallable)
class HiddenProducts(object):
    def getNonInstallableProducts(self):
        """Do not show on QuickInstaller's list of installable products."""
        return [
            u'collective.documentgenerator:install-base',
        ]
