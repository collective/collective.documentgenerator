# -*- coding: utf-8 -*-

from plone.dexterity.content import Item
from plone.supermodel import model

from zope.interface import implements


class IODTTemplate(model.Schema):
    """
    ODTTemplate dexterity schema.
    """


class ODTTemplate(Item):
    """
    ODTTemplate dexterity class.
    """

    implements(IODTTemplate)
