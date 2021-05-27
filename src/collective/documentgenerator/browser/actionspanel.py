# -*- coding: utf-8 -*-
from Products.CMFPlone.utils import base_hasattr


try:
    from imio.actionspanel.browser.views import ActionsPanelView

    class ConfigurablePODTemplateActionsPanelView(ActionsPanelView):

        def mayExtEdit(self):
            """
              Method that check if special 'external_edit' action has to be displayed.
            """
            if base_hasattr(self.context, 'pod_template_to_use'):
                if getattr(self.context, 'pod_template_to_use'):
                    return False
            return super(ConfigurablePODTemplateActionsPanelView, self).mayExtEdit()
except ImportError:
    pass
