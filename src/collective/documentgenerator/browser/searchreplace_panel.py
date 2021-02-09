# -*- coding: utf-8 -*-
from collections import OrderedDict

from collective.documentgenerator.helper.search_replace import PODTemplateSearchReplace
from collective.documentgenerator.utils import get_site_root_relative_path
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

    search_expr = schema.TextLine(title=_(u"Search"), required=True,)
    replace_expr = schema.TextLine(title=_(u"Replace"), required=False,)

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
        self.preview_table = OrderedDict()
        self.results_list = []
        super(DocumentGeneratorSearchReplacePanelForm, self).__init__(context, request)

    @button.buttonAndHandler(_("Launch"), name="launch")
    def handle_launch(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        for template_uuid in data["selected_templates"]:  # TODO : Exctract me elsewhere !
            with PODTemplateSearchReplace(template_uuid) as podtemplate_search_replace:
                for replacement in data["replacements"]:
                    podtemplate_search_replace.replace(
                        replacement["search_expr"], replacement["replace_expr"]
                    )
        return self.render()

    @button.buttonAndHandler(_("Preview"), name="preview")
    def handle_preview(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        for template_uuid in data["selected_templates"]:  # TODO : Exctract me elsewhere !
            template = uuidToObject(template_uuid)
            template_path = get_site_root_relative_path(template)
            search_expr = self.get_search_exprs(data["replacements"])
            self.preview_table[template_path] = []
            with PODTemplateSearchReplace(template_uuid) as podtemplate_search_replace:
                search_results = podtemplate_search_replace.search(search_expr)
                for search_result in search_results:
                    self.preview_table[template_path].append(search_result)

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

    def get_search_exprs(self, replacements_form_data):
        results = []
        for replacement in replacements_form_data:
            if replacement["include"]:
                results.append(replacement["search_expr"])
        return results


class DocumentGeneratorSearchReplace(ControlPanelFormWrapper):
    form = DocumentGeneratorSearchReplacePanelForm

    def get_preview_table(self):
        return self.form_instance.preview_table

    def get_results_list(self):
        return self.form_instance.results_list
