# -*- coding: utf-8 -*-

from collective.documentgenerator import _
from collective.documentgenerator.utils import compute_md5
from plone.autoform import directives as form
from plone.dexterity.content import Item
from plone.formwidget.namedfile import NamedFileWidget
from plone.namedfile.field import NamedBlobFile
from plone.supermodel import model
from Products.CMFPlone.utils import safe_unicode
from zope import schema
from zope.interface import implementer

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

    form.omitted('initial_md5')
    initial_md5 = schema.TextLine(description=u'Initially loaded file md5. Will be compared with os file md5.')


@implementer(IStyleTemplate)
class StyleTemplate(Item):
    """
    StyleTemplate dexterity class.
    """

    @property
    def current_md5(self):
        md5 = u''
        if self.odt_file:
            md5 = safe_unicode(compute_md5(self.odt_file.data))
        return md5

    def has_been_modified(self):
        """
            Current md5 will be different from initial_md5 if user modification.
        """
        return self.current_md5 != self.initial_md5
