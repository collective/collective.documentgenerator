# coding=utf-8
from collective.documentgenerator.search_replace.pod_template import SearchAndReplacePODTemplates
from collective.documentgenerator.testing import PODTemplateIntegrationTest
from collective.documentgenerator.utils import compute_md5
from plone.testing._z2_testbrowser import Browser
from zExceptions import Unauthorized
from zope.interface import Invalid

import io
import os
import zipfile


class TestSearchReplaceTemplate(PODTemplateIntegrationTest):
    """
    Test search and replace feature
    """

    def setUp(self):
        super(TestSearchReplaceTemplate, self).setUp()
        self.template1 = self.portal.podtemplates.test_template
        self.template2 = self.portal.podtemplates.test_template_bis

    def test_podtemplate_is_searchable(self):
        with SearchAndReplacePODTemplates((self.template1, self.template2)) as search_replace:
            results = search_replace.search("view")

        self.assertGreater(len(results.keys()), 0)

    def test_search_dont_alter_podtemplate(self):
        template1_md5 = compute_md5(self.template1.odt_file.data)
        template2_md5 = compute_md5(self.template2.odt_file.data)

        with SearchAndReplacePODTemplates((self.template1, self.template2)) as search_replace:
            search_replace.search("view")

        self.assertEqual(compute_md5(self.template1.odt_file.data), template1_md5)
        self.assertEqual(compute_md5(self.template2.odt_file.data), template2_md5)

    def test_can_search_regex(self):
        with SearchAndReplacePODTemplates((self.template1, self.template2)) as search_replace:
            # We want only the `view` before the `get_localized_field_name` method
            results = search_replace.search("view(?=.get_localized_field_name)", is_regex=True)

        template1_results = results[self.template1.UID()]
        self.assertEqual(len(template1_results), 1)
        self.assertNotIn(self.template2.UID(), results.keys())  # Nothing in template2

        self.assertIn("view.get_localized_field_name", template1_results[0].pod_expr)
        self.assertEqual("view", template1_results[0].match)

    def test_can_search_string(self):
        with SearchAndReplacePODTemplates((self.template1, self.template2)) as search_replace:
            results = search_replace.search("Author")

        self.assertNotIn(self.template1.UID(), results.keys())
        template2_results = results[self.template2.UID()]
        self.assertEqual(len(template2_results), 1)

        self.assertEqual("Author", template2_results[0].match)
        self.assertIn("Author", template2_results[0].pod_expr)

    def test_can_search_in_headers_and_footers(self):
        with SearchAndReplacePODTemplates((self.template1, self.template2)) as search_replace:
            header_results = search_replace.search("context.title.upper()")
            footer_results = search_replace.search("^view.display_date", is_regex=True)

        self.assertNotIn(self.template1.UID(), header_results.keys())
        self.assertNotIn(self.template1.UID(), footer_results.keys())

        self.assertEqual(len(header_results[self.template2.UID()]), 1)
        self.assertEqual("context.title.upper()", header_results[self.template2.UID()][0].match)

        self.assertEqual(len(footer_results[self.template2.UID()]), 1)
        self.assertEqual("view.display_date", footer_results[self.template2.UID()][0].match)

    def test_can_search_multiple_times(self):
        with SearchAndReplacePODTemplates((self.template1,)) as search_replace:
            not_found_results = search_replace.search("No where to be found")
            view_results = search_replace.search("view")
            regex_results = search_replace.search("view(?=.get_localized_field_name)", is_regex=True)

        template1_uid = self.template1.UID()

        self.assertNotEqual(not_found_results, view_results)
        self.assertNotEqual(view_results, regex_results)

        self.assertNotIn(template1_uid, not_found_results)

        for result in view_results[template1_uid]:
            self.assertIn("view", result.pod_expr)
            self.assertEqual("view", result.match)

        self.assertEqual(len(regex_results[template1_uid]), 1)
        self.assertIn("view.get_localized_field_name", regex_results[template1_uid][0].pod_expr)
        self.assertEqual("view", regex_results[self.template1.UID()][0].match)

    def test_search_clean_after_itself(self):
        tmp_files_count = len(os.listdir("/tmp/docgen"))
        with SearchAndReplacePODTemplates((self.template1, self.template2)) as search_replace:
            search_replace.search("view")

        self.assertTrue(len(os.listdir("/tmp/docgen")) == tmp_files_count)

        # Test if it clean after itself after an exception is raised
        try:
            with SearchAndReplacePODTemplates((self.template1, self.template2)) as search_replace:
                search_replace.search("view")
                raise OSError
        except OSError:
            pass

        self.assertEqual(len(os.listdir("/tmp/docgen")), tmp_files_count)

    def test_can_replace_in_podtemplate(self):
        with SearchAndReplacePODTemplates((self.template1, self.template2)) as search_replace:
            results = search_replace.replace("view", "View")

        self.assertGreater(len(results), 0)

    def test_replace_change_podtemplate_file(self):
        template1_md5 = compute_md5(self.template1.odt_file.data)
        template2_md5 = compute_md5(self.template2.odt_file.data)

        with SearchAndReplacePODTemplates((self.template1, self.template2)) as search_replace:
            search_replace.replace("view", "View")

        self.assertNotEquals(compute_md5(self.template1.odt_file.data), template1_md5)
        self.assertNotEquals(compute_md5(self.template2.odt_file.data), template2_md5)

    def test_replace_dont_alter_pod_template_odt_file_structure(self):
        with SearchAndReplacePODTemplates((self.template1,)) as search_replace:
            search_replace.replace("view", "View")

        zip_bytes = io.BytesIO(self.template1.odt_file.data)
        zip_file = zipfile.ZipFile(zip_bytes)
        odt_subfiles = zip_file.namelist()

        expected_files = [
            u"mimetype",
            u"content.xml",
            u"styles.xml",
            u"meta.xml",
            u"settings.xml",
            u"manifest.rdf",
            u"META-INF/manifest.xml",
        ]

        for expected_file in expected_files:
            self.assertIn(expected_file, odt_subfiles)

    def test_replace_dont_change_podtemplate_file_size_too_much(self):
        template1_filesize = self.template1.odt_file.getSize()
        template2_filesize = self.template2.odt_file.getSize()

        with SearchAndReplacePODTemplates((self.template1, self.template2)) as search_replace:
            search_replace.replace("view", "View")

        self.assertAlmostEqual(template1_filesize, self.template1.odt_file.getSize(), delta=500)
        self.assertAlmostEqual(template2_filesize, self.template2.odt_file.getSize(), delta=500)

    def test_can_replace_string(self):
        with SearchAndReplacePODTemplates((self.template1, self.template2)) as search_replace:
            results = search_replace.replace("Author", "Writer")

        self.assertTrue(self.template1.UID() not in results.keys())
        template2_results = results[self.template2.UID()]
        self.assertEqual(len(template2_results), 1)

        self.assertEqual("Author", template2_results[0].match)
        self.assertIn("Author", template2_results[0].pod_expr)
        self.assertNotIn("Author", template2_results[0].new_pod_expr)
        self.assertIn("Writer", template2_results[0].new_pod_expr)

        # Verification with search
        with SearchAndReplacePODTemplates((self.template2,)) as search_replace:
            writer_search = search_replace.search("Writer")
            author_search = search_replace.search("Author")

        template2_writer_search = writer_search[self.template2.UID()]
        self.assertGreater(len(template2_writer_search), 0)

        self.assertNotIn(self.template2.UID(), author_search.keys())

    def test_can_replace_regex(self):
        with SearchAndReplacePODTemplates((self.template1, self.template2)) as search_replace:
            # We want only the `view` before the `get_localized_field_name` method
            results = search_replace.replace("view(?=.get_localized_field_name)", "NewView", is_regex=True)

        template1_results = results[self.template1.UID()]
        self.assertEqual(len(template1_results), 1)
        self.assertNotIn(self.template2.UID(), results.keys())  # Nothing in template2

        self.assertIn("view.get_localized_field_name", template1_results[0].pod_expr)
        self.assertNotIn("view.get_localized_field_name", template1_results[0].new_pod_expr)
        self.assertEqual("view", template1_results[0].match)

        # Verification with search
        with SearchAndReplacePODTemplates((self.template1,)) as search_replace:
            results = search_replace.search("NewView")

        result = results[self.template1.UID()]
        self.assertGreater(len(result), 0)
        self.assertEqual("NewView", result[0].match)
        self.assertIn("NewView", result[0].pod_expr)

    def test_can_replace_multiple_times(self):
        with SearchAndReplacePODTemplates((self.template2,)) as search_replace:
            search_replace.replace("Author", "Writer")
            search_replace.replace("Writer", u"Écrivain")
            results = search_replace.replace(u"Écrivain", "Schrijver")

        template2_results = results[self.template2.UID()]
        self.assertEqual(len(template2_results), 1)

        self.assertIn("Schrijver", template2_results[0].new_pod_expr)
        self.assertNotIn("Author", template2_results[0].new_pod_expr)

        # Verification with search
        with SearchAndReplacePODTemplates((self.template2,)) as search_replace:
            results = search_replace.search("Schrijver")

        template2_results = results[self.template2.UID()]
        self.assertEqual(len(template2_results), 1)
        self.assertEqual("Schrijver", template2_results[0].match)
        self.assertIn("Schrijver", template2_results[0].pod_expr)

    def test_replace_clean_after_itself(self):
        tmp_files_count = len(os.listdir("/tmp/docgen"))
        with SearchAndReplacePODTemplates((self.template1, self.template2)) as search_replace:
            search_replace.replace("View", "view")

        self.assertEqual(len(os.listdir("/tmp/docgen")), tmp_files_count)

        # Test if it clean after itself after an exception is raised
        try:
            with SearchAndReplacePODTemplates((self.template1, self.template2)) as search_replace:
                search_replace.replace("View", "view")
                raise OSError
        except OSError:
            pass

        self.assertEqual(len(os.listdir("/tmp/docgen")), tmp_files_count)

    def test_replace_can_replace_in_headers_and_footers(self):
        with SearchAndReplacePODTemplates((self.template1, self.template2)) as search_replace:
            header_results = search_replace.replace("context.title.upper()", "context.title.lower()")
            footer_results = search_replace.replace("^view.display_date", "view.new_method", is_regex=True)

        self.assertNotIn(self.template1.UID(), header_results.keys())
        self.assertNotIn(self.template1.UID(), footer_results.keys())

        self.assertIn("context.title.lower()", header_results[self.template2.UID()][0].new_pod_expr)
        self.assertIn("view.new_method(", footer_results[self.template2.UID()][0].new_pod_expr)

        # Verification with search
        with SearchAndReplacePODTemplates((self.template2,)) as search_replace:
            header_results = search_replace.search("context.title.lower()")
            footer_results = search_replace.search("view.new_method(")

        self.assertGreater(len(header_results), 0)
        self.assertEqual("context.title.lower()", header_results[self.template2.UID()][0].match)

        self.assertGreater(len(footer_results), 0)
        self.assertEqual("view.new_method(", footer_results[self.template2.UID()][0].match)

    def test_podtemplate_is_still_functional_after_search_replace(self):
        with SearchAndReplacePODTemplates((self.template2,)) as search_replace:
            search_replace.replace("context.description", "context.title")
            search_replace.search("context.description")

        template_uid = self.template2.UID()
        view = self.portal.podtemplates.restrictedTraverse("@@document-generation")
        self.assertIn("pdf", self.template2.get_available_formats())
        generated_doc = view(template_uid, "pdf")
        self.assertEqual("%PDF", generated_doc[:4])

    def test_search_replace_control_panel_anonymous_unauthorized(self):
        app = self.layer["app"]
        browser = Browser(app)
        browser.handleErrors = False
        with self.assertRaises(Unauthorized):  # Anonymous cannot access this page
            browser.open("{}/@@collective.documentgenerator-searchreplacepanel".format(self.portal.absolute_url()))

    def test_search_replace_control_panel_doesnt_fail(self):
        # self.browser is logged in as admin
        self.browser.handleErrors = False
        self.browser.open(
            "{}/@@collective.documentgenerator-searchreplacepanel".format(self.portal.absolute_url())
        )

    def test_search_replace_control_panel_can_preview(self):
        view = self.portal.restrictedTraverse("@@collective.documentgenerator-searchreplacepanel")
        selected_templates_mock = [self.template1.UID(), self.template2.UID()]
        replacements_mock = [
            {"search_expr": "^view.display_date", "replace_expr": "view.display_new_date", "is_regex": True},
            {"search_expr": "Author", "replace_expr": "Writer", "is_regex": False},
        ]
        form_data = {"selected_templates": selected_templates_mock, "replacements": replacements_mock}

        view.form_instance.perform_preview(form_data)
        view()

    def test_search_replace_control_panel_can_replace(self):
        view = self.portal.restrictedTraverse("@@collective.documentgenerator-searchreplacepanel")
        selected_templates_mock = [self.template1.UID(), self.template2.UID()]
        replacements_mock = [
            {"search_expr": "^view.display_date", "replace_expr": "view.display_new_date", "is_regex": True},
            {"search_expr": "Author", "replace_expr": "Writer", "is_regex": False},
        ]
        form_data = {"selected_templates": selected_templates_mock, "replacements": replacements_mock}

        view.form_instance.perform_replacements(form_data)
        view()

    def test_search_replace_control_panel_regex_validator(self):
        view = self.portal.restrictedTraverse("@@collective.documentgenerator-searchreplacepanel")
        form = view.form_instance
        form.update()
        selected_templates = [self.template1.UID(), self.template2.UID()]
        replacements = [
            {"search_expr": "get_elements(", "replace_expr": "", "is_regex": False},
            {"search_expr": "get_elements(", "replace_expr": "", "is_regex": True},
        ]
        data = {'replacements': replacements,
                'selected_templates': selected_templates}
        errors = form.widgets.validate(data)
        self.assertEqual(len(errors), 1)
        self.assertTrue(isinstance(errors[0], Invalid))
        self.assertEqual(errors[0].message, u'Incorrect regex at row #2 : "get_elements("')
        replacements = [
            {"search_expr": "get_elements(", "replace_expr": "", "is_regex": False},
            {"search_expr": "valid_regex?", "replace_expr": "", "is_regex": True},
        ]
        data = {'replacements': replacements}
        errors = form.widgets.validate(data)
        self.assertFalse(errors)
