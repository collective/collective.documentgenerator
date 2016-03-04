# -*- coding: utf-8 -*-

from collective.documentgenerator.content.pod_template import ConfigurablePODTemplate
from collective.documentgenerator.content.pod_template import PODTemplate
from collective.documentgenerator.content.pod_template import SubTemplate
from collective.documentgenerator.content.style_template import StyleTemplate

from plone import api

ODS_FORMATS = (('ods', 'LibreOffice Calc (.ods)'),
               ('xls', 'Microsoft Excel (.xls)'),)

ODT_FORMATS = (('odt', 'LibreOffice Doc (.odt)'),
               ('doc', 'Microsoft Word (.doc)'),
               ('rtf', 'Rich Text Format (.RTF)'),)

NEUTRAL_FORMATS = (('pdf', 'Adobe PDF (.pdf)'),)

POD_FORMATS = ODS_FORMATS + ODT_FORMATS + NEUTRAL_FORMATS

POD_TEMPLATE_TYPES = {
    PODTemplate.__name__: PODTemplate,
    ConfigurablePODTemplate.__name__: ConfigurablePODTemplate,
    SubTemplate.__name__: SubTemplate,
    StyleTemplate.__name__: StyleTemplate,
}

DEFAULT_PYTHON_UNO_PATH = '/usr/bin/python'


def get_uno_path():
    return api.portal.get_registry_record(
        'collective.documentgenerator.browser.controlpanel.IDocumentGeneratorControlPanelSchema.uno_path'
    )


def get_oo_port():
    return api.portal.get_registry_record(
        'collective.documentgenerator.browser.controlpanel.IDocumentGeneratorControlPanelSchema.oo_port'
    )
