# -*- coding: utf-8 -*-

from collective.documentgenerator.helper import ATDocumentGenerationHelperView


class DemoHelperView(ATDocumentGenerationHelperView):
    """
    Archetypes implementation of document generation helper methods.
    """

    def get_default_CT_fields(self):
        field_list = []
        filtered_fields = ['id', 'title', 'sort_on', 'sort_reversed', 'b_size',
                           'limit', 'customViewFields']
        default_field_list = self.real_context.schema.getSchemataFields('default')
        for field in default_field_list:
            if field.getName() not in filtered_fields:
                field_list.append(field.getName())
        return field_list

    def is_rich_text_field(self, field_name):
        return self.real_context.schema.get(field_name).getWidgetName() == 'RichWidget'
