# -*- coding: utf-8 -*-
import re
from collections import OrderedDict

from collective.documentgenerator.utils import get_site_root_relative_path
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.app.uuid.utils import uuidToObject
from plone.autoform import directives
from plone.autoform.form import AutoExtensibleForm
from plone.z3cform.widget import SingleCheckBoxFieldWidget
from z3c.form import button, form
from zope import schema, interface, component

from collective.z3cform.datagridfield import DictRow, DataGridFieldFactory
from collective.documentgenerator.search_replace.pod_template import SearchAndReplacePODTemplates
from collective.documentgenerator import _


class IReplacementRowSchema(interface.Interface):
    """
    Schema for DataGridField widget's row of field 'replacements'
    """

    def is_valid_regex(value):
        try:
            re.compile(value)
            return True
        except re.error:
            return False

    search_expr = schema.TextLine(title=_(u"Search"), required=True, default=u"", constraint=is_valid_regex)
    replace_expr = schema.TextLine(title=_(u"Replace"), required=False, default=u"")

    directives.widget("include", SingleCheckBoxFieldWidget)
    include = schema.Bool(title=_(u"Preview ?"),)


class IDocumentGeneratorSearchReplacePanelSchema(interface.Interface):
    """
    Schema for DocumentGeneratorSearchReplacePanel
    """

    selected_templates = schema.List(
        title=_(u"heading_selected_templates", default=u"Selected templates"),
        description=_(u"description_selected_templates", default=u""),
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
        self.context = context


class DocumentGeneratorSearchReplacePanelForm(AutoExtensibleForm, form.Form):
    """
    DocumentGenerator Search & Replace control panel form
    """

    schema = IDocumentGeneratorSearchReplacePanelSchema
    label = _(u"Search & Replace")
    description = _(u"Search & replace among all template directives in this Plone site templates")

    def __init__(self, context, request):
        self.preview_table = OrderedDict()
        self.results_table = OrderedDict()
        super(DocumentGeneratorSearchReplacePanelForm, self).__init__(context, request)

    @button.buttonAndHandler(_("Launch"), name="launch")
    def handle_launch(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        self.perform_replacements(data)
        return self.render()

    @button.buttonAndHandler(_("Preview"), name="preview")
    def handle_preview(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        self.perform_preview(data)
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

    def updateWidgets(self, prefix=None):
        super(DocumentGeneratorSearchReplacePanelForm, self).updateWidgets(prefix)
        self.widgets["replacements"].auto_append = False

    @staticmethod
    def get_search_exprs(replacements_form_data):
        """
        Get all search expressions from form_data
        """
        filtered = filter(lambda replacement: replacement["include"], replacements_form_data)
        search_exprs = map(lambda r: r["search_expr"], filtered)
        return search_exprs

    @staticmethod
    def get_selected_templates(form_data):
        """
        Get selected templates from form_data
        """
        return [uuidToObject(template_uuid) for template_uuid in form_data["selected_templates"]]

    def perform_replacements(self, form_data):
        """
        Execute replacements action
        """
        if len(form_data["replacements"]) == 0:
            self.status = _("Nothing to replace.")
            return

        templates = self.get_selected_templates(form_data)
        self.results_table = {get_site_root_relative_path(template): [] for template in templates}

        with SearchAndReplacePODTemplates(templates) as replace:
            for replacement in form_data["replacements"]:
                replacement["replace_expr"] = replacement["replace_expr"] or ""
                search_expr = replacement["search_expr"]
                replace_expr = replacement["replace_expr"]
                replace_results = replace.replace(search_expr, replace_expr)

                for template_uid, template_result in replace_results.items():
                    template = uuidToObject(template_uid)
                    template_path = get_site_root_relative_path(template)
                    self.results_table[template_path] += template_result

    def perform_preview(self, form_data):
        """
        Execute preview action
        """
        search_exprs = self.get_search_exprs(form_data["replacements"])
        if len(search_exprs) == 0:
            self.status = _("Nothing to preview.")
            return
        templates = self.get_selected_templates(form_data)

        self.preview_table = {get_site_root_relative_path(template): [] for template in templates}

        with SearchAndReplacePODTemplates(templates) as search_replace:
            for search_expr in search_exprs:
                search_results = search_replace.search(search_expr)
                for template_uid, template_result in search_results.items():
                    template = uuidToObject(template_uid)
                    template_path = get_site_root_relative_path(template)
                    self.preview_table[template_path] += template_result


class DocumentGeneratorSearchReplace(ControlPanelFormWrapper):
    """
    DocumentGenerator Search & Replace control panel
    """

    form = DocumentGeneratorSearchReplacePanelForm

    def get_preview_table(self):
        return self.form_instance.preview_table

    def get_results_table(self):
        return self.form_instance.results_table

    @staticmethod
    def highlight_pod_expr(pod_expr, start, end):
        """
        Add a <strong> HTML tag with class highlight around start and end indices
        """
        return pod_expr[:start] + "<strong class='highlight'>" + pod_expr[start:end] + "</strong>" + pod_expr[end:]
