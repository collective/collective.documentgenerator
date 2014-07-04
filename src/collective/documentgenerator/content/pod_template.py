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

    pod_permission = schema.Choice(
        title=_(u'Permission'),
        vocabulary='collective.documentgenerator.Permissions',
        default='View',
        required=False,
    )

    pod_expression = schema.TextLine(
        title=_(u'TAL expression'),
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

    def get_file(self):
        return self.odt_file

    def can_be_generated(self, context, TAL_context=None):
        """
        Check the permission and the  TAL expression of a PODTemplate
        on a context.
        """
        if not TAL_context:
            TAL_context = {'here': context, 'object': context, 'context': context, 'self': context}

        has_permission = self.check_pod_permission(context)
        can_generate = self.evaluate_pod_condition(TAL_context)

        return self.enabled and has_permission and can_generate

    def check_pod_permission(self, context):
        return _checkPermission(self.pod_permission, context)

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
