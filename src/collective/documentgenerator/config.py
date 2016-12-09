# -*- coding: utf-8 -*-

import os
from plone import api

ODS_FORMATS = (('ods', 'LibreOffice Calc (.ods)'),
               ('xls', 'Microsoft Excel (.xls)'),)

ODT_FORMATS = (('odt', 'LibreOffice Writer (.odt)'),
               ('doc', 'Microsoft Word (.doc)'),
               ('docx', 'Microsoft Word XML (.docx)'),
               ('rtf', 'Rich Text Format (.RTF)'),)

NEUTRAL_FORMATS = (('pdf', 'Adobe PDF (.pdf)'),)

POD_FORMATS = ODS_FORMATS + ODT_FORMATS + NEUTRAL_FORMATS

DEFAULT_PYTHON_UNO_PATH = '/usr/bin/python'

VIEWLET_TYPES = ['PODTemplate', 'ConfigurablePODTemplate']


def get_uno_path():
    return api.portal.get_registry_record(
        'collective.documentgenerator.browser.controlpanel.IDocumentGeneratorControlPanelSchema.uno_path'
    )


def get_oo_port():
    return api.portal.get_registry_record(
        'collective.documentgenerator.browser.controlpanel.IDocumentGeneratorControlPanelSchema.oo_port'
    )


def set_oo_port():
    """ Get environment value ste in buildout to define port """
    oo_port = os.getenv('OO_PORT', None)
    if oo_port:
        api.portal.set_registry_record('collective.documentgenerator.browser.controlpanel.'
                                       'IDocumentGeneratorControlPanelSchema.oo_port', int(oo_port))
