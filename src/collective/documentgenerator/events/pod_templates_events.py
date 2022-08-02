# -*- coding: utf-8 -*-

from appy.bin.odfsub import Sub
from appy.shared import utils as sutils
from appy.shared.zip import zip as a_zip
from appy.shared.zip import unzip as a_unzip
from collective.documentgenerator.events.styles_events import update_PODtemplate_styles
from collective.documentgenerator.utils import clean_notes
from imio.helpers.content import get_modified_attrs
from plone import api

import io
import os


def podtemplate_created(pod_template, event):
    set_initial_md5(pod_template, event)
    # clean notes, will only update odt_file if any notes cleaned
    clean_notes(pod_template)
    pod_template.add_parent_pod_annotation()


def podtemplate_modified(pod_template, event):
    # add or remove annotation from pod template is managed in the setter
    update_PODtemplate_styles(pod_template, event)
    # clean notes, will only update odt_file if any notes cleaned
    # only clean if odt_file changed, as it is a file, for now even
    # when not changed, it is in mod_attrs... maybe working better newer versions...
    mod_attrs = get_modified_attrs(event)
    if "odt_file" in mod_attrs:
        clean_notes(pod_template)


def podtemplate_will_be_removed(pod_template, event):
    pod_template.del_parent_pod_annotation()


def set_initial_md5(pod_template, event):
    """
    Set the md5 of the initial document template in 'initial_md5' field.
    """
    md5 = pod_template.current_md5
    if not pod_template.initial_md5:
        pod_template.initial_md5 = md5
        pod_template.style_modification_md5 = md5
    update_PODtemplate_styles(pod_template, event)


def apply_default_page_style_for_mailing(pod_template, event):
    """
    """
    force_style = api.portal.get_registry_record(
        'collective.documentgenerator.browser.controlpanel.'
        'IDocumentGeneratorControlPanelSchema.force_default_page_style_for_mailing'
    )
    if not force_style:
        return
    if not pod_template.mailing_loop_template:
        return

    tmp_dir = sutils.getOsTempFolder(sub=True)
    filename = '{}/{}'.format(tmp_dir, pod_template.odt_file.filename)
    if os.path.isfile(filename):
        os.remove(filename)
    # copy the pod templates on the file system.
    changed = False
    with open(filename, "wr") as template_file:
        template_file.write(pod_template.odt_file.data)
        appy_sub = DocGenSub()
        appy_sub.tempFolder = tmp_dir
        contents = a_unzip(io.BytesIO(pod_template.odt_file.data), tmp_dir, odf=True)
        changed = appy_sub.analyseContent(contents)

    if changed:
        print "APLIED DEFAULT PAGE STYLE"
        # Re-zip the result
        a_zip(filename, tmp_dir, odf=True)
        with open(filename, "r") as new_template_file:
            pod_template.odt_file.data = new_template_file.read()

    # Delete the temp folder
    sutils.FolderDeleter.delete(tmp_dir)


class DocGenSub(Sub):

    def __init__(self):
        self.check = False
        return
