# coding=utf-8
import io
import os
import zipfile

from collective.documentgenerator.testing import PODTemplateIntegrationTest
from collective.documentgenerator.search_replace.pod_template import SearchAndReplacePODTemplates
from collective.documentgenerator.utils import compute_md5


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
            results = search_replace.search("view", is_regex=False)

        self.assertTrue(len(results.keys()) > 0)

    def test_search_dont_alter_podtemplate(self):
        template1_md5 = compute_md5(self.template1.odt_file.data)
        template2_md5 = compute_md5(self.template2.odt_file.data)

        with SearchAndReplacePODTemplates((self.template1, self.template2)) as search_replace:
            search_replace.search("view", is_regex=False)

        self.assertEqual(compute_md5(self.template1.odt_file.data), template1_md5)
        self.assertEqual(compute_md5(self.template2.odt_file.data), template2_md5)

    def test_can_search_regex(self):
        with SearchAndReplacePODTemplates((self.template1, self.template2)) as search_replace:
            # We want only the `view` before the `get_localized_field_name` method
            results = search_replace.search("view(?=\.get_localized_field_name)")

        template1_results = results[self.template1.UID()]
        self.assertTrue(len(template1_results) == 1)
        self.assertTrue(self.template2.UID() not in results.keys())  # Nothing in template2

        self.assertIn("view.get_localized_field_name", template1_results[0].pod_expr)
        self.assertEqual("view", template1_results[0].match)

    def test_can_search_string(self):
        with SearchAndReplacePODTemplates((self.template1, self.template2)) as search_replace:
            results = search_replace.search("Author")

        self.assertTrue(self.template1.UID() not in results.keys())
        template2_results = results[self.template2.UID()]
        self.assertTrue(len(template2_results) == 1)

        self.assertEqual("Author", template2_results[0].match)
        self.assertIn("Author", template2_results[0].pod_expr)

    def test_can_search_multiple_times(self):
        with SearchAndReplacePODTemplates((self.template1,)) as search_replace:
            not_found_results = search_replace.search("No where to be found", is_regex=False)
            view_results = search_replace.search("view", is_regex=False)
            regex_results = search_replace.search("view(?=.get_localized_field_name)")

        template1_uid = self.template1.UID()

        self.assertNotEqual(not_found_results, view_results)
        self.assertNotEqual(view_results, regex_results)

        self.assertNotIn(template1_uid, not_found_results)

        for result in view_results[template1_uid]:
            self.assertIn("view", result.pod_expr)
            self.assertEqual("view", result.match)

        self.assertTrue(len(regex_results[template1_uid]) == 1)
        self.assertIn("view.get_localized_field_name", regex_results[template1_uid][0].pod_expr)
        self.assertEqual("view", regex_results[self.template1.UID()][0].match)

    def test_search_clean_after_itself(self):
        tmp_files_count = len(os.listdir("/tmp/docgen"))
        with SearchAndReplacePODTemplates((self.template1, self.template2)) as search_replace:
            search_replace.search("view", is_regex=False)

        self.assertTrue(len(os.listdir("/tmp/docgen")) == tmp_files_count)

        # Test if it clean after itself after an exception is raised
        try:
            with SearchAndReplacePODTemplates((self.template1, self.template2)) as search_replace:
                result = search_replace.search("view", is_regex=False)
                raise OSError
        except OSError:
            pass

        self.assertTrue(len(os.listdir("/tmp/docgen")) == tmp_files_count)

    def test_can_replace_in_podtemplate(self):
        with SearchAndReplacePODTemplates((self.template1, self.template2)) as search_replace:
            results = search_replace.replace("view", "View", is_regex=False)

        self.assertTrue(len(results) > 0)

    def test_replace_change_podtemplate_file(self):
        template1_md5 = compute_md5(self.template1.odt_file.data)
        template2_md5 = compute_md5(self.template2.odt_file.data)

        with SearchAndReplacePODTemplates((self.template1, self.template2)) as search_replace:
            search_replace.replace("view", "View", is_regex=False)

        self.assertNotEquals(compute_md5(self.template1.odt_file.data), template1_md5)
        self.assertNotEquals(compute_md5(self.template2.odt_file.data), template2_md5)

    def test_replace_dont_alter_pod_template_odt_file_structure(self):
        with SearchAndReplacePODTemplates((self.template1,)) as search_replace:
            search_replace.replace("view", "View", is_regex=False)

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
            search_replace.replace("view", "View", is_regex=False)

        self.assertAlmostEqual(template1_filesize, self.template1.odt_file.getSize(), delta=500)
        self.assertAlmostEqual(template2_filesize, self.template2.odt_file.getSize(), delta=500)

    def test_can_replace_string(self):
        with SearchAndReplacePODTemplates((self.template1, self.template2)) as search_replace:
            results = search_replace.replace("Author", "Writer", is_regex=False)

        self.assertTrue(self.template1.UID() not in results.keys())
        template2_results = results[self.template2.UID()]
        self.assertTrue(len(template2_results) == 1)

        self.assertEqual("Author", template2_results[0].match)
        self.assertIn("Author", template2_results[0].pod_expr)
        self.assertNotIn("Author", template2_results[0].new_pod_expr)
        self.assertIn("Writer", template2_results[0].new_pod_expr)

        # Verification with search
        with SearchAndReplacePODTemplates((self.template2,)) as search_replace:
            writer_search = search_replace.search("Writer")
            author_search = search_replace.search("Author")

        template2_writer_search = writer_search[self.template2.UID()]
        self.assertTrue(len(template2_writer_search) > 0)

        self.assertNotIn(self.template2.UID(), author_search.keys())

    def test_can_replace_regex(self):
        with SearchAndReplacePODTemplates((self.template1, self.template2)) as search_replace:
            # We want only the `view` before the `get_localized_field_name` method
            results = search_replace.replace("view(?=.get_localized_field_name)", "NewView")

        template1_results = results[self.template1.UID()]
        self.assertTrue(len(template1_results) == 1)
        self.assertTrue(self.template2.UID() not in results.keys())  # Nothing in template2

        self.assertIn("view.get_localized_field_name", template1_results[0].pod_expr)
        self.assertNotIn("view.get_localized_field_name", template1_results[0].new_pod_expr)
        self.assertEqual("view", template1_results[0].match)

        # Verification with search
        with SearchAndReplacePODTemplates((self.template1,)) as search_replace:
            results = search_replace.search("NewView")

        result = results[self.template1.UID()]
        self.assertTrue(len(result) > 0)
        self.assertEqual("NewView", result[0].match)
        self.assertIn("NewView", result[0].pod_expr)

    def test_can_replace_multiple_times(self):
        with SearchAndReplacePODTemplates((self.template2,)) as search_replace:
            search_replace.replace("Author", "Writer", is_regex=False)
            search_replace.replace("Writer", u"Écrivain", is_regex=False)
            results = search_replace.replace(u"Écrivain", "Schrijver", is_regex=False)

        template2_results = results[self.template2.UID()]
        self.assertTrue(len(template2_results) == 1)

        self.assertIn("Schrijver", template2_results[0].new_pod_expr)
        self.assertNotIn("Author", template2_results[0].new_pod_expr)

        # Verification with search
        with SearchAndReplacePODTemplates((self.template2,)) as search_replace:
            results = search_replace.search("Schrijver")

        template2_results = results[self.template2.UID()]
        self.assertTrue(len(template2_results) == 1)
        self.assertEqual("Schrijver", template2_results[0].match)
        self.assertIn("Schrijver", template2_results[0].pod_expr)

    def test_replace_clean_after_itself(self):
        tmp_files_count = len(os.listdir("/tmp/docgen"))
        with SearchAndReplacePODTemplates((self.template1, self.template2)) as search_replace:
            search_replace.replace("View", "view", is_regex=False)

        self.assertTrue(len(os.listdir("/tmp/docgen")) == tmp_files_count)

        # Test if it clean after itself after an exception is raised
        try:
            with SearchAndReplacePODTemplates((self.template1, self.template2)) as search_replace:
                search_replace.replace("View", "view", is_regex=False)
                raise OSError
        except OSError:
            pass

        self.assertTrue(len(os.listdir("/tmp/docgen")) == tmp_files_count)

    def test_podtemplate_is_still_functional_after_search_replace(self):
        with SearchAndReplacePODTemplates((self.template2,)) as search_replace:
            search_replace.replace("context.description", "context.title", is_regex=False)
            search_replace.search("context.description", is_regex=False)

        template_uid = self.template2.UID()
        view = self.portal.podtemplates.restrictedTraverse("@@document-generation")
        self.assertIn("pdf", self.template2.get_available_formats())
        generated_doc = view(template_uid, "pdf")
        self.assertEqual("%PDF", generated_doc[:4])
