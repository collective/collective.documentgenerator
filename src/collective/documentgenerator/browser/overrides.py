# -*- coding: utf-8 -*-

from collective.documentgenerator.browser.views import ViewConfigurablePodTemplate
from collective.documentviewer.browser.views import DocumentViewerView


class DGDXDocumentViewerView(ViewConfigurablePodTemplate, DocumentViewerView):
    """The documentviewer view from collective.documentviewer overrides the default DX
       view, so override it again so our own override is taken into account."""
