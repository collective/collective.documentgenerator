import inspect
import os

from Products.statusmessages.interfaces import IStatusMessage

from collective.documentgenerator import _
from collective.documentgenerator.interfaces import IDocumentGeneratorSettings

from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper

from z3c.form import button

from zope.interface import implements
from zope.interface import Interface

from zope import schema
from zope.schema import ValidationError


class InvalidPythonPath(ValidationError):
    "Invalid Python path"


class InvalidUnoPath(ValidationError):
    "Can't import python uno library with the python path"


def checkForUno(value):
    try:
        inspect.isabstract(IDocumentGeneratorControlPanelSchema)
    except Exception:
        return True
    if "python" in value and os.system(value + " -V") != 0:
        raise InvalidPythonPath()
    if os.system(value + " -c 'import uno'") != 0:
        raise InvalidUnoPath()
    return True


class IDocumentGeneratorControlPanelSchema(Interface):
    """
    """

    oo_port = schema.Int(
        title=_(u"oo_port"),
        description=_(u"Port Number of OO"),
        required=False,
        default=False
    )

    oo_unoPath = schema.TextLine(
        title=_(u"oo_unoPath"),
        description=_(u"uno path of OO"),
        required=False,
        default=u"/usr/bin/python",
        constraint=checkForUno
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
