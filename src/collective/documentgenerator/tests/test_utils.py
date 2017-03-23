# -*- coding: utf-8 -*-
import copy

from collective.documentgenerator.testing import PODTemplateIntegrationTest
from collective.documentgenerator.utils import update_templates, compute_md5, update_dict_with_validation
import collective.documentgenerator as cdg
from zope.interface import Invalid


class TestUtils(PODTemplateIntegrationTest):
    """
    Test Utils methods.
    """

    def test_update_templates(self):
        tpath = '%s/profiles/demo/templates' % cdg.__path__[0]

        def path(tmpl):
            return '%s/%s' % (tpath, tmpl)

        with open(path('modele_general.odt'), 'rb') as f:
            mgodt = compute_md5(f.read())
        with open(path('modele_general.ods'), 'rb') as f:
            mgods = compute_md5(f.read())

        # check current file
        self.assertEqual(self.test_podtemplate.initial_md5, mgodt)
        modified = self.test_podtemplate.modification_date
        # replace file
        ret = update_templates([('/podtemplates/test_template', path('modele_general.ods'))])
        self.assertEqual(compute_md5(self.test_podtemplate.odt_file.data), mgods)
        self.assertEquals(ret[0][2], 'replaced')
        self.assertNotEquals(modified, self.test_podtemplate.modification_date)
        modified = self.test_podtemplate.modification_date
        # bad plone obj path => no change
        ret = update_templates([('/podtemplates/test_template_bad', path('modele_general.odt'))])
        self.assertEqual(modified, self.test_podtemplate.modification_date)
        self.assertEquals(ret[0][2], 'plone path error')
        # bad file path => no change
        ret = update_templates([('/podtemplates/test_template', path('modele_general.bad'))])
        self.assertEqual(modified, self.test_podtemplate.modification_date)
        self.assertEquals(ret[0][2], 'os path error')
        # same file => no change
        ret = update_templates([('/podtemplates/test_template', path('modele_general.ods'))])
        self.assertEqual(modified, self.test_podtemplate.modification_date)
        self.assertEquals(ret[0][2], 'unchanged')

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
