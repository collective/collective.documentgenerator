# -*- coding: utf-8 -*-

from collective.documentgenerator.helper.base import DisplayProxyObject
from collective.documentgenerator.helper.base import DocumentGenerationHelperView
from collective.documentgenerator.interfaces import IFieldRendererForDocument
from zope.component import getMultiAdapter


class ATDocumentGenerationHelperView(DocumentGenerationHelperView):
    """
    Archetypes implementation of document generation helper methods.
    """

    def display(self, field_name, no_value='', bypass_check_permission=False):
        if bypass_check_permission or self.check_permission(field_name):
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
        renderer.helper_view = self

        return renderer

    def get_value(self, field_name, default=None, as_utf8=False):
        field = self.real_context.getField(field_name)
        value = field.getAccessor(self.real_context)()
        if value is None:
            return default
        if as_utf8 and isinstance(value, unicode):
            value = value.encode('utf8')
        return value

    def display_voc(self, field_name, separator=', '):
        display_value = self.real_context.restrictedTraverse('@@at_utils').translate

        field = self.real_context.getField(field_name)
        raw_values = field.getAccessor(self.real_context)()
        voc = field.Vocabulary(self.real_context)
        values = [display_value(voc, val) for val in raw_values]
        display = separator.join(values)

        return display

    def get_file_binary(self, file_obj):
        """ """
        data = file_obj.getPrimaryField().get(file_obj).data
        return data


class ATDisplayProxyObject(DisplayProxyObject):
    """
    Archetypes implementation of DisplayProxyObject.
    """

    def is_field(self, attr_name):
        is_field = bool(self.context.getField(attr_name))
        return is_field
