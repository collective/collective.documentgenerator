# -*- coding: utf-8 -*-
"""Init and utils."""
from zope.i18nmessageid import MessageFactory

import os


_ = MessageFactory('collective.documentgenerator')

if os.environ.get("ZOPE_HOME", ""):
    BLDT_DIR = "/".join(os.getenv("INSTANCE_HOME", "").split("/")[:-2])
else:  # test env
    BLDT_DIR = os.getenv("PWD", "")


def initialize(context):
    """Initializer called when used as a Zope 2 product."""
