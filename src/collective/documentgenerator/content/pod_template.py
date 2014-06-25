# -*- coding: utf-8 -*-

from plone.dexterity.content import Item
from plone.supermodel import model

from zope.interface import implements


class IPODTemplate(model.Schema):
    """
    PODTemplate dexterity schema.
    """


class PODTemplate(Item):
    """
    PODTemplate dexterity class.
    """

    implements(IPODTemplate)
