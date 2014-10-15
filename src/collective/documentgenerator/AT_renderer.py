# -*- coding: utf-8 -*-

from collective.documentgenerator.interfaces import IFieldRendererForDocument

from zope.interface import implements


class DefaultATFieldRenderer(object):
    """
    """
    implements(IFieldRendererForDocument)

    def __init__(self, field, widget, context):
        self.field = field
        self.widget = widget
        self.context = context

    def render(self):
        return self.field.get(self.context)


class VocabularyATFieldRenderer(DefaultATFieldRenderer):
    """
    """

    def render(self):
        display_value = self.context.restrictedTraverse('@@at_utils').translate

        voc = self.field.Vocabulary(self.context)
        raw_values = self.field.get(self.context)
        values = [display_value(voc, val) for val in raw_values]
        display = ', '.join(values)

        return display
