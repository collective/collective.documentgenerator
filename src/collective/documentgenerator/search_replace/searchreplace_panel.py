# -*- coding: utf-8 -*-
from collections import OrderedDict
from collective.documentgenerator import _
from collective.documentgenerator.search_replace.pod_template import SearchAndReplacePODTemplates
from collective.documentgenerator.utils import get_site_root_relative_path
from collective.z3cform.datagridfield import DataGridFieldFactory
from collective.z3cform.datagridfield import DictRow
from plone import api
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.app.uuid.utils import uuidToObject
from plone.autoform import directives
from plone.autoform.form import AutoExtensibleForm
from plone.z3cform.widget import SingleCheckBoxFieldWidget
from z3c.form import button
from z3c.form import form
from zope import component
from zope import interface
from zope import schema
from zope.interface import Invalid
from zope.interface import invariant

import re


class IReplacementRowSchema(interface.Interface):
    """
    Schema for DataGridField widget's row of field 'replacements'
    """

    search_expr = schema.TextLine(title=_(u"Search"), required=True, default=u"")
    replace_expr = schema.TextLine(title=_(u"Replace"), required=False, default=u"")

    directives.widget("is_regex", SingleCheckBoxFieldWidget)
    is_regex = schema.Bool(title=_(u"Regex?"),)


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
        value_type=schema.Choice(source="collective.documentgenerator.AllPODTemplateWithFile"),
    )
    directives.widget("replacements", DataGridFieldFactory)
    replacements = schema.List(
        title=_(u"Replacements"),
        description=_("The replacements that will be made."),
        required=False,
        value_type=DictRow(schema=IReplacementRowSchema, required=True),
    )

    @invariant
    def has_valid_regexes(data):
        if hasattr(data, 'replacements'):
            for i, row in enumerate(data.replacements):
                if row["is_regex"]:
                    try:
                        re.compile(row["search_expr"])
                    except re.error:
                        raise Invalid(_(u"Incorrect regex at row #{0} : \"{1}\"").format(
                            i + 1, row["search_expr"]))


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
        self.is_previewing = False
        self.results_table = OrderedDict()
        super(DocumentGeneratorSearchReplacePanelForm, self).__init__(context, request)

    @button.buttonAndHandler(_("Preview"), name="preview")
    def handle_preview(self, action):  # pragma: no cover
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        self.perform_preview(data)
        return self.render()

    @button.buttonAndHandler(_("Apply"), name="apply")
    def handle_apply(self, action):  # pragma: no cover
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        self.perform_replacements(data)
        return self.render()

    @button.buttonAndHandler(_("Cancel"), name="cancel")
    def handle_cancel(self, action):  # pragma: no cover
        self.request.response.redirect(
            "{context_url}/{view}".format(
                context_url=self.context.absolute_url(), view="@@collective.documentgenerator-controlpanel"
            )
        )

    def updateActions(self):  # pragma: no cover
        super(DocumentGeneratorSearchReplacePanelForm, self).updateActions()
        self.actions["apply"].addClass("context")  # Make "Apply" button primary

    def updateWidgets(self, prefix=None):  # pragma: no cover
        super(DocumentGeneratorSearchReplacePanelForm, self).updateWidgets(prefix)
        self.widgets["replacements"].auto_append = False

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
        self.results_table = {}

        with SearchAndReplacePODTemplates(templates) as replace:
            for row in form_data["replacements"]:
                row["replace_expr"] = row["replace_expr"] or ""
                search_expr = row["search_expr"]
                replace_expr = row["replace_expr"]
                replace_results = replace.replace(search_expr, replace_expr, is_regex=row["is_regex"])

                for template_uid, template_result in replace_results.items():
                    template = uuidToObject(template_uid)
                    template_path = get_site_root_relative_path(template)
                    self.results_table[template_path] = template_result

        if len(self.results_table) == 0:
            self.status = _("Nothing found.")

    def perform_preview(self, form_data):
        """
        Execute preview action
        """
        if len(form_data["replacements"]) == 0:
            self.status = _("Nothing to preview.")
            return
        templates = self.get_selected_templates(form_data)

        self.results_table = {}

        with SearchAndReplacePODTemplates(templates) as search_replace:
            for row in form_data["replacements"]:
                search_expr = row["search_expr"]
                search_results = search_replace.search(search_expr, is_regex=row["is_regex"])
                for template_uid, template_result in search_results.items():
                    template = uuidToObject(template_uid)
                    template_path = get_site_root_relative_path(template)
                    self.results_table[template_path] = template_result
            self.is_previewing = True

        if len(self.results_table) == 0:
            self.status = _("Nothing found.")


class DocumentGeneratorSearchReplace(ControlPanelFormWrapper):
    """
    DocumentGenerator Search & Replace control panel
    """

    form = DocumentGeneratorSearchReplacePanelForm

    def is_previewing(self):
        return self.form_instance.is_previewing

    def get_results_table(self):
        return self.form_instance.results_table

    def get_template_link(self, path):
        return api.portal.get().absolute_url() + path

    @staticmethod
    def highlight_pod_expr(pod_expr, start, end):
        """
        Add a <strong> HTML tag with class highlight around start and end indices
        """
        return pod_expr[:start] + "<strong class='highlight'>" + pod_expr[start:end] + "</strong>" + pod_expr[end:]
