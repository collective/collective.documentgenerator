# -*- coding: utf-8 -*-

from collective.documentgenerator.helper.base import DisplayProxyObject
from collective.documentgenerator.helper.base import DocumentGenerationHelperView
from collective.documentgenerator.interfaces import IFieldRendererForDocument

from zope.component import getMultiAdapter


class ATDocumentGenerationHelperView(DocumentGenerationHelperView):
    """
    Archetypes implementation of document generation helper methods.
    """

    def display(self, field_name, no_value=''):
        if self.check_permission(field_name):
            field_renderer = self.get_AT_field_renderer(field_name)
            display_value = field_renderer.render(no_value=no_value)
        else:
            display_value = u''

        return display_value

    def check_permission(self, field_name):
        return bool(self.real_context.getField(field_name).checkPermission('r', self.real_context))

    def get_AT_field_renderer(self, field_name):
        field = self.real_context.getField(field_name)
        widget = field.widget
        renderer = getMultiAdapter((field, widget, self.real_context), IFieldRendererForDocument)

        return renderer

    def display_date(self, field_name, long_format=None, time_only=None, custom_format=None):
        date_field = self.real_context.getField(field_name)
        date = date_field.get(self.real_context)
        if not custom_format:
            # use toLocalizedTime
            formatted_date = self.plone.toLocalizedTime(date, long_format, time_only)
        else:
            formatted_date = date.strftime(custom_format)

        return formatted_date

    def display_voc(self, field_name, separator=', '):
        display_value = self.real_context.restrictedTraverse('@@at_utils').translate

        field = self.real_context.getField(field_name)
        voc = field.Vocabulary(self.real_context)
        raw_values = field.get(self.real_context)
        values = [display_value(voc, val) for val in raw_values]
        display = separator.join(values)

        return display

    def display_text(self, field_name):
        if not self.appy_renderer:
            return ''

        html_field = self.real_context.getField(field_name)
        html_text = html_field.get(self.real_context)
        display = self.appy_renderer.renderXhtml(html_text)
        return display

    def display_list(self, field_name, separator=', '):
        field = self.real_context.getField(field_name)
        values = field.get(self.real_context)
        display = separator.join(values)

        return display

    def list(self, field_name):
        field = self.real_context.getField(field_name)
        values = field.get(self.real_context)

        return values


class ATDisplayProxyObject(DisplayProxyObject):
    """
    Archetypes implementation of DisplayProxyObject.
    """

    def is_field(self, attr_name):
        is_field = bool(self.context.getField(attr_name))
        return is_field
