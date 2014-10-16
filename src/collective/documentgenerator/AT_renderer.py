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

    def render(self, no_value=''):
        if self.has_no_value():
            display_value = no_value
        else:
            display_value = self.render_value()

        return display_value

    def render_value(self):
        return self.field.get(self.context)

    def has_no_value(self):
        is_empty = not bool(self.field.get(self.context))
        return is_empty


class VocabularyATFieldRenderer(DefaultATFieldRenderer):
    """
    """

    def render_value(self):
        display_value = self.context.restrictedTraverse('@@at_utils').translate

        voc = self.field.Vocabulary(self.context)
        raw_values = self.field.get(self.context)
        values = [display_value(voc, val) for val in raw_values]
        display = ', '.join(values)

        return display


class DateATFieldRenderer(DefaultATFieldRenderer):
    """
    """

    def render_value(self):
        date = self.field.get(self.context)
        display = date.strftime('%d/%m/%Y %H:%M')

        return display
