# -*- coding: utf-8 -*-
import re
from collections import OrderedDict

from collective.documentgenerator.helper.search_replace import SearchPODTemplates
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

import mimetypes
import os


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
        self.name = None


class DocumentGeneratorSearchReplacePanelForm(AutoExtensibleForm, form.Form):
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

    def get_search_exprs(self, replacements_form_data):
        filtered = filter(lambda replacement: replacement["include"], replacements_form_data)
        search_exprs = map(lambda r: r["search_expr"], filtered)
        return search_exprs

    def highlight_pod_expr(self, pod_expr, start, end):
        return pod_expr[:start] + "<b class='highlight'>" + pod_expr[start:end] + "</b>" + pod_expr[end:]

    def perform_replacements(self, form_data):
        for template_uuid in form_data["selected_templates"]:
            template = uuidToObject(template_uuid)
            template_path = get_site_root_relative_path(template)
            self.results_table[template_path] = []
            with SearchSitePODTemplates(template) as search_replace:
                for replacement in form_data["replacements"]:
                    if replacement["replace_expr"] is None:
                        replacement["replace_expr"] = ""

                    replace_results = search_replace.replace(
                        replacement["search_expr"], replacement["replace_expr"]
                    )
                    for replace_result in replace_results:
                        replace_result["old_pod_expr"] = self.highlight_pod_expr(
                            replace_result["old_pod_expr"], replace_result["match_start"],
                            replace_result["match_end"]
                        )
                        self.results_table[template_path].append(replace_result)

    def perform_preview(self, form_data):
        search_expr = self.get_search_exprs(form_data["replacements"])
        if len(search_expr) == 0:
            self.status = _("Nothing to preview.")
            return

        templates = []
        for template_uuid in form_data["selected_templates"]:
            template = uuidToObject(template_uuid)
            templates.append(template)
            template_path = get_site_root_relative_path(template)
            self.preview_table[template_path] = []

        with SearchSitePODTemplates(templates) as search:
            search_results = search.run(search_expr)
            for filename, search_result in search_results.iteritems():
                template_path = search.templates_by_filename[filename]['path']
                for match_pod_zone in search_result[1]:
                    pod_expr = match_pod_zone["XMLnode"].data
                    for match in match_pod_zone['matches']:
                        to_display = {'pod_expr': pod_expr}
                        match_start = match.start()
                        match_end = match.end()
                        to_display['match'] = pod_expr[match_start:match_end]
                        to_display["pod_expr"] = self.highlight_pod_expr(
                            pod_expr, match_start, match_end
                        )
                        self.preview_table[template_path].append(to_display)


class DocumentGeneratorSearchReplace(ControlPanelFormWrapper):
    form = DocumentGeneratorSearchReplacePanelForm

    def get_preview_table(self):
        return self.form_instance.preview_table

    def get_results_table(self):
        return self.form_instance.results_table


class SearchSitePODTemplates(SearchPODTemplates):
    """
    """

    def __init__(self, pod_templates, find_expr=[''], ignorecase=False, recursive=False, silent=False):
        """
        """
        self.pod_templates = pod_templates
        self.templates_by_filename = {}
        self.tmp_dir = '/tmp/docgen'
        if not os.path.isdir(self.tmp_dir):
            os.mkdir(self.tmp_dir)

        # compute the (future) file system path of the plone pod templates
        for pod_template in pod_templates:
            template_path = get_site_root_relative_path(pod_template)
            extension = mimetypes.guess_extension(pod_template.odt_file.contentType)
            fs_filename = '{}/{}{}'.format(self.tmp_dir, template_path.replace('/', '_'), extension)
            self.templates_by_filename[fs_filename] = {'obj': pod_template, 'path': template_path}

        filenames_expr = self.templates_by_filename.keys()

        super(SearchSitePODTemplates, self).__init__(find_expr, filenames_expr, ignorecase, recursive)

    def __enter__(self):
        """
        copy the plone pod template content on the file system
        """
        for filename in self.filenames_expr:
            # clean old files
            if os.path.isfile(filename):
                os.remove(filename)
            # copy the pod templates on the file system.
            template_file = open(filename, 'w')
            plone_template = self.templates_by_filename[filename]['obj']
            template_file.write(plone_template.odt_file.data)
            template_file.close()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        for filename in self.filenames_expr:
            if os.path.isfile(filename):
                os.remove(filename)
