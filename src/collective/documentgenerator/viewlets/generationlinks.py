# ------------------------------------------------------------------------------
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from plone.app.layout.viewlets import ViewletBase
from zope.component import getMultiAdapter
# ------------------------------------------------------------------------------


class DocumentGeneratorLinksViewlet(ViewletBase):
    '''This viewlet displays the available pod templates for an object'''
    render = ViewPageTemplateFile('./generationlinks.pt')

    def available(self):
        return True

    def update(self):
        self.context_state = getMultiAdapter((self.context, self.request),
                                             name=u'plone_context_state')

    def getCurrentObject(self):
        '''Returns the current object.'''
        return self.context

    def getPortalUrl(self):
        getToolByName(self.context, 'portal_url').getPortalPath()
