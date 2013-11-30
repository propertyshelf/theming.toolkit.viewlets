# -*- coding: utf-8 -*-

"""Custom static viewlets for theming.toolkit.viewlets"""

from plone.app.layout.viewlets.common import ViewletBase
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.registry.interfaces import IRegistry
from zope.component import queryUtility
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

