# -*- coding: utf-8 -*-

"""Custom static viewlets for theming.toolkit.viewlets"""
from Acquisition import aq_inner
from plone.app.layout.viewlets.common import ViewletBase
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFCore.utils import getToolByName
from plone.registry.interfaces import IRegistry
from zope.component import queryUtility
from zope.component import getMultiAdapter
from theming.toolkit.core.interfaces import IToolkitSettings


class SocialHeaderViewlet(ViewletBase):
    index = ViewPageTemplateFile('templates/socialheader.pt')

    def update(self):
        super(SocialHeaderViewlet, self).update()
        registry = queryUtility(IRegistry)
        self.registry_settings = registry.forInterface(IToolkitSettings, check=False)
        
    @property
    def available(self):
        settings = self.registry_settings
        if not getattr(settings, 'show_headerplugin', True):
            return False
        return True

    @property
    def getCode(self):
        settings = self.registry_settings
        code = getattr(settings, 'headerplugin_code', None)
        
        return code


class TitleContactViewlet(ViewletBase):
    index = ViewPageTemplateFile('templates/titlecontact.pt')

    def update(self):
        super(TitleContactViewlet, self).update()
        registry = queryUtility(IRegistry)
        self.registry_settings = registry.forInterface(IToolkitSettings, check=False)
        self.site_title = self.portal_state.portal_title()

    @property
    def available(self):
        settings = self.registry_settings
        if not getattr(settings, 'show_title_contact', True):
            return False
        return True

    @property
    def getCode(self):
        settings = self.registry_settings
        code = getattr(settings, 'contact_code', None)
        
        return code


class NaviViewlet(ViewletBase):
    """featured navigation Viewlet."""
    index = ViewPageTemplateFile('templates/featured-navigation.pt')

    def update(self):
        """update: set context"""
        super(NaviViewlet, self).update()

        self.id = self.context.id
        self.context_state = getMultiAdapter((self.context, self.request),
                                             name=u'plone_context_state')
        self.portal_state = getMultiAdapter((self.context, self.request),
                                            name=u'plone_portal_state')
        self.navigation_root_path = self.portal_state.navigation_root_path()
        self.lang = self.portal_state.language()

    @property
    def catalog(self):
        context = aq_inner(self.context)
        return getToolByName(context, 'portal_catalog')

    @property
    def available(self):

        return True

    def getTabSources(self):
        """ List content items in the folder of this item.

        """
        navi_url = ''
        path = '/'.join([self.navigation_root_path, navi_url])
        foo = self.catalog( path={'query': path, 'depth': 2},
                            sort_on='getObjPositionInParent',
                            portal_type=['Document', 'Folder',],
                            Subject=('featured navigation', 'Featured Navigation' )
                            )

        return foo

    def getTabData(self):
        """
        Generate dict of data needed to render navigation tabs.
        """
        self.tabs = self.getTabSources()
        published = self.request.get("PUBLISHED", None)

        if hasattr(published, "context"):
            published = published.context

        for t in self.tabs:
            active = (t == published)
            link_data = self.getLinkData(t)
            data = {
                "url": link_data['url'],
                "class": "navi-item selected" if active else "navi-item normal",
                "title": t.Title,
                "id": t.getId,
                "image": link_data['image']
            }
            yield data

    def getLinkData(self, brain):
        """
        Get lead image for ZCatalog brain in folder listing.
        (Based on collective.contentleadimage add-on product)
        @param brain: Products.ZCatalog.Catalog.mybrains object

        @return: HTML source code for content lead <img>
        """
        context = brain.getObject()
        data = {'image': None, 'url': context.absolute_url_path()}

        # First check if the index exist
        if "hasContentLeadImage" in brain:
            has_image = brain.hasContentLeadImage
        else:
            has_image = False

        # The value was missing, None or False
        if not has_image:
            return data

        # AT inspection API
        field = context.getField("leadImage")
        if not field:
            return data

        # ImageField.tag() API
        if field.get_size(context) != 0:
            scale = "leadimage"  
            data['image'] = field.tag(context, scale=scale)

        return data

