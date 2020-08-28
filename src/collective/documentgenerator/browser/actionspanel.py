# -*- coding: utf-8 -*-
from imio.actionspanel.browser.views import ActionsPanelView


class ConfigurablePODTemplateActionsPanelView(ActionsPanelView):

    def __init__(self, context, request):
        super(ConfigurablePODTemplateActionsPanelView, self).__init__(context, request)

    def mayExtEdit(self):
        """
          Method that check if special 'external_edit' action has to be displayed.
        """
        if hasattr(self.context, 'pod_template_to_use'):
            if getattr(self.context, 'pod_template_to_use'):
                return False
        return super(ConfigurablePODTemplateActionsPanelView, self).mayExtEdit()
