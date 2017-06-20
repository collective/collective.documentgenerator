# -*- coding: utf-8 -*-

import os
from Products.CMFPlone.utils import safe_unicode
from plone import api

ODS_FORMATS = (('ods', 'LibreOffice Calc (.ods)'),
               ('xls', 'Microsoft Excel (.xls)'),)

ODT_FORMATS = (('odt', 'LibreOffice Writer (.odt)'),
               ('doc', 'Microsoft Word (.doc)'),
               ('docx', 'Microsoft Word XML (.docx)'),
               ('rtf', 'Rich Text Format (.RTF)'),)

NEUTRAL_FORMATS = (('pdf', 'Adobe PDF (.pdf)'),)

POD_FORMATS = ODS_FORMATS + ODT_FORMATS + NEUTRAL_FORMATS

DEFAULT_PYTHON_UNO_PATH = u'/usr/bin/python'

VIEWLET_TYPES = ['PODTemplate', 'ConfigurablePODTemplate']

HAS_PLONE_5 = api.env.plone_version().startswith('5')


def get_uno_path():
    return api.portal.get_registry_record(
        'collective.documentgenerator.browser.controlpanel.IDocumentGeneratorControlPanelSchema.uno_path'
    )


def get_oo_port():
    return api.portal.get_registry_record(
        'collective.documentgenerator.browser.controlpanel.IDocumentGeneratorControlPanelSchema.oo_port'
    )


def get_optimize_tables():
    return api.portal.get_registry_record(
        'collective.documentgenerator.browser.controlpanel.IDocumentGeneratorControlPanelSchema.optimize_tables'
    )


def get_raiseOnError_for_non_managers():
    return api.portal.get_registry_record(
        'collective.documentgenerator.browser.controlpanel.'
        'IDocumentGeneratorControlPanelSchema.raiseOnError_for_non_managers'
    )


def set_oo_port():
    """ Get environment value in buildout to define port """
    oo_port = os.getenv('OO_PORT', None)
    if oo_port:
        api.portal.set_registry_record('collective.documentgenerator.browser.controlpanel.'
                                       'IDocumentGeneratorControlPanelSchema.oo_port', int(oo_port))


def set_uno_path():
    """ Get environment value in buildout to define path """
    python_uno = os.getenv('PYTHON_UNO', None)
    if python_uno:
        api.portal.set_registry_record('collective.documentgenerator.browser.controlpanel.'
                                       'IDocumentGeneratorControlPanelSchema.uno_path', safe_unicode(python_uno))
