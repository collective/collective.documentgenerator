# -*- coding: utf-8 -*-
from collections import OrderedDict
from collective.documentgenerator import _
from collective.documentgenerator.content.vocabulary import AllPODTemplateWithFileVocabularyFactory
from collective.documentgenerator.search_replace.pod_template import SearchAndReplacePODTemplates
from imio.helpers.content import HAS_PLONE5
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.app.uuid.utils import uuidToObject
from plone.autoform import directives
from plone.autoform.form import AutoExtensibleForm
from plone.z3cform.widget import SingleCheckBoxFieldWidget
from z3c.form import button
from z3c.form import form
from z3c.form.contentprovider import ContentProviders
from z3c.form.interfaces import IFieldsAndContentProvidersForm
from zope import component
from zope import interface
from zope import schema
from zope.browserpage.viewpagetemplatefile import ViewPageTemplateFile
from zope.contentprovider.provider import ContentProviderBase
from zope.interface import implements
from zope.interface import Invalid
from zope.interface import invariant

import re

if HAS_PLONE5:
    from collective.z3cform.datagridfield.datagridfield import DataGridFieldFactory
    from collective.z3cform.datagridfield.row import DictRow
else:
    from collective.z3cform.datagridfield import DataGridFieldFactory
    from collective.z3cform.datagridfield import DictRow


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


class SearchResultProvider(ContentProviderBase):
    """
    Search result and replace form is implemented through a content provider.
    """

    template = ViewPageTemplateFile('search_result_form.pt')

    def __init__(self, context, request, view):
        super(SearchResultProvider, self).__init__(context, request, view)
        self.view = view
        self.results_table = OrderedDict()

    def render(self):
        return self.template()

    def is_previewing(self):
        return self.view.is_previewing

    def get_results_table(self):
        return self.view.results_table

    def get_template_link(self, uid):
        template = uuidToObject(uid)
        return template.absolute_url()

    def get_template_breadcrumb(self, uid):
        template = uuidToObject(uid)
        breadcrumb_view = template.restrictedTraverse('breadcrumbs_view')
        title = ' / '.join([bc['Title'] for bc in breadcrumb_view.breadcrumbs()]) + ' ({})'.format(template.id)
        return title

    @staticmethod
    def display_diff(result):
        """
        Add a <strong> HTML tag with class highlight around start and end indices
        """
        return result.getDiff(type="xhtml")


class DocumentGeneratorSearchReplacePanelAdapter(object):
    interface.implements(IDocumentGeneratorSearchReplacePanelSchema)
    component.adapts(interface.Interface)

    def __init__(self, context):
        self.context = context


class DocumentGeneratorSearchReplacePanelForm(AutoExtensibleForm, form.Form):
    """
    DocumentGenerator Search & Replace control panel form
    """
    implements(IFieldsAndContentProvidersForm)

    schema = IDocumentGeneratorSearchReplacePanelSchema
    label = _(u"Search & Replace")
    description = _(u"Search & replace among all template directives in this Plone site templates")

    # display the search result and replace form as content provider
    contentProviders = ContentProviders()
    contentProviders['search_result_provider'] = SearchResultProvider
    # defining a contentProvider position is mandatory...
    contentProviders['search_result_provider'].position = 2

    def __init__(self, context, request):
        self.is_previewing = False
        self.results_table = OrderedDict()
        super(DocumentGeneratorSearchReplacePanelForm, self).__init__(context, request)

    @button.buttonAndHandler(_("Replace"), name="replace", condition=lambda form: form.can_replace())
    def handle_replace(self, action):  # pragma: no cover
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        self.perform_replacements(data)
        return self.render()

    @button.buttonAndHandler(_("Search"), name="search")
    def handle_search(self, action):  # pragma: no cover
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        self.perform_preview(data)
        return self.render()

    @button.buttonAndHandler(_("Cancel"), name="cancel")
    def handle_cancel(self, action):  # pragma: no cover
        self.request.response.redirect(
            "{context_url}/{view}".format(
                context_url=self.context.absolute_url(), view="@@collective.documentgenerator-controlpanel"
            )
        )

    def can_replace(self):
        # allow to perform a replace only if we performed a search first or if we are performing the replace
        search_done = self.request.get('form.buttons.search', False)
        replacing = self.request.get('selected_templates', False)
        return search_done or replacing

    def updateActions(self):  # pragma: no cover
        super(DocumentGeneratorSearchReplacePanelForm, self).updateActions()
        self.actions["search"].addClass("context")  # Make "Search" button primary
        if self.request.get('selected_templates', False):  # Must do a new new search before replacing again
            self.actions["replace"].addClass("hidden")

    def updateWidgets(self, prefix=None):  # pragma: no cover
        super(DocumentGeneratorSearchReplacePanelForm, self).updateWidgets(prefix)
        self.widgets["replacements"].auto_append = False

    @staticmethod
    def get_selected_templates(form_data):
        """
        Get selected templates from form_data
        """
        uids = form_data["selected_templates"]
        if 'all' in uids:
            voc = AllPODTemplateWithFileVocabularyFactory()
            uids = [brain.UID for brain in voc._get_all_pod_templates_with_file()]
        templates = [uuidToObject(template_uuid) for template_uuid in uids]
        return templates

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
                    if not self.results_table.get(template_uid):
                        self.results_table[template_uid] = template_result
                    else:
                        self.results_table[template_uid].extend(template_result)

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
                    if not self.results_table.get(template_uid):
                        self.results_table[template_uid] = template_result
                    else:
                        self.results_table[template_uid].extend(template_result)
            self.is_previewing = True

        if len(self.results_table) == 0:
            self.status = _("Nothing found.")


class DocumentGeneratorSearchReplace(ControlPanelFormWrapper):
    """
    DocumentGenerator Search & Replace control panel
    """

    form = DocumentGeneratorSearchReplacePanelForm
