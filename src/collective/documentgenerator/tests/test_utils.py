# -*- coding: utf-8 -*-
from collective.documentgenerator.testing import PODTemplateIntegrationTest
from collective.documentgenerator.utils import compute_md5
from collective.documentgenerator.utils import update_dict_with_validation
from collective.documentgenerator.utils import update_templates
from zope.interface import Invalid
from zope.lifecycleevent import modified

import collective.documentgenerator as cdg
import copy


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
        modified(test_template)
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
