# -*- coding: utf-8 -*-
import copy

from collective.documentgenerator import _
from collective.documentgenerator.interfaces import IPODTemplateCondition
from collective.documentgenerator.interfaces import ITemplatesToMerge
from collective.documentgenerator.utils import compute_md5

from collective.z3cform.datagridfield import DataGridFieldFactory
from collective.z3cform.datagridfield import DictRow
from collective.documentgenerator.config import NEUTRAL_FORMATS
from collective.documentgenerator.config import ODS_FORMATS
from collective.documentgenerator.config import ODT_FORMATS
from collective.documentgenerator.config import POD_FORMATS
from collective.documentgenerator.content.style_template import StyleTemplate

from plone import api
from plone.autoform import directives as form
from plone.dexterity.content import Item
from plone.formwidget.namedfile import NamedFileWidget
from plone.namedfile.field import NamedBlobFile
from plone.supermodel import model

from z3c.form import validator
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form.browser.orderedselect import OrderedSelectFieldWidget
from z3c.form.browser.radio import RadioFieldWidget
from z3c.form.browser.select import SelectWidget

from zope import schema
from zope.component import provideAdapter
from zope.component import queryAdapter
from zope.component import queryMultiAdapter
from zope.interface import implements
from zope.interface import Interface
from zope.interface import Invalid
from zope.interface import invariant

import logging

from Products.CMFPlone.utils import safe_unicode


logger = logging.getLogger('collective.documentgenerator: PODTemplate')


class IPODTemplate(model.Schema):
    """
    PODTemplate dexterity schema.
    """

    model.primary('odt_file')
    form.widget('odt_file', NamedFileWidget)
    odt_file = NamedBlobFile(
        title=_(u'ODT File'),
    )

    form.omitted('initial_md5')
    initial_md5 = schema.TextLine()

    form.widget('enabled', RadioFieldWidget)
    enabled = schema.Bool(
        title=_(u'Enabled'),
        default=True,
        required=False,
    )


class PODTemplate(Item):
    """
    PODTemplate dexterity class.
    """

    implements(IPODTemplate)

    def get_file(self):
        return self.odt_file

    def can_be_generated(self, context):
        """
        Evaluate if the template can be generated on a given context.
        """
        condition_obj = queryMultiAdapter((self, context), IPODTemplateCondition)
        if condition_obj:
            can_be_generated = condition_obj.evaluate()
            return can_be_generated

    def get_style_template(self):
        """
        Return associated StylesTemplate from which styles will be imported
        to the current PODTemplate.
        """
        return None

    def get_templates_to_merge(self):
        """
        Return associated PODTemplates merged into the current PODTemplate
        when it is rendered.
        """
        templates_to_merge = queryAdapter(self, ITemplatesToMerge)
        if templates_to_merge:
            return templates_to_merge.get()
        return {}

    def get_available_formats(self):
        """
        Returns formats in which current template may be generated.
        """
        return ['odt', ]

    @property
    def current_md5(self):
        md5 = u''
        if self.odt_file:
            md5 = safe_unicode(compute_md5(self.odt_file.data))
        return md5

    def has_been_modified(self):
        has_been_modified = self.current_md5 != self.initial_md5
        return has_been_modified


class IMergeTemplatesRowSchema(Interface):
    """
    Schema for DataGridField widget's row of field 'merge_templates'
    """
    template = schema.Choice(
        title=_(u'Template'),
        vocabulary='collective.documentgenerator.MergeTemplates',
        required=True,
    )

    pod_context_name = schema.TextLine(
        title=_(u'POD context name'),
        required=True,
    )

    form.widget('do_rendering', RadioFieldWidget)
    do_rendering = schema.Bool(
        title=_(u'Do rendering'),
    )


class IContextVariablesRowSchema(Interface):
    """
    Schema for DataGridField widget's row of field 'context_variables'
    """
    name = schema.TextLine(
        title=_(u'Variable name'),
        required=True,
    )

    value = schema.TextLine(
        title=_(u'Value'),
        required=False,
    )


class PodFormatsValidator(validator.SimpleFieldValidator):
    """ z3c.form validator class for Pod formats """

    def validate(self, selected_formats):
        # thanks to widget, we get just-loaded file.filename.
        widgets = self.view.widgets
        current_filename = u""
        for element in widgets.items():
            if element[0] == 'odt_file':
                current_filename = safe_unicode(element[1].filename)
        if current_filename:
            FORMATS_DICT = {'ods': ODS_FORMATS + NEUTRAL_FORMATS,
                            'odt': ODT_FORMATS + NEUTRAL_FORMATS}
            extension = current_filename.split('.')[-1]
            authorise_element_list = FORMATS_DICT[extension]
            authorise_extension_list = [elem[0] for elem in authorise_element_list]
            if not selected_formats:
                raise Invalid(_(u"No format selected"))
            for element in selected_formats:
                if element not in authorise_extension_list:
                    elem = self.get_invalid_error(element)
                    error_message = _(
                        u"element_not_valid",
                        default=u"Element ${elem} is not valid for .${extension} template : \"${template}\"",
                        mapping={u"elem": elem, u"extension": extension, u"template": current_filename})
                    raise Invalid(error_message)

    def get_invalid_error(self, extension):
        for element in POD_FORMATS:
            if element[0] == extension:
                return element[1]


class IConfigurablePODTemplate(IPODTemplate):
    """
    ConfigurablePODTemplate dexterity schema.
    """

    form.widget('pod_formats', OrderedSelectFieldWidget, multiple='multiple', size=5)
    pod_formats = schema.List(
        title=_(u'Available formats'),
        description=_(u'Select format in which the template will be generable.'),
        value_type=schema.Choice(source='collective.documentgenerator.Formats'),
        required=True,
        default=['odt', ],
    )

    form.widget('pod_portal_types', CheckBoxFieldWidget, multiple='multiple', size=15)
    pod_portal_types = schema.List(
        title=_(u'Allowed portal types'),
        description=_(u'Select for which content types the template will be available.'),
        value_type=schema.Choice(source='collective.documentgenerator.PortalTypes'),
        required=False,
    )

    form.widget('style_template', SelectWidget)
    style_template = schema.List(
        title=_(u'Style template'),
        description=_(u'Choose the style template to apply for this template.'),
        value_type=schema.Choice(source='collective.documentgenerator.StyleTemplates'),
        required=True,
    )

    form.widget('merge_templates', DataGridFieldFactory)
    merge_templates = schema.List(
        title=_(u'Templates to merge.'),
        required=False,
        value_type=DictRow(
            schema=IMergeTemplatesRowSchema,
            required=False
        ),
        default=[],
    )

    form.widget('context_variables', DataGridFieldFactory)
    context_variables = schema.List(
        title=_(u'Context variables.'),
        description=_("These context variables are added to the odt_file context."),
        required=False,
        value_type=DictRow(
            schema=IContextVariablesRowSchema,
            required=False
        ),
    )

    @invariant
    def validate_context_variables(data):
        keys = []
        forbidden = ['context', 'view', 'uids', 'brains', 'self']
        to_check = copy.deepcopy(data.context_variables or [])
        to_check.extend(copy.deepcopy(data.merge_templates or []))

        for line in to_check:
            value = ('name' in line and line['name']) or ('pod_context_name' in line and line['pod_context_name'])

            if value in forbidden:
                raise Invalid(_("You can't use one of these words: ${list}", mapping={'list': ', '.join(forbidden)}))

            if value in keys:
                raise Invalid(_("You have twice used the same name '${name}'", mapping={'name': value}))
            else:
                keys.append(value)

# Set conditions for which fields the validator class applies
validator.WidgetValidatorDiscriminators(PodFormatsValidator, field=IConfigurablePODTemplate['pod_formats'])

# Register the validator so it will be looked up by z3c.form machinery
provideAdapter(PodFormatsValidator)


class ConfigurablePODTemplate(PODTemplate):
    """
    ConfigurablePODTemplate dexterity class.
    """

    implements(IConfigurablePODTemplate)

    def get_style_template(self):
        """
        Return associated StylesTemplate from which styles will be imported
        to the current PODTemplate.
        """
        catalog = api.portal.get_tool('portal_catalog')
        style_template_UID = self.style_template
        if not style_template_UID:
            # do not query catalog if no style_template
            return

        style_template_brain = catalog(UID=style_template_UID)

        if style_template_brain:
            style_template = style_template_brain[0].getObject()
        else:
            style_template = None

        return style_template

    def set_merge_templates(self, pod_template, pod_context_name, do_rendering=True, position=-1):
        old_value = list(self.merge_templates)
        newline = {'template': pod_template.UID(), 'pod_context_name': pod_context_name, 'do_rendering': do_rendering}
        if position >= 0:
            old_value.insert(position, newline)
        else:
            old_value.append(newline)
        self.merge_templates = old_value

    def get_templates_to_merge(self):
        """
        Return associated PODTemplates merged into the current PODTemplate
        when it is rendered.
        """
        catalog = api.portal.get_tool('portal_catalog')
        pod_context = {}

        if self.merge_templates:
            for line in self.merge_templates:
                pod_template = catalog(UID=line['template'])[0].getObject()
                pod_context[line['pod_context_name'].encode('utf-8')] = (pod_template, line['do_rendering'])

        return pod_context

    def get_available_formats(self):
        """
        Returns formats in which current template may be generated.
        """
        return self.pod_formats

    def get_context_variables(self):
        """
            Returns context_variables as dict
        """
        ret = {}
        for line in self.context_variables or []:
            # Simple boolean conversion actually implemented
            # May be improved with ZPublisher.Converters, managing boolean, int, date, string, text, ...
            # Those last values in a list box with string as default value
            val = line['value']
            if val == 'True':
                val = True
            elif val == 'False':
                val = False
            ret[line['name']] = val
        return ret


class ISubTemplate(IPODTemplate):
    """
    PODTemplate used only a sub template to merge
    """


class SubTemplate(PODTemplate):
    """
    PODTemplate used only a sub template to merge
    """

    implements(ISubTemplate)

POD_TEMPLATE_TYPES = {
    PODTemplate.__name__: PODTemplate,
    ConfigurablePODTemplate.__name__: ConfigurablePODTemplate,
    SubTemplate.__name__: SubTemplate,
    StyleTemplate.__name__: StyleTemplate,
}
