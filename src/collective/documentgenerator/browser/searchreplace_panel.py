# -*- coding: utf-8 -*-
from Products.CMFPlone.utils import safe_unicode
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.app.uuid.utils import uuidToObject
from plone.autoform import directives
from plone.autoform.form import AutoExtensibleForm
from plone.z3cform.widget import SingleCheckBoxFieldWidget
from z3c.form import button, form
from zope import schema, interface, component

from collective.z3cform.datagridfield import DictRow, DataGridFieldFactory
from collective.documentgenerator import _


class IReplacementRowSchema(interface.Interface):
    """
    Schema for DataGridField widget's row of field 'replacements'
    """

    name = schema.TextLine(title=_(u"Search"), required=True,)
    value = schema.TextLine(title=_(u"Replace"), required=False,)

    directives.widget("include", SingleCheckBoxFieldWidget)
    include = schema.Bool(title=_(u"Preview ?"),)


class IDocumentGeneratorSearchReplacePanelSchema(interface.Interface):
    """
    Schema for DocumentGeneratorSearchReplacePanel
    """

    selected_templates = schema.List(
        title=_(u"heading_selected_templates", default=u"Selected templates"),
        description=_(u"description_selected_templates", default=u"Select which templates."),
        required=False,
        default=[],
        missing_value=[],
        value_type=schema.Choice(source="collective.documentgenerator.AllPODTemplate"),
    )
    directives.widget("replacements", DataGridFieldFactory)
    replacements = schema.List(
        title=_(u"Replacements"),
        description=_("The replacements that will be made."),
        required=False,
        value_type=DictRow(schema=IReplacementRowSchema, required=True),
    )


class DocumentGeneratorSearchReplacePanelAdapter(object):
    interface.implements(IDocumentGeneratorSearchReplacePanelSchema)
    component.adapts(interface.Interface)

    def __init__(self, context):
        self.name = None


class DocumentGeneratorSearchReplacePanelForm(AutoExtensibleForm, form.Form):
    schema = IDocumentGeneratorSearchReplacePanelSchema
    label = _(u"Search & Replace")
    description = _(u"Search & replace among all template directives in this Plone site templates")

    def __init__(self, context, request):
        self.preview = {}
        self.results = {}
        super(DocumentGeneratorSearchReplacePanelForm, self).__init__(context, request)

    @button.buttonAndHandler(_("Launch"), name="launch")
    def handle_launch(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        for template_uuid in data["selected_templates"]:
            # TODO : do the actual operation
            template = uuidToObject(template_uuid)
            self.results[self.print_template(template)] = {"matched": "self.getItem()", "replaced_by": "self.get_grouped()"}

        return self.render()

    @button.buttonAndHandler(_("Preview"), name="preview")
    def handle_preview(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        for template_uuid in data["selected_templates"]:
            # TODO : do the actual operation
            template = uuidToObject(template_uuid)
            self.preview[self.print_template(template)] = "self.getItem()"

        return self.render()

    @button.buttonAndHandler(_("Cancel"), name="cancel")
    def handle_cancel(self, action):
        self.request.response.redirect(
            "{context_url}/{view}".format(
                context_url=self.context.absolute_url(), view="@@collective.documentgenerator-controlpanel"
            )
        )

    def updateActions(self):
        super(DocumentGeneratorSearchReplacePanelForm, self).updateActions()
        self.actions["launch"].addClass("context")  # Make Launch button primary

    def updateWidgets(self):
        super(DocumentGeneratorSearchReplacePanelForm, self).updateWidgets()
        self.widgets["replacements"].auto_append = False

    def print_template(self, template):
        return u"{} -> {}".format(safe_unicode(template.Title()), safe_unicode(template.odt_file.filename))


class DocumentGeneratorSearchReplace(ControlPanelFormWrapper):
    form = DocumentGeneratorSearchReplacePanelForm

    def get_preview(self):
        return self.form_instance.preview

    def get_results(self):
        return self.form_instance.results
