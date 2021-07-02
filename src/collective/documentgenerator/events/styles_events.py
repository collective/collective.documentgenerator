# -*- coding: utf-8 -*-

import logging
import os

import appy.pod
from appy.shared.utils import executeCommand
from plone import api
from plone.namedfile.file import NamedBlobFile
from Products.CMFPlone.utils import safe_unicode
from zExceptions import Redirect
from zope.i18n import translate

from collective.documentgenerator import _, config
from collective.documentgenerator.content.pod_template import IPODTemplate
from collective.documentgenerator.utils import (remove_tmp_file,
                                                temporary_file_name)

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
            if pod_template.has_linked_template() or \
                    pod_template.odt_file.contentType != 'application/vnd.oasis.opendocument.text':
                continue
            if pod_template.get_style_template() == style_template:
                _update_template_styles(pod_template, style_template_file.name)
                logger.info('"{}" => updated'.format(pod_template.Title()))

    # delete temporary styles files
    remove_tmp_file(style_template_file.name)


def styletemplate_created(style_template, event):
    """
    Set the md5 of the initial style template in 'initial_md5' field.
    """
    if not style_template.initial_md5:
        style_template.initial_md5 = style_template.current_md5


def update_PODtemplate_styles(pod_template, event):
    """
    Update styles on a pod_template using external styles only if not reusing an other template file.
    """
    if not pod_template.has_linked_template():
        style_template = pod_template.get_style_template()
        if not style_template or pod_template.odt_file.contentType != 'application/vnd.oasis.opendocument.text':
            return
        style_odt = style_template.odt_file
        style_template_file = create_temporary_file(style_odt, 'style_template.odt')
        _update_template_styles(pod_template, style_template_file.name)
        logger.info('"{}" => updated'.format(pod_template.Title()))


def _update_template_styles(pod_template, style_template_filename):
    """
    Update template pod_template by templateStyle.
    """
    # we check if the pod_template has been modified except by style only
    style_changes_only = \
        pod_template.style_modification_md5 and pod_template.current_md5 == pod_template.style_modification_md5
    # save in temporary file, the template
    temp_file = create_temporary_file(pod_template.odt_file, 'pod_template.odt')
    with open(temp_file.name, 'w') as new_template:
        new_template.write(pod_template.odt_file.data)

    # merge style from templateStyle in template
    cmd = '{path} {script} {tmp_file} {extension} -e ' \
          '{libreoffice_host} -p {port} ' \
          '-t {style_template} -v -a {stream}'.format(path=config.get_uno_path(),
                                                      script=CONVSCRIPT,
                                                      tmp_file=temp_file.name,
                                                      extension='odt',
                                                      libreoffice_host=config.get_oo_server(),
                                                      port=config.get_oo_port(),
                                                      style_template=style_template_filename,
                                                      stream=config.get_use_stream())
    (stdout, stderr) = executeCommand(cmd.split())
    if stderr:
        logger.error("Error during command '%s'" % cmd)
        logger.error("Error is '%s'" % stderr)
        portal = api.portal.get()
        request = portal.REQUEST
        api.portal.show_message(message=_(u"Problem during styles update on template '${tmpl}': ${err}",
                                          mapping={'tmpl': safe_unicode(pod_template.absolute_url_path()),
                                                   'err': safe_unicode(stderr)}),
                                request=request,
                                type='error')
        raise Redirect(request.get('ACTUAL_URL'),
                       translate(_(u"Problem during styles update on template '${tmpl}': ${err}",
                                   mapping={'tmpl': safe_unicode(pod_template.absolute_url_path()),
                                            'err': safe_unicode(stderr)})))

    # read the merged file
    resTempFileName = '.res.'.join(temp_file.name.rsplit('.', 1))
    if os.path.isfile(resTempFileName):
        with open(resTempFileName, 'rb') as resTemplate:
            # update template
            result = NamedBlobFile(data=resTemplate.read(),
                                   contentType='application/vnd.oasis.opendocument.text',
                                   filename=pod_template.odt_file.filename)
            pod_template.odt_file = result
            # if only styles were modified: update the style_modification_md5 attribute
            if style_changes_only:
                pod_template.style_modification_md5 = pod_template.current_md5
        remove_tmp_file(resTempFileName)
    remove_tmp_file(temp_file.name)


def create_temporary_file(initial_file=None, base_name=''):
    tmp_filename = temporary_file_name(suffix=base_name)
    # create the file in any case
    with open(tmp_filename, 'w+') as tmp_file:
        if initial_file:
            tmp_file.write(initial_file.data)
    return tmp_file
