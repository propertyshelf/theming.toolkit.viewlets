# -*- coding: utf-8 -*-

"""Test Layer theming.toolkit.viewlets"""

# zope imports
from plone.app.testing import (
    IntegrationTesting,
    PloneSandboxLayer,
    PLONE_FIXTURE,
    applyProfile,
)

from zope.configuration import xmlconfig


class ToolkitViewlets(PloneSandboxLayer):
    """Custom Test Layer for theming.toolkit.viewlets"""
    defaultBases = (PLONE_FIXTURE, )

    def setUpZope(self, app, configurationContext):
        # Load ZCML for this package       
        import theming.toolkit.viewlets 
        xmlconfig.file('configure.zcml',
                       theming.toolkit.viewlets,
                       context=configurationContext)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'theming.toolkit.viewlets:default')
        

TOOLKIT_VIEWLETS_FIXTURE = ToolkitViewlets()
TOOLKIT_VIEWLETS_INTEGRATION_TESTING = IntegrationTesting(
    bases=(TOOLKIT_VIEWLETS_FIXTURE, ),
    name="ToolkitViewlets:Integration")
