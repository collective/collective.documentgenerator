# -*- coding: utf-8 -*-

from Products.CMFCore.Expression import Expression
from Products.CMFCore.utils import _checkPermission
from Products.PageTemplates.Expressions import getEngine

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

    form.omitted('condition_adapter')
    condition_adapter = schema.TextLine(
        default=u'default-generation-condition',
    )

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
        condition_obj = queryMultiAdapter((self, context), IPODTemplateCondition, self.condition_adapter)
        if condition_obj:
            can_be_generated = condition_obj.evaluate()
            return can_be_generated
        return True


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

    pod_expression = schema.TextLine(
        title=_(u'TAL expression'),
        description=_(u'pod_condition'),
        required=False,
    )

    enabled = schema.Bool(
        title=_(u'Enabled'),
        default=True,
        required=False,
    )


class ConfigurablePODTemplate(PODTemplate):
    """
    ConfigurablePODTemplate dexterity class.
    """

    implements(IConfigurablePODTemplate)

    def can_be_generated(self, context, TAL_context=None):
        """
        Check the permission and the  TAL expression of a PODTemplate
        on a context.
        """
        if not TAL_context:
            TAL_context = {'here': context, 'object': context, 'context': context, 'self': context}

        is_good_pt = self.check_pod_good_pt(context)
        can_generate = self.evaluate_pod_condition(TAL_context)

        return self.enabled and is_good_pt and can_generate

    def check_pod_good_pt(self, context):
        """
        Evaluate if context is in pt selected list
        If not use, return True
        """
        return (not self.pod_portal_type) or (context.portal_type in self.pod_portal_type)

    def evaluate_pod_condition(self, TAL_context=None):
        """
        Evaluate the TAL expression of pod_condition field.
        """
        if not TAL_context:
            TAL_context = {}

        result = True  # At least for now

        TAL_condition = self.pod_expression

        if TAL_condition:
            TAL_condition = TAL_condition.strip()
            TAL_context = getEngine().getContext(TAL_context)
            result = Expression(TAL_condition)(TAL_context)

        return result
