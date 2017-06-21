# -*- coding: utf-8 -*-

from zExceptions import Redirect
from appy.shared.utils import executeCommand

from collective.documentgenerator import config
from collective.documentgenerator.content.pod_template import IPODTemplate
from .. import _

from plone import api
from plone.namedfile.file import NamedBlobFile

from Products.CMFPlone.utils import safe_unicode

import appy.pod
import logging
import os
import tempfile

logger = logging.getLogger('collective.documentgenerator: styles update')

CONVSCRIPT = '{}/converter.py'.format(os.path.dirname(appy.pod.__file__))


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
            if pod_template.odt_file.contentType != 'application/vnd.oasis.opendocument.text':
                return
            if pod_template.get_style_template() == style_template:
                _update_template_styles(pod_template, style_template_file.name)
                logger.info(' {} => updated'.format(pod_template.Title()))

    # delete temporary styles files
    os.remove(style_template_file.name)


def podtemplate_modified(pod_template, event):
    update_PODtemplate_styles(pod_template, event)


def update_PODtemplate_styles(pod_template, event):
    """
    Update styles on a pod_template using external styles.
    """
    style_template = pod_template.get_style_template()
    if not style_template or pod_template.odt_file.contentType != 'application/vnd.oasis.opendocument.text':
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
    new_template = open(temp_file.name, 'w')
    new_template.write(pod_template.odt_file.data)
    new_template.close()

    # merge style from templateStyle in template
    cmd = '{path} {script} {tmp_file} {extension} -p{port} -t{style_template}'.format(
        path=config.get_uno_path(),
        script=CONVSCRIPT,
        tmp_file=temp_file.name,
        extension='odt',
        port=config.get_oo_port(),
        style_template=style_template_filename
    )
    (stdout, stderr) = executeCommand(cmd.split())
    if stderr:
        request = pod_template.REQUEST
        api.portal.show_message(message=_(u"Problem during styles update on template '${tmpl}': ${err}",
                                mapping={'tmpl': safe_unicode(pod_template.absolute_url_path()),
                                         'err': safe_unicode(stderr)}),
                                request=request, type='error')
        raise Redirect(request.get('ACTUAL_URL'), _(u"Problem during styles update on template '${tmpl}': ${err}",
                                                    mapping={'tmpl': safe_unicode(pod_template.absolute_url_path()),
                                                             'err': safe_unicode(stderr)}))

    # read the merged file
    resTempFileName = '.res.'.join(temp_file.name.rsplit('.', 1))
    if os.path.isfile(resTempFileName):
        resTemplate = open(resTempFileName, 'rb')
        # update template
        result = NamedBlobFile(data=resTemplate.read(),
                               contentType='application/vnd.oasis.opendocument.text',
                               filename=pod_template.odt_file.filename)
        pod_template.odt_file = result
        os.remove(resTempFileName)

    os.remove(temp_file.name)


def create_temporary_file(initial_file=None, base_name=''):
    tmp_file = tempfile.NamedTemporaryFile(suffix=base_name, delete=False)
    if initial_file:
        tmp_file.file.write(initial_file.data)
    tmp_file.close()
    return tmp_file
