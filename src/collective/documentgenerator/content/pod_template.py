# -*- coding: utf-8 -*-

from collective.documentgenerator import _
from collective.documentgenerator.interfaces import IPODTemplateCondition
from collective.documentgenerator.interfaces import ITemplatesToMerge
from collective.documentgenerator.utils import compute_md5

from collective.z3cform.datagridfield import DataGridFieldFactory
from collective.z3cform.datagridfield import DictRow

from plone import api
from plone.autoform import directives as form
from plone.dexterity.content import Item
from plone.formwidget.namedfile import NamedFileWidget
from plone.namedfile.field import NamedBlobFile
from plone.supermodel import model

from zope import schema
from zope.component import queryAdapter
from zope.component import queryMultiAdapter
from zope.interface import implements
from zope.schema._messageid import _ as zope_message_factory

from z3c.form.browser.select import SelectWidget

import logging
import zope
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
        md5 = ''
        if self.odt_file:
            md5 = compute_md5(self.odt_file.data)
        return md5

    def has_been_modified(self):
        has_been_modified = self.current_md5 != self.initial_md5
        return has_been_modified


class IMergeTemplatesRowSchema(zope.interface.Interface):
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


class IConfigurablePODTemplate(IPODTemplate):
    """
    ConfigurablePODTemplate dexterity schema.
    """

    def pod_formats_constraint(value):
        """
        By default, it seems that 'required' is not correctly validated
        so we double check that the field is not empty...
        """
        if not value:
            raise zope.interface.Invalid(zope_message_factory(u"Required input is missing."))
        return True

    pod_formats = schema.List(
        title=_(u'Available formats'),
        description=_(u'Select format in which the template will be generable.'),
        value_type=schema.Choice(source='collective.documentgenerator.Formats'),
        required=True,
        default=['odt', ],
        constraint=pod_formats_constraint,
    )

    form.widget('pod_portal_types', SelectWidget, multiple='multiple', size=15)
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

    def set_merge_templates(self, pod_template, pod_context_name, position=-1):
        old_value = list(self.merge_templates)
        newline = {'template': pod_template.UID(), 'pod_context_name': pod_context_name}
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
                pod_context[line['pod_context_name'].encode('utf-8')] = pod_template

        return pod_context

    def get_available_formats(self):
        """
        Returns formats in which current template may be generated.
        """
        return self.pod_formats


class ISubTemplate(IPODTemplate):
    """
    PODTemplate used only a sub template to merge
    """


class SubTemplate(PODTemplate):
    """
    PODTemplate used only a sub template to merge
    """

    implements(ISubTemplate)
