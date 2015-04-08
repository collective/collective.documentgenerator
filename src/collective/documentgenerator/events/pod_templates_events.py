# -*- coding: utf-8 -*-


def set_initial_md5(pod_template, event):
    """
    Set the md5 of the initial document template in 'initial_md5' field.
    """
    pod_template.initial_md5 = pod_template.current_md5
