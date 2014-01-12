# -*- coding: utf-8 -*-

"""Test Viewlets of theming.toolkit.viewlets"""

from zope.interface import alsoProvides

from plone.app.layout.viewlets.tests.base import ViewletsTestCase
from theming.toolkit.viewlets.browser.header_plugins import (HeaderPluginsViewlet, \
    IHeaderPlugins, IPossibleHeaderPlugins)
from theming.toolkit.viewlets.browser.viewlets import NaviViewlet



class TestToolkitViewlet(ViewletsTestCase):
    """Test the content views viewlet.
    """

    def afterSetUp(self):
        self.folder.invokeFactory('Document', 'test',
                                  title='Test default page')
        self.folder.test.unmarkCreationFlag()
        self.folder.setTitle(u"Folder")
        alsoProvides(self.folder.test, IHeaderPlugins)
        alsoProvides(self.folder.test, IPossibleHeaderPlugins)
        self.folder.test.reindexObject(idxs=['object_provides', ])
        

    def _invalidateRequestMemoizations(self):
        try:
            del self.app.REQUEST.__annotations__
        except AttributeError:
            pass

    def test_headerplugins_available(self):
        """ Test for availabbility of HeaderPlugins Viewlet
        """
        self._invalidateRequestMemoizations()
        self.loginAsPortalOwner()
        self.app.REQUEST['ACTUAL_URL'] = self.folder.test.absolute_url()
        
        viewlet = HeaderPluginsViewlet(self.folder, self.app.REQUEST, None)
        viewlet.update()
        self.assertEqual(viewlet.site_url, "http://nohost/plone")
        self.assertFalse(viewlet.available)
        viewlet = HeaderPluginsViewlet(self.folder.test, self.app.REQUEST, None)
        viewlet.update()
        self.assertTrue(viewlet.available)


    def test_featuredNav_viewlet(self):
        """Test for featured Navi Viewlet"""
        self._invalidateRequestMemoizations()
        self.loginAsPortalOwner()
        self.app.REQUEST['ACTUAL_URL'] = self.folder.test.absolute_url()
        #test featured navi
        viewlet = NaviViewlet(self.folder.test, self.app.REQUEST, None)
        viewlet.update()
        self.assertTrue(viewlet.available)
