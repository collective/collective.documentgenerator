# -*- coding: utf-8 -*-

from collective.documentgenerator.interfaces import IFieldRendererForDocument
from zope.interface import implementer


@implementer(IFieldRendererForDocument)
class DefaultATFieldRenderer(object):
    """
    """

    def __init__(self, field, widget, context):
        self.field = field
        self.widget = widget
        self.context = context
        self.helper_view = None

    def render(self, no_value=''):
        if self.has_no_value():
            display_value = no_value
        else:
            display_value = self.render_value()

        return display_value

    def render_value(self):
        """
        Compute the rendering of the display value.
        To override for each different type of ATFieldRenderer.
        """
        return self.field.getAccessor(self.context)()

    def has_no_value(self):
        is_empty = not bool(self.field.getAccessor(self.context)())
        return is_empty


class VocabularyATFieldRenderer(DefaultATFieldRenderer):
    """
    """

    def render_value(self):
        display_value = self.context.unrestrictedTraverse('@@at_utils').translate

        voc = self.field.Vocabulary(self.context)
        raw_values = self.field.getAccessor(self.context)()
        if type(raw_values) not in [list, tuple]:
            raw_values = [raw_values]
        values = [display_value(voc, val) for val in raw_values]
        display = ', '.join(values)

        return display


class DateATFieldRenderer(DefaultATFieldRenderer):
    """
    """

    def render_value(self):
        date = self.field.getAccessor(self.context)()
        display = date.strftime('%d/%m/%Y %H:%M')

        return display


class RichTextATFieldRenderer(DefaultATFieldRenderer):
    """
    """

    def render_value(self):
        display = self.helper_view.render_xhtml(self.field.getName())
        return display


class LinesATFieldRenderer(DefaultATFieldRenderer):
    """
    """

    def render_value(self):
        msg = "!!! the field '{field_name}' is a lines field, use 'view.display_list('{field_name}')' \
              to display all elements on one line or  use 'do text for val in view.list('{field_name}')'\
              in a commentary to render each evalue line by line!!!'".format(
            field_name=self.field.getName()
        )
        return msg


class QueryATFieldRenderer(DefaultATFieldRenderer):
    """
    """

    def render_value(self):
        msg = "!!! the field '{field_name}' is a query field returning catalog brains, use \
              'do text for brain in view.list('{field_name}')' in a commentary to iterate \
              over the query result. !!!'".format(
            field_name=self.field.getName()
        )
        return msg
