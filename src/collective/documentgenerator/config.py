from plone import api

DEFAULT_PYTHON_UNO_PATH = "/usr/bin/python"
def get_uno_path():
    return api.portal.get_registry_record(
        "collective.documentgenerator.browser.controlpanel.IDocumentGeneratorControlPanelSchema.uno_path"
    )


def get_oo_port():
    return api.portal.get_registry_record(
        "collective.documentgenerator.browser.controlpanel.IDocumentGeneratorControlPanelSchema.oo_port"
    )
