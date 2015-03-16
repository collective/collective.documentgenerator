# -*- coding: utf-8 -*-

from collective.documentgenerator import _
from collective.documentgenerator.interfaces import IPODTemplateCondition

from plone.autoform import directives as form
from plone.dexterity.content import Item
from plone.formwidget.namedfile import NamedFileWidget
from plone.namedfile.field import NamedBlobFile
from plone.supermodel import model

from zope import schema
from zope.component import queryMultiAdapter
from zope.interface import implements

from z3c.form.browser.select import SelectWidget

import logging
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

    def get_StylesPODTemplate(self):
        """
        Return associated StylesPODTemplate from which styles will be imported
        to the current PODTemplate.
        """


class IConfigurablePODTemplate(IPODTemplate):
    """
    ConfigurablePODTemplate dexterity schema.
    """

    form.widget('pod_portal_type', SelectWidget, multiple='multiple', size=15)
    pod_portal_type = schema.List(
        title=_(u'Allowed portal types'),
        description=_(u'pod_portal_type'),
        value_type=schema.Choice(source='collective.documentgenerator.PortalType'),
        required=False,
    )

    enabled = schema.Bool(
        title=_(u'Enabled'),
        default=True,
        required=False,
    )

    form.widget('style', SelectWidget)
    style = schema.List(
        title=_(u'Style template'),
        description=_(u'style_template_descr'),
        value_type=schema.Choice(source='collective.documentgenerator.StyleTemplates'),
        required=True,
    )


class ConfigurablePODTemplate(PODTemplate):
    """
    ConfigurablePODTemplate dexterity class.
    """

    implements(IConfigurablePODTemplate)
