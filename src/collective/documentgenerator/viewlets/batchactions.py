# -*- coding: utf-8 -*-

try:
    from collective.eeafaceted.batchactions.browser.viewlets import BatchActionsViewlet
except ImportError:
    from plone.app.layout.viewlets import ViewletBase as BatchActionsViewlet


class DGBatchActionsViewlet(BatchActionsViewlet):
    ''' '''

    def available(self):
        """Global availability of the viewlet."""
        return self.view.__name__ == 'dg-templates-listing'
