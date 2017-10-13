# -*- coding: utf-8 -*-

from Products.Five import BrowserView


class ResetMd5(BrowserView):

    def __call__(self):
        self.context.style_modification_md5 = self.context.current_md5
