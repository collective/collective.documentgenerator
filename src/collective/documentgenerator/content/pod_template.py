# -*- coding: utf-8 -*-

from Products.CMFCore.Expression import Expression
from Products.PageTemplates.Expressions import getEngine

from collective.documentgenerator import _

from plone.autoform import directives as form
from plone.dexterity.content import Item
from plone.formwidget.namedfile import NamedFileWidget
from plone.namedfile.field import NamedBlobFile
from plone.supermodel import model

from zope import schema
from zope.interface import implements
from zope.security import checkPermission

import logging
logger = logging.getLogger('collective.documentgenerator: PODTemplate')


class IPODTemplate(model.Schema):
    """
    PODTemplate dexterity schema.
    """

    form.widget('odt_file', NamedFileWidget)
    odt_file = NamedBlobFile(
        title=_(u'ODT File'),
    )

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


class PODTemplate(Item):
    """
    PODTemplate dexterity class.
    """

    implements(IPODTemplate)

    def get_file(self):
        return self.odt_file

    def can_be_generated(self, context, TAL_context=None):
        """
        Check the permission and the  TAL expression of a PODTemplate
        on a context.
        """
        if not TAL_context:
            TAL_context = {}

        has_permission = checkPermission(self.pod_permission, context)
        can_generate = self.evaluate_pod_condition(context, TAL_context)

        return has_permission and can_generate

    def evaluate_pod_condition(self, obj, TAL_context):
        """
        Evaluate the TAL expression of pod_condition field.
        """
        result = True  # At least for now

        TAL_condition = self.pod_condition.strip()
        if TAL_condition:
            TAL_context = getEngine().getContext(TAL_context)
            result = Expression(TAL_condition)(TAL_context)

        return result
