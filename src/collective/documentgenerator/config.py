# -*- coding: utf-8 -*-

from plone import api

ODS_FORMATS = (('ods', 'LibreOffice Calc (.ods)'),
               ('xls', 'Microsoft Excel (.xls)'),)

ODT_FORMATS = (('odt', 'LibreOffice Writer (.odt)'),
               ('doc', 'Microsoft Word (.doc)'),
               ('rtf', 'Rich Text Format (.RTF)'),)

NEUTRAL_FORMATS = (('pdf', 'Adobe PDF (.pdf)'),)

POD_FORMATS = ODS_FORMATS + ODT_FORMATS + NEUTRAL_FORMATS

DEFAULT_PYTHON_UNO_PATH = '/usr/bin/python'


def get_uno_path():
    return api.portal.get_registry_record(
        'collective.documentgenerator.browser.controlpanel.IDocumentGeneratorControlPanelSchema.uno_path'
    )


def get_oo_port():
    return api.portal.get_registry_record(
        'collective.documentgenerator.browser.controlpanel.IDocumentGeneratorControlPanelSchema.oo_port'
    )
