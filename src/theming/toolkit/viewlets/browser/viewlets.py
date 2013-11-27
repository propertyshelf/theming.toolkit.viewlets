# -*- coding: utf-8 -*-

###############################################################################
#
# Copyright (c) 2013 Propertyshelf, Inc. and its Contributors.
# All Rights Reserved.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by the
# Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
###############################################################################
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

