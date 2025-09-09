# -*- coding: utf-8 -*-
from collective.documentgenerator.testing import PODTemplateIntegrationTest
from collective.documentgenerator.utils import compute_md5
from collective.documentgenerator.utils import convert_odt
from collective.documentgenerator.utils import temporary_file_name
from collective.documentgenerator.utils import update_dict_with_validation
from collective.documentgenerator.utils import update_oo_config
from collective.documentgenerator.utils import update_templates
from os import getenv
from os import rmdir
from plone.api.portal import get_registry_record
from plone.namedfile import NamedBlobFile
from zope.interface import Interface
from zope.interface import Invalid
from zope.lifecycleevent import Attributes
from zope.lifecycleevent import modified

import collective.documentgenerator as cdg
import copy
import os


class TestUtils(PODTemplateIntegrationTest):
    """
    Test Utils methods.
    """

    def test_update_templates(self):
        # we use a ConfigurablePODTemplate to test style modification
        test_template = self.portal.podtemplates.get('test_template_multiple')
        tpath = '%s/profiles/demo/templates' % cdg.__path__[0]

        def path(tmpl):
            return '%s/%s' % (tpath, tmpl)

        with open(path('modele_general.odt'), 'rb') as f:
            mgodt = f.read()
            mgodt_md5 = compute_md5(mgodt)
        with open(path('modèle_collection.odt'), 'rb') as f:
            mcodt_md5 = compute_md5(f.read())

        # check loaded current template is same as os one
        self.assertEqual(test_template.initial_md5, mgodt_md5)
        # check current md5 is no more initial_md5 after style update
        self.assertNotEqual(test_template.initial_md5, test_template.current_md5)
        # check style_modification_md5 is equal to current md5 after style update only
        self.assertEqual(test_template.style_modification_md5, test_template.current_md5)
        self.assertFalse(test_template.has_been_modified())
        modif_date = test_template.modification_date

        # bad plone obj path => no change
        ret = update_templates([('/podtemplates/test_template_bad', path('modele_general.odt'))])
        self.assertEquals(ret[0][2], 'plone path error')

        # bad file path => no change
        ret = update_templates([('/podtemplates/test_template_multiple', path('modele_general.bad'))])
        self.assertEqual(modif_date, test_template.modification_date)
        self.assertEquals(ret[0][2], 'os path error')

        # same os file => unchanged status
        ret = update_templates([('/podtemplates/test_template_multiple', path('modele_general.odt'))])
        self.assertEqual(modif_date, test_template.modification_date)
        self.assertEquals(ret[0][2], 'unchanged')

        # replace file when not same os file and template not modified
        ret = update_templates([('/podtemplates/test_template_multiple', path('modèle_collection.odt'))])
        self.assertEqual(test_template.initial_md5, mcodt_md5)
        self.assertNotEqual(test_template.initial_md5, test_template.current_md5)
        self.assertEqual(test_template.style_modification_md5, test_template.current_md5)
        self.assertFalse(test_template.has_been_modified())
        self.assertEquals(ret[0][2], 'replaced')
        self.assertNotEquals(modif_date, test_template.modification_date)
        modif_date = test_template.modification_date

        # don't replace file when not same os file but template is modified
        # We change template file
        test_template.odt_file.data = mgodt
        modified(test_template, Attributes(Interface, 'odt_file'))
        self.assertEqual(test_template.initial_md5, mcodt_md5)
        self.assertNotEqual(test_template.style_modification_md5, test_template.current_md5)
        self.assertTrue(test_template.has_been_modified())
        modif_date = test_template.modification_date
        ret = update_templates([('/podtemplates/test_template_multiple', path('modele_general.odt'))])
        self.assertEquals(ret[0][2], 'kept')
        self.assertEquals(modif_date, test_template.modification_date)
        # we force replacement
        ret = update_templates([('/podtemplates/test_template_multiple', path('modele_general.odt'))], force=True)
        self.assertEquals(ret[0][2], 'replaced')
        self.assertNotEquals(modif_date, test_template.modification_date)

    def test_update_dict_with_validation(self):
        # if dict have no common keys, nothing is returned
        self._update_dict_with_validation_helper({}, {})
        self._update_dict_with_validation_helper({'test1': 1}, {'test2': 2})
        self._update_dict_with_validation_helper({'test1': 1}, {})
        self._update_dict_with_validation_helper({}, {'test2': 2})
        self._update_dict_with_validation_helper({'test': 1}, {'test1': 2, 'test2': 2})

        # if dict have at least 1 common keys, Invalid is raised
        self.assertRaises(Invalid, update_dict_with_validation, {'test': 1, 'test2': 2}, {'test': 2})
        self.assertRaises(Invalid, update_dict_with_validation, {'test1': 1, 'test_1': 1}, {'test1': 1, 'test2': 1})
        self.assertRaises(Invalid, update_dict_with_validation, {'test': 1}, {'test': 2, 'test1': 1, 'test2': 1})
        self.assertRaises(Invalid, update_dict_with_validation, {'test': 1}, {'test': 2})

    def _update_dict_with_validation_helper(self, original_dict, update_dict):
        res = copy.deepcopy(original_dict)
        self.assertIsNone(update_dict_with_validation(res, update_dict))

        expected = copy.deepcopy(original_dict)
        expected.update(update_dict)

        self.assertDictEqual(res, expected)

    def test_temporary_file_name(self):
        # setup
        initial_custom_tmp = getenv('CUSTOM_TMP', None)
        if 'CUSTOM_TMP' in os.environ:
            del os.environ["CUSTOM_TMP"]
        tmp_dir = "/tmp/random-non-existing-directory"
        if os.path.exists(tmp_dir):
            rmdir(tmp_dir)
        # test
        self.assertRegexpMatches(temporary_file_name(), r"/tmp/tmp.{6}")
        self.assertRegexpMatches(temporary_file_name('foobarbar'), r"/tmp/tmp.{6}foobarbar")

        self.assertFalse(os.path.exists(tmp_dir))
        os.environ["CUSTOM_TMP"] = tmp_dir
        self.assertRegexpMatches(temporary_file_name(), tmp_dir + r"/tmp.{6}")
        self.assertRegexpMatches(temporary_file_name('foobarbar'), tmp_dir + r"/tmp.{6}foobarbar")
        # tear down
        if initial_custom_tmp:
            os.environ["CUSTOM_TMP"] = initial_custom_tmp
        else:
            del os.environ["CUSTOM_TMP"]

    def test_update_oo_config(self):
        original_oo_server = getenv("OO_SERVER")
        original_oo_port = getenv("OO_PORT")
        original_uno = getenv("PYTHON_UNO")

        lo = "libreofficetest"
        port = "10422"
        uno = "/test/fake/python"

        os.environ['OO_SERVER'] = lo
        os.environ['OO_PORT'] = port
        os.environ['PYTHON_UNO'] = uno

        update_oo_config()

        oo_server = get_registry_record('collective.documentgenerator.browser.controlpanel.'
                                        'IDocumentGeneratorControlPanelSchema.oo_server')
        self.assertEqual(oo_server, lo)
        oo_port_list = get_registry_record('collective.documentgenerator.browser.controlpanel.'
                                           'IDocumentGeneratorControlPanelSchema.oo_port_list')
        self.assertEqual(oo_port_list, port)
        uno_path = get_registry_record('collective.documentgenerator.browser.controlpanel.'
                                       'IDocumentGeneratorControlPanelSchema.uno_path')
        self.assertEqual(uno_path, uno)

        if original_oo_server:
            os.environ['OO_SERVER'] = original_oo_server
        if original_oo_port:
            os.environ['OO_PORT'] = original_oo_port
        if original_uno:
            os.environ['PYTHON_UNO'] = original_uno

    def test_convert_odt(self):
        filename = u"test_file.odt"
        current_path = os.path.dirname(__file__)
        odt_file = open(os.path.join(current_path, filename), "r").read()
        odt_blob_file = NamedBlobFile(
            data=odt_file,
            contentType="application/vnd.oasis.opendocument.text",
            filename=filename,
        )

        # convert to pdf
        filename, content = convert_odt(odt_blob_file, "pdf")
        self.assertTrue(filename.endswith(".pdf"))
        self.assertTrue(content.startswith("%PDF-"))
        self.assertEqual(len(content), 7583)

        # convert to odt
        filename, content = convert_odt(odt_blob_file, "odt")
        self.assertTrue(filename.endswith(".odt"))
        self.assertTrue(content.startswith("PK"))
        self.assertEqual(len(content), 9729)

        # convert to docx
        filename, content = convert_odt(odt_blob_file, "docx")
        self.assertTrue(filename.endswith(".docx"))
        self.assertTrue(content.startswith("PK"))
        self.assertEqual(len(content), 5048)

        # convert to rtf
        filename, content = convert_odt(odt_blob_file, "rtf")
        self.assertTrue(filename.endswith(".rtf"))
        self.assertTrue(content.startswith("{\\rtf1"))
        self.assertEqual(len(content), 2338)

        # convert to txt
        filename, content = convert_odt(odt_blob_file, "txt")
        self.assertTrue(filename.endswith(".txt"))
        self.assertEqual(content, "\xef\xbb\xbfPage 1\nPage 2\n")

        # convert to html
        filename, content = convert_odt(odt_blob_file, "html")
        self.assertTrue(filename.endswith(".html"))
        self.assertEqual(
            content,
            '<!DOCTYPE html>\n<html>\n<head>\n\t<meta http-equiv="content-type" content="text/html; chars'
            'et=utf-8"/>\n\t<title></title>\n\t<meta name="generator" content="LibreOffice 24.2.7.2 (Linu'
            'x)"/>\n\t<meta name="created" content="2025-09-08T15:18:36.852551815"/>\n\t<meta name="chang'
            'ed" content="2025-09-08T15:18:57.612006776"/>\n\t<style type="text/css">\n\t\t@page { size: '
            "8.27in 11.69in; margin: 0.79in }\n\t\tp { line-height: 115%; margin-bottom: 0.1in; backgroun"
            'd: transparent }\n\t</style>\n</head>\n<body lang="en-US" link="#000080" vlink="#800000" dir'
            '="ltr"><p style="line-height: 100%; margin-bottom: 0in">\nPage 1</p>\n<p style="line-height:'
            ' 100%; margin-bottom: 0in; page-break-before: always">\nPage 2</p>\n</body>\n</html>',
        )
