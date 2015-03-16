# -*- coding: utf-8 -*-

from collective.documentgenerator import _

from plone.autoform import directives as form
from plone.dexterity.content import Item
from plone.formwidget.namedfile import NamedFileWidget
from plone.namedfile.field import NamedBlobFile
from plone.supermodel import model

from zope.interface import implements


import logging
logger = logging.getLogger('collective.documentgenerator: StyleTemplate')


class IStyleTemplate(model.Schema):
    """
    StyleTemplate dexterity schema.
    """

    model.primary('odt_file')
    form.widget('odt_file', NamedFileWidget)
    odt_file = NamedBlobFile(
        title=_(u'ODT File'),
    )


class StyleTemplate(Item):
    """
    StyleTemplate dexterity class.
    """

    implements(IStyleTemplate)
