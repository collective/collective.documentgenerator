# -*- coding: utf-8 -*-

from collective.documentgenerator.testing import PODTemplateIntegrationTest
from collective.documentgenerator.utils import update_templates, compute_md5
import collective.documentgenerator as cdg


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
