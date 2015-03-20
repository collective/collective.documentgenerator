import inspect
import os

from Products.statusmessages.interfaces import IStatusMessage

from collective.documentgenerator import _
from collective.documentgenerator import interfaces
from collective.documentgenerator.interfaces import IDocumentGeneratorSettings

from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper

from z3c.form import button

from zope.interface import implements
from zope.interface import Interface

from zope import schema


def check_for_uno(value):
    """
    """

    try:
        inspect.isabstract(IDocumentGeneratorControlPanelSchema)
    except Exception:
        return True
    if "python" not in value and os.system(value + " -V") != 0:
        raise interfaces.InvalidPythonPath()
    if os.system(value + " -c 'import uno'") != 0:
        raise interfaces.InvalidUnoPath()
    return True


class IDocumentGeneratorControlPanelSchema(Interface):
    """
    """

    oo_port = schema.Int(
        title=_(u"oo_port"),
        description=_(u"Port Number of OO"),
        required=False,
        default=2002
    )

    uno_path = schema.TextLine(
        title=_(u"uno path"),
        description=_(u"Path of python with uno"),
        required=False,
        default=u"/usr/bin/python",
        constraint=check_for_uno
    )


class DocumentGeneratorControlPanelEditForm(RegistryEditForm):

    implements(IDocumentGeneratorSettings)

    schema = IDocumentGeneratorControlPanelSchema
    label = _(u"Document Generator settings")
    description = _(u"")

    @button.buttonAndHandler(_('Save'), name=None)
    def handle_save(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        self.applyChanges(data)
        IStatusMessage(self.request).addStatusMessage(_(u"Changes saved"), "info")
        self.context.REQUEST.RESPONSE.redirect("@@collective.documentgenerator-controlpanel")

    @button.buttonAndHandler(_('Cancel'), name='cancel')
    def handleCancel(self, action):
        IStatusMessage(self.request).addStatusMessage(_(u"Edit cancelled"), "info")
        self.request.response.redirect("%s/%s" % (self.context.absolute_url(), self.control_panel_view))


class DocumentGeneratorSettings(ControlPanelFormWrapper):
    form = DocumentGeneratorControlPanelEditForm
