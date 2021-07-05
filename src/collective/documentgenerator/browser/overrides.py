# -*- coding: utf-8 -*-

from collective.documentgenerator.browser.views import ViewConfigurablePodTemplate
from collective.documentviewer.views import DXDocumentViewerView


class DGDXDocumentViewerView(ViewConfigurablePodTemplate, DXDocumentViewerView):
    """The documentviewer view from collective.documentviewer overrides the default DX
       view, so override it again so our own override is taken into account."""
