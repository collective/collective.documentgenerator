# -*- coding: utf-8 -*-

from Products.CMFPlone.utils import safe_unicode
from Products.statusmessages.interfaces import IStatusMessage

from collective.documentgenerator import _
from collective.documentgenerator import interfaces
from collective.documentgenerator.interfaces import IDocumentGeneratorSettings

from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.app.registry.browser.controlpanel import RegistryEditForm

from z3c.form import button

from zope import schema
from zope.interface import Interface
from zope.interface import implements

import inspect
import os


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

    oo_port = schema.Int(
        title=_(u'oo_port'),
        description=_(u'Port Number of OO.'),
        required=False,
        default=int(os.getenv('OO_PORT', 2002))
    )

    uno_path = schema.TextLine(
        title=_(u'uno path'),
        description=_(u'Path of python with uno.'),
        required=False,
        default=safe_unicode(os.getenv('PYTHON_UNO', u'/usr/bin/python')),
        constraint=check_for_uno
    )

    optimize_tables = schema.Bool(
        title=_(u'Optimize tables'),
        description=_(u'This will apply the "Optimize table columns width" of '
                      u'LibreOffice to tables that do not use the '
                      u'"table-layout: fixed" CSS style.'),
        required=False,
        default=False
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


class DocumentGeneratorControlPanelEditForm(RegistryEditForm):

    implements(IDocumentGeneratorSettings)

    schema = IDocumentGeneratorControlPanelSchema
    label = _(u'Document Generator settings')
    description = _(u'')

    @button.buttonAndHandler(_('Save'), name=None)
    def handle_save(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        self.applyChanges(data)
        IStatusMessage(self.request).addStatusMessage(_(u'Changes saved'), 'info')
        self.context.REQUEST.RESPONSE.redirect('@@collective.documentgenerator-controlpanel')

    @button.buttonAndHandler(_('Cancel'), name='cancel')
    def handleCancel(self, action):
        IStatusMessage(self.request).addStatusMessage(_(u'Edit cancelled'), 'info')
        self.request.response.redirect(
            '{context_url}/{view}'.format(
                context_url=self.context.absolute_url(),
                view=self.control_panel_view
            )
        )


class DocumentGeneratorSettings(ControlPanelFormWrapper):
    form = DocumentGeneratorControlPanelEditForm
