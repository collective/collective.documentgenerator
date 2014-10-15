# ------------------------------------------------------------------------------
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from collective.documentgenerator.content.pod_template import IPODTemplate

from plone import api
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

    def getAllModels(self):
        catalog = api.portal.get_tool(name='portal_catalog')
        brains = catalog(object_provides=IPODTemplate.__identifier__)
        pod_templates = [brain.getObject() for brain in brains]
        return pod_templates

    def getGenerableModels(self):
        pod_templates = self.getAllModels()
        generable_templates = [pt for pt in pod_templates if pt.can_be_generated(self.context)]
        return generable_templates

    def getLinksInfo(self):
        base_url = self.context.absolute_url()
        generable_templates = self.getGenerableModels()
        links = []
        for template in generable_templates:
            title = template.Title()
            uid = template.UID()
            link = '{base_url}/document-generation?doc_uid={uid}'.format(
                base_url=base_url,
                uid=uid,
            )
            links.append({'link': link, 'title': title})
        return links
