# -*- coding: utf-8 -*-

from plone import api


def isNotCurrentProfile(context):
    return context.readDataFile("collectivedocumentgenerator_marker.txt") is None


def post_install(context):
    """Post install script"""
    if isNotCurrentProfile(context): return
    portal = context.getSite()


def install_demo(context):
    """ """
    portal = api.portal.get()
    templates_folder = api.content.create(
        type='Folder',
        title='podtemplates',
        container=portal
    )
