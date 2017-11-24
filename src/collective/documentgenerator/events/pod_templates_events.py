# -*- coding: utf-8 -*-
from styles_events import update_PODtemplate_styles


def podtemplate_created(pod_template, event):
    set_initial_md5(pod_template, event)
    pod_template.add_parent_pod_annotation()


def podtemplate_modified(pod_template, event):
    # add or remove annotation from pod template is managed in the setter
    update_PODtemplate_styles(pod_template, event)


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
