from plone import api


def get_uno_path():
    return api.portal.get_registry_record(
        "collective.documentgenerator.browser.controlpanel.IDocumentGeneratorControlPanelSchema.oo_unoPath"
    )
