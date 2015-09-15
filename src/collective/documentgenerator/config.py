# -*- coding: utf-8 -*-

from collective.documentgenerator.content.pod_template import ConfigurablePODTemplate
from collective.documentgenerator.content.pod_template import PODTemplate
from collective.documentgenerator.content.pod_template import SubTemplate
from collective.documentgenerator.content.style_template import StyleTemplate

from plone import api

POD_FORMATS = (("doc", "Microsoft Word"),
               ("odt", "Open Document Format (text)"),
               ("rtf", "Rich Text Format (RTF)"),
               ("pdf", "Adobe PDF"))

POD_TEMPLATE_TYPES = {
    PODTemplate.__name__: PODTemplate,
    ConfigurablePODTemplate.__name__: ConfigurablePODTemplate,
    SubTemplate.__name__: SubTemplate,
    StyleTemplate.__name__: StyleTemplate,
}

DEFAULT_PYTHON_UNO_PATH = "/usr/bin/python"


def get_uno_path():
    return api.portal.get_registry_record(
        "collective.documentgenerator.browser.controlpanel.IDocumentGeneratorControlPanelSchema.uno_path"
    )


def get_oo_port():
    return api.portal.get_registry_record(
        "collective.documentgenerator.browser.controlpanel.IDocumentGeneratorControlPanelSchema.oo_port"
    )
