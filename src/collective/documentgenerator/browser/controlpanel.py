# -*- coding: utf-8 -*-

from collective.documentgenerator import _
from collective.documentgenerator import interfaces
from collective.documentgenerator.config import DEFAULT_COLUMN_MODIFIER
from collective.documentgenerator.config import DEFAULT_OO_PORT
from collective.documentgenerator.config import DEFAULT_OO_SERVER
from collective.documentgenerator.config import DEFAULT_PYTHON_UNO
from collective.documentgenerator.interfaces import IDocumentGeneratorSettings
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.app.registry.browser.controlpanel import RegistryEditForm
from Products.CMFPlone.utils import safe_unicode
from Products.statusmessages.interfaces import IStatusMessage
from z3c.form import button
from zope import schema
from zope.interface import implementer
from zope.interface import Interface

import inspect
import os


COLUMN_MODIFIER_DESCR = _(
    u'If enabled, this will allow the "table-layout: fixed|auto|none" '
    u'CSS style handling while generating document. If no such style is defined on the table, '
    u'the chosen column modifier of LibreOffice will be applied.')


def _string_to_boolean(value):
    return value == "True"


def check_for_uno(value):
    """
    """

    try:
        inspect.isabstract(IDocumentGeneratorControlPanelSchema)
    except Exception:
        return True
    if 'python' not in value and os.system(value + ' -V') != 0:
        raise interfaces.InvalidPythonPath()
    if os.system(value + ' -c "import unohelper"') != 0:
        raise interfaces.InvalidUnoPath()
    return True


class IDocumentGeneratorControlPanelSchema(Interface):
    """
    """

    oo_server = schema.TextLine(
        title=_(u'oo_server'),
        description=_(u'IP address or hostname of OO.'),
        required=False,
        default=safe_unicode(os.getenv('OO_SERVER', DEFAULT_OO_SERVER)),
    )

    oo_port = schema.Int(
        title=_(u'oo_port'),
        description=_(u'Port Number of OO.'),
        required=False,
        default=int(os.getenv('OO_PORT', DEFAULT_OO_PORT))
    )

    uno_path = schema.TextLine(
        title=_(u'uno path'),
        description=_(u'Path of python with uno.'),
        required=False,
        default=safe_unicode(os.getenv('PYTHON_UNO', DEFAULT_PYTHON_UNO)),
        constraint=check_for_uno
    )

    column_modifier = schema.Choice(
        title=_(u'Table column modifier'),
        description=_(COLUMN_MODIFIER_DESCR),
        vocabulary='collective.documentgenerator.ConfigColumnModifier',
        required=True,
        default=DEFAULT_COLUMN_MODIFIER
    )

    raiseOnError_for_non_managers = schema.Bool(
        title=_(u'Raise an error instead generating the document'),
        description=_(u'If enabled, this will avoid generating a document '
                      u'containing an error, instead a common Plone error will '
                      u'be raised.  Nevertheless to ease debugging, Managers '
                      u'will continue to get errors in the generated document '
                      u'if it uses .odt format.'),
        required=False,
        default=False
    )

    use_stream = schema.Choice(
        title=_(u'Force communication via in/out stream with LibreOffice.'),
        description=_(u'If enabled, this will force using stream to communicate witth LibreOffice server. '
                      u'This must be true if the LO server is not on localhost or is in a docker container.'),
        required=True,
        vocabulary='collective.documentgenerator.ConfigStream',
        default=os.getenv('USE_STREAM', None) is None and 'auto' or _string_to_boolean(os.getenv('USE_STREAM')),
    )


@implementer(IDocumentGeneratorSettings)
class DocumentGeneratorControlPanelEditForm(RegistryEditForm):
    schema = IDocumentGeneratorControlPanelSchema
    label = _(u'Document Generator settings')
    description = _(u'The Document Generator settings control panel')

    @button.buttonAndHandler(_('Save'), name=None)
    def handle_save(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        self.applyChanges(data)
        IStatusMessage(self.request).addStatusMessage(_(u'Changes saved'), 'info')
        self.context.REQUEST.RESPONSE.redirect('@@collective.documentgenerator-controlpanel')

    @button.buttonAndHandler(_('Search & replace'), name='search_and_replace')
    def handleSearchAndReplace(self, action):
        self.request.response.redirect(
            '{context_url}/{view}'.format(
                context_url=self.context.absolute_url(),
                view="@@collective.documentgenerator-searchreplacepanel"
            )
        )

    @button.buttonAndHandler(_('Check Pod Templates'), name='checkPod')
    def handleCheckPod(self, action):
        self.request.response.redirect(
            '{context_url}/{view}'.format(
                context_url=self.context.absolute_url(),
                view="@@check-pod-templates"

            )
        )

    @button.buttonAndHandler(_('Cancel'), name='cancel')
    def handleCancel(self, action):
        IStatusMessage(self.request).addStatusMessage(_(u'Edit cancelled'), 'info')
        self.request.response.redirect(
            '{context_url}/{view}'.format(
                context_url=self.context.absolute_url(),
                view="@@overview-controlpanel"
            )
        )


class DocumentGeneratorSettings(ControlPanelFormWrapper):
    form = DocumentGeneratorControlPanelEditForm
