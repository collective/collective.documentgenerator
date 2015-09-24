# -*- coding: utf-8 -*-
from zope.component import getMultiAdapter

from collective.documentgenerator.interfaces import IFieldRendererForDocument
from collective.documentgenerator.helper import DocumentGenerationHelperView
from collective.documentgenerator.helper import DisplayProxyObject


class ATDocumentGenerationHelperView(DocumentGenerationHelperView):
    """
    Archetypes implementation of document generation helper methods.
    """

    def display(self, field_name, context=None, no_value=''):
        if context is None:
            context = self.real_context

        if self.checkPermission(field_name, context):
            field_renderer = self.get_AT_field_renderer(field_name, context)
            display_value = field_renderer.render(no_value=no_value)
        else:
            display_value = u''

        return display_value

    def checkPermission(self, field_name, context):
        return context.getField(field_name).checkPermission('r', context)

    def get_AT_field_renderer(self, field_name, context):
        field = context.getField(field_name)
        widget = field.widget
        renderer = getMultiAdapter((field, widget, context), IFieldRendererForDocument)

        return renderer

    def display_date(self, field_name, context=None, long_format=None, time_only=None, custom_format=None):
        date_field = self.context.getField(field_name)
        date = date_field.get(self.context)
        if not custom_format:
            # use toLocalizedTime
            formatted_date = self.plone.toLocalizedTime(date, long_format, time_only)
        else:
            formatted_date = date.strftime(custom_format)

        return formatted_date

    def display_voc(self, field_name, context=None, separator=', '):
        if context is None:
            context = self.real_context

        display_value = context.restrictedTraverse('@@at_utils').translate

        field = context.getField(field_name)
        voc = field.Vocabulary(context)
        raw_values = field.get(context)
        values = [display_value(voc, val) for val in raw_values]
        display = separator.join(values)

        return display

    def display_text(self, field_name, context=None):
        if not self.appy_renderer:
            return

        if context is None:
            context = self.real_context

        html_field = self.context.getField(field_name)
        html_text = html_field.get(context)
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
