# -*- coding: utf-8 -*-

from Products.CMFPlone.utils import safe_unicode
from plone import api

import os

ODS_FORMATS = (('ods', 'LibreOffice Calc (.ods)'),
               ('xls', 'Microsoft Excel (.xls)'),
               ('xlsx', 'Microsoft Excel (.xlsx)'),)

ODT_FORMATS = (('odt', 'LibreOffice Writer (.odt)'),
               ('doc', 'Microsoft Word (.doc)'),
               ('docx', 'Microsoft Word XML (.docx)'),
               ('rtf', 'Rich Text Format (.RTF)'),)

NEUTRAL_FORMATS = (('pdf', 'Adobe PDF (.pdf)'),)

POD_FORMATS = ODS_FORMATS + ODT_FORMATS + NEUTRAL_FORMATS

DEFAULT_PYTHON_UNO_PATH = u'/usr/bin/python'

VIEWLET_TYPES = ['PODTemplate', 'ConfigurablePODTemplate']

HAS_PLONE_4 = api.env.plone_version().startswith('4')
HAS_PLONE_5 = api.env.plone_version().startswith('5')
HAS_PLONE_5_1 = api.env.plone_version() > '5.1'
HAS_PLONE_5_2 = api.env.plone_version() > '5.2'

DEFAULT_OO_SERVER = u'localhost'
DEFAULT_OO_PORT = 2002
DEFAULT_PYTHON_UNO = u'/usr/bin/python3'
DEFAULT_COLUMN_MODIFIER = u'nothing'


if HAS_PLONE_5_2:
    import sys
    from zope.deprecation import deprecation
    sys.modules['collective.documentgenerator.demo.helper.ATDemoHelperView'] = \
        deprecation.deprecated(deprecation, 'Archetypes was removed from Plone 5.2.')


def get_uno_path():
    return api.portal.get_registry_record(
        'collective.documentgenerator.browser.controlpanel.IDocumentGeneratorControlPanelSchema.uno_path'
    )


def get_oo_server():
    return api.portal.get_registry_record(
        'collective.documentgenerator.browser.controlpanel.IDocumentGeneratorControlPanelSchema.oo_server'
    )


def get_oo_port():
    return api.portal.get_registry_record(
        'collective.documentgenerator.browser.controlpanel.IDocumentGeneratorControlPanelSchema.oo_port'
    )


def get_column_modifier():
    return api.portal.get_registry_record(
        'collective.documentgenerator.browser.controlpanel.IDocumentGeneratorControlPanelSchema.column_modifier'
    )


def get_raiseOnError_for_non_managers():
    return api.portal.get_registry_record(
        'collective.documentgenerator.browser.controlpanel.'
        'IDocumentGeneratorControlPanelSchema.raiseOnError_for_non_managers'
    )


def get_use_stream():
    use_stream = api.portal.get_registry_record(
        'collective.documentgenerator.browser.controlpanel.IDocumentGeneratorControlPanelSchema.use_stream'
    )
    return use_stream


def set_oo_server():
    """ Get environment value in buildout to define port """
    oo_server = os.getenv('OO_SERVER', DEFAULT_OO_SERVER)
    if oo_server:
        api.portal.set_registry_record('collective.documentgenerator.browser.controlpanel.'
                                       'IDocumentGeneratorControlPanelSchema.oo_server', safe_unicode(oo_server))


def set_oo_port():
    """ Get environment value in buildout to define port """
    oo_port = os.getenv('OO_PORT', DEFAULT_OO_PORT)
    if oo_port:
        api.portal.set_registry_record('collective.documentgenerator.browser.controlpanel.'
                                       'IDocumentGeneratorControlPanelSchema.oo_port', int(oo_port))


def set_uno_path():
    """ Get environment value in buildout to define path """
    python_uno = os.getenv('PYTHON_UNO', DEFAULT_PYTHON_UNO)
    if python_uno:
        api.portal.set_registry_record('collective.documentgenerator.browser.controlpanel.'
                                       'IDocumentGeneratorControlPanelSchema.uno_path', safe_unicode(python_uno))


def set_column_modifier(value):
    api.portal.set_registry_record(
        'collective.documentgenerator.browser.controlpanel.IDocumentGeneratorControlPanelSchema.column_modifier',
        value
    )


def set_raiseOnError_for_non_managers(value):
    api.portal.set_registry_record(
        'collective.documentgenerator.browser.controlpanel.'
        'IDocumentGeneratorControlPanelSchema.raiseOnError_for_non_managers',
        value)


def set_use_stream(value):
    api.portal.set_registry_record(
        'collective.documentgenerator.browser.controlpanel.IDocumentGeneratorControlPanelSchema.use_stream',
        value
    )
