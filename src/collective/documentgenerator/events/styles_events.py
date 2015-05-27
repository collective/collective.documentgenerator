# -*- coding: utf-8 -*-

from appy.shared.utils import executeCommand

from collective.documentgenerator import config
from collective.documentgenerator.content.pod_template import IPODTemplate

from plone import api
from plone.namedfile.file import NamedBlobFile

import appy.pod
import logging
import os
import tempfile

logger = logging.getLogger('collective.documentgenerator: styles update')

CONVSCRIPT = '%s/converter.py' % os.path.dirname(appy.pod.__file__)


def update_styles_of_all_PODtemplate(style_template, event):
    """
    Update all pod templates using 'style_template'.
    """
    style_odt = style_template.odt_file
    # template style is modify, update all template with style.
    style_template_file = create_temporary_file(style_odt, '-style_template.odt')
    if style_template_file:
        catalog = api.portal.get_tool('portal_catalog')
        pod_templates = catalog(object_provides=IPODTemplate.__identifier__)
        for brain in pod_templates:
            pod_template = brain.getObject()
            if pod_template.get_style_template() == style_template:
                _update_template_styles(pod_template, style_template_file.name)
                logger.info(" %s => updated" % pod_template.Title())

    # delete temporary styles files
    os.remove(style_template_file.name)


def update_PODtemplate_styles(pod_template, event):
    """
    Update styles on a pod_template using external styles.
    """
    style_template = pod_template.get_style_template()
    if not style_template:
        return
    style_odt = style_template.odt_file
    style_template_file = create_temporary_file(style_odt, 'style_template.odt')
    _update_template_styles(pod_template, style_template_file.name)


def _update_template_styles(pod_template, style_template_filename):
    """
    Update template pod_template by templateStyle.
    """
    # save in temporary file, the template
    temp_file = create_temporary_file(pod_template.odt_file, 'pod_template.odt')
    new_template = open(temp_file.name, "w")
    new_template.write(pod_template.odt_file.data)
    new_template.close()

    # merge style from templateStyle in template
    cmd = '%s %s %s %s -p%d -t%s' % \
        (config.get_uno_path(), CONVSCRIPT, temp_file.name, 'odt',
            config.get_oo_port(), style_template_filename)
    executeCommand(cmd.split())

    # read the merged file
    resTempFileName = '.res.'.join(temp_file.name.rsplit('.', 1))
    if os.path.isfile(resTempFileName):
        resTemplate = open(resTempFileName, 'rb')
        # update template
        result = NamedBlobFile(data=resTemplate.read(), contentType='applications/odt')
        pod_template.odt_file = result
        os.remove(resTempFileName)

    os.remove(temp_file.name)


def create_temporary_file(initial_file=None, base_name=''):
    tmp_file = tempfile.NamedTemporaryFile(suffix=base_name, delete=False)
    if initial_file:
        tmp_file.file.write(initial_file.data)
    tmp_file.close()
    return tmp_file
