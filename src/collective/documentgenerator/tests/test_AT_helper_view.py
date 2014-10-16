# -*- coding: utf-8 -*-

from collective.documentgenerator.testing import ArchetypesBaseTests

from zope.component import queryAdapter


class TestArchetypesHelperView(ArchetypesBaseTests):
    """
    Test Archetypes helper view.
    """

    def test_AT_helper_view_registration(self):
        """
        Test that when we query a IDocumentGenerationHelper adpater on an AT object, we get
        the AT implementation of DocumentGenerationHelperView.
        """
        from collective.documentgenerator.interfaces import IDocumentGenerationHelper
        from collective.documentgenerator.helper import ATDocumentGenerationHelperView

        helper_view = queryAdapter(self.AT_topic, IDocumentGenerationHelper)
        msg = "The helper object should have been an instance of ATDocumentGenerationHelperView"
        self.assertTrue(isinstance(helper_view, ATDocumentGenerationHelperView), msg)
