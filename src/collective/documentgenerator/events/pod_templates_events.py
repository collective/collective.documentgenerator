# -*- coding: utf-8 -*-

from collective.documentgenerator.events.styles_events import update_PODtemplate_styles
from collective.documentgenerator.utils import clean_notes
from imio.helpers.content import get_modified_attrs


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
