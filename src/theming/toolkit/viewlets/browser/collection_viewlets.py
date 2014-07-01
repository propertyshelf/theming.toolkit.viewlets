# -*- coding: utf-8 -*-
"""Collection viewlets that render a carousel/slideshow"""

import copy

from plone.app.layout.viewlets.common import ViewletBase
from plone.memoize.view import memoize
from plone.registry.interfaces import IRegistry

from Products.CMFPlone import PloneMessageFactory as PMF

from z3c.form import form,field, button
from zope import schema
from zope.annotation.interfaces import IAnnotations
from zope.component import queryUtility
from zope.component.hooks import getSite
from zope.interface import Interface, alsoProvides, noLongerProvides
from zope.traversing.browser.absoluteurl import absoluteURL

#plone.mls.listing imports
from plone.mls.listing import api
from plone.mls.listing.browser import (
    listing_collection,
    recent_listings,
)

#local import
from theming.toolkit.core.interfaces import IToolkitSettings
from theming.toolkit.viewlets.browser.interfaces import IToolkitBaseViewlets
from theming.toolkit.viewlets.i18n import _

try:
    from plone.app.collection.interfaces import ICollection
except ImportError:
    class ICollection(Interface):
        pass

CONFIGURATION_KEY       = 'theming.toolkit.viewlets.collection'
CONFIGURATION_KEY_ABOVE = 'theming.toolkit.viewlets.featuredlisting.above'
CONFIGURATION_KEY_BELOW = 'theming.toolkit.viewlets.featuredlisting.below'

AVAILABLE_FLS_DEFAULTS = ['featuredListingSlider_ItemList', 'featuredListingSlider_Limit', 'featuredListingSlider_offset', 'featuredListingSliderJS']
MLS_IMAGE_SIZES = ['thumb', 'mini', 'preview', 'large']

class IPossibleCollectionViewlet(Interface):
    """Marker interface for possible Collection viewlet."""

class ICollectionViewlet(IToolkitBaseViewlets):
    """Marker interface for Collection viewlet."""


class FeaturedListingCollectionViewlet(ViewletBase):
    """Show Collection viewlet in header"""

    @property
    def available(self):
        
        return IPossibleCollectionViewlet.providedBy(self.context) and \
            not ICollectionViewlet.providedBy(self.context)

    def update(self):
        super(FeaturedListingCollectionViewlet, self).update()

    @property
    def local_config(self):
        """Get view configuration data from annotations."""
        annotations = IAnnotations(self.context)
        key = self.getConfigurationKey
        return annotations.get(key, {})

    def get_config(self, obj):
        """Get config for listing object"""
        key = self.get_mls_config_key(obj)
        annotations = IAnnotations(obj)
        try:          
            return annotations.get(key, {})
        except Exception:
            return False


    def get_mls_config_key(self, obj):
        """Check if the obj have mls collections.
            if so, return config key for annotations
            if not, reurn False
        """
        if listing_collection.IListingCollection.providedBy(obj):
            return listing_collection.CONFIGURATION_KEY
        elif recent_listings.IRecentListings.providedBy(obj):
            return recent_listings.CONFIGURATION_KEY
        else:
            return False

    @property
    def GlobalDefaults(self):
        """Get the default values from theming.toolkit.core settings"""
        registry = queryUtility(IRegistry)
        global_defaults = registry.forInterface(IToolkitSettings, check=False)

        return global_defaults
        

    @property
    def Settings(self):
        """Return the merged local & global settings"""
        global_defaults = self.GlobalDefaults
        local_settings = self.local_config

        for n in local_settings:
            if local_settings[n] is None:
                try:
                    local_settings[n] = global_defaults[n]
                except Exception:
                    """keys for config in theming.toolkit.core & theming.toolkit.viewlets?"""

        return local_settings

    @property
    def get_code(self):
        """Get Slider JS Code"""
        settings = self.Settings
        return settings.get('featuredListingSliderJS', None)
        

    @property
    def get_title(self):
        """Get Viewlet title"""
        settings = self.Settings
        return settings.get('viewlet_title', False)

    @property
    def ItemsLimit(self):
        """Get the limit parameter for Listing collection"""
        settings = self.Settings
        default = 20
        limit= settings.get('featuredListingSlider_Limit', None)
        if limit is None:
            """no limit set in the settings"""
            return default
        else:
            try:
                return int(limit)
            except Exception:
                msg = _(u"Your Limit setting caused an error. Please check the input.")
                self.context.plone_utils.addPortalMessage(msg, 'error')

    @property
    def ItemsOffset(self):
        """Get the offset parameter for Listing collection"""
        settings = self.Settings
        default = 0
        offset= settings.get('featuredListingSlider_offset', None)
        if offset is None:
            """no limit set in the settings"""
            return default
        else:
            try:
                return int(offset)
            except Exception:
                msg = _(u"Your Offset setting caused an error. Please check the input.")
                self.context.plone_utils.addPortalMessage(msg, 'error')

    @property
    def getConfigurationKey(self):
        """get Config depending on viewlet.manager"""

        manager_name = self.manager.__name__
        if manager_name == u'plone.abovecontentbody':
            return CONFIGURATION_KEY_ABOVE
        elif manager_name == u'plone.belowcontentbody':
            return CONFIGURATION_KEY_BELOW
        else:
            return CONFIGURATION_KEY

    @property
    def ItemProvider(self):
        """the object providing Items to show & slide"""
        annotations = IAnnotations(self.context)
        key = self.getConfigurationKey
        config = annotations.get(key, {})       
        provider_url = config.get('featuredListingSlider_ItemList', None)

        try:
            portal = getSite()
            return portal.restrictedTraverse(provider_url.encode('ascii','ignore'))

        except Exception:
            return None

    @property
    def ProviderUrl(self):
        """delivers the absolute URL to the Item provider"""
        try:
            return self.ItemProvider.absolute_url()
        except Exception:
            return False

    def getProviders(self):
        """Get Listing Provider"""
        return self.ItemProvider


    def results(self):
        """
            try to return a resultset of items
            different data provider are intended
            we try until we find a resultset 

        """
        provider = self.ItemProvider
        
        if provider is None:
            """No ItemProvider found"""
            return None

        try:
            """First Check if we get results from MLS Listing Collections"""
            results= self._mls_results(provider)

            if results is not None:
                return results

        except Exception:
            """no MLS results found"""
            msg = _(u"No MLS results found. Please check the configuration")
            self.context.plone_utils.addPortalMessage(msg, 'error')

        try:
            return provider.results()
        except Exception, e:
            """Don't have .results()"""
            print e
        try:
            return provider.queryCatalog()
        except Exception, e:
            """Don't have .queryCatalog()"""
            print e
        return None

    def _mls_results(self, obj):
        items = []
        
        if obj is None or not obj:
            return None

        if not self.get_mls_config_key(obj):
            """Don't have a MLS Collection"""
            return None

        config = copy.copy(self.get_config(obj))
        portal_state = obj.unrestrictedTraverse('@@plone_portal_state')

        params = {
                'limit': self.ItemsLimit,
                'offset': self.ItemsOffset,
                'lang': portal_state.language(),
            }

        config.update(params)

        try:
            items = api.search(
                params=api.prepare_search_params(config),
                batching=False,
                context=obj,
            )
        except Exception, e:
            print e
            return None

        items = self._resizeImages(items)
        return items

    def _resizeImages(self, data):
        """get config and set new image size"""
        isize = self.Settings.get('featuredListingSlider_ImageSize', None)

        if isize is None:
            """No Image Size defined -> return original data"""
            return data
        if isize not in MLS_IMAGE_SIZES:
            """config input manipulated?"""
            return data
       
        for index, item in enumerate(data):
            """Loop through all listings"""
            iurl = item.get('lead_image', None)

            if iurl is not None:
                """Normalize the MLS imagesize with marker"""
                for s in MLS_IMAGE_SIZES:
                    iurl = iurl.replace(s, 'FLSSIZE')

            try:
                """replace the original url with a new to a bigger image"""
                if iurl is not None:        
                    data[index]['lead_image'] = iurl.replace('FLSSIZE', isize)

            except Exception, e:
                """something wrong with the url?"""
                print e

        return data

    def get_tile(self, obj):
        tile = obj.unrestrictedTraverse("carousel-view")
        if tile is None:
            return None
        return tile()

    @memoize
    def view_url(self):
        """Generate view url."""
        if not self.context_state.is_view_template():
            return self.context_state.current_base_url()
        else:
            return absoluteURL(self.context, self.request) + '/'


class ICollectionViewletConfiguration(Interface):
    """FLS Configuration Form."""

    viewlet_title = schema.TextLine(
        required=False,
        title=_(
            u'Viewlet Title',
            default=u'Viewlet Title',
        ),
    )
    
    featuredListingSlider_ItemList = schema.TextLine(
        required=False,
        title=_(
            u'Item List to show',
            default=u'FeaturedListingSlider Item List',
        ),
    )
    
    """
    featuredListingSlider_ItemList = schema.Choice(
        description=_(
            u'Find the search page which will be used to show the results.'
        ),
        required=False,
        source=ToolkitSearchableTextSourceBinder({'is_folderish' : True}, default_query='path:'),
        title=_(u'Item List to show'),
    )
    """

    use_custom_config = schema.Bool(
        default=True,
        required=False,
        title=_(
            u"label_use_custom_config",
            default=u"Use local Slider Customization",
        ),
    )

    featuredListingSlider_effect =schema.TextLine(
        default=u"",
        required=False,
        title=_(
            u"label_FLS_effect",
            default=u"Slider Animation Effect",
        )      
    )

    featuredListingSlider_duration =schema.TextLine(
        default=u"",
        required=False,
        title=_(
            u"label_FLS_duration",
            default=u"Slider Animation Duration",
        )      
    )

    featuredListingSlider_Limit =schema.TextLine(
        default=u"",
        required=False,
        title=_(
            u"label_FLS_limit",
            default=u"Limit the amount of shown listings ",
        )      
    )

    featuredListingSlider_offset =schema.TextLine(
        default=u"",
        required=False,
        title=_(
            u"label_FLS_offset",
            default=u"Set a offset for the Listing Items in the List",
        )      
    )

    featuredListingSlider_ImageSize = schema.Choice(
        description=_(
            u'Choose the image size of the slider'
        ),
        required=False,
        title=_(u'Slider Image size'),
        values= MLS_IMAGE_SIZES
    )

    use_custom_js = schema.Bool(
        default=False,
        required=False,
        title=_(
            u"label_use_custom_js",
            default=u"Show local Slider Javascript",
        ),
    )

    featuredListingSliderJS =schema.Text(
        default=u"",
        description=PMF(
            u'help_FLS_code',
            default=u'The custom JavaScript code for initialising the FeaturedListingSlider',
        ),
        required=False,
        title=PMF(u'label_featuredListingSliderJS', default=u'Custom JS to start'),
    )

class CollectionViewletConfiguration(form.Form):
    """HeaderPlugin Configuration Form."""

    fields = field.Fields(ICollectionViewletConfiguration)
    ignoreContext = False

    label = _(u"Configure your MLS FeaturedListingSlider")
    description = _(
        u"Adjust the slider settings."
    )

    def __init__(self, context, request):
        """Customized form constructor"""
        super(CollectionViewletConfiguration, self).__init__(context, request)
        self.context = context
        self.request = request

    def updateWidgets(self):
        super(CollectionViewletConfiguration, self).updateWidgets()

    @property
    def getConfigurationKey(self):
        """get Config depending on the form name"""

        name = self.__name__
        if name == 'featuredlisting-collection-config-above':
            return CONFIGURATION_KEY_ABOVE
        elif name == 'featuredlisting-collection-config-below':
            return CONFIGURATION_KEY_BELOW
        else:
            return CONFIGURATION_KEY
    
    @property
    def getGlobalDefaults(self):
        """Get the default values from theming.toolkit.core setting"""
        registry = queryUtility(IRegistry)
        global_defaults = registry.forInterface(IToolkitSettings, check=False)
        fls_fields =AVAILABLE_FLS_DEFAULTS
        fls_local_defaults = {}

        for n in fls_fields:
            try:
                fls_local_defaults[n] = getattr(global_defaults, n, None)
            except:
                """if a field raises an error -> ignore field"""

        return fls_local_defaults
        
        
    def getContent(self):
        annotations = IAnnotations(self.context)
        key = self.getConfigurationKey
        fls_context = annotations.get(key,
                               annotations.setdefault(key, {}))
        defaults = self.getGlobalDefaults

        # set some default values from the global config
        # featuredListingSliderJS
        for k in defaults:
            if fls_context.get(k, None)==None:
                fls_context[k] = defaults[k]

        return fls_context

    @button.buttonAndHandler(_(u'Save'))
    def handle_save(self, action):
        data, errors = self.extractData()
        if not errors:
            annotations = IAnnotations(self.context)
            key = self.getConfigurationKey
            annotations[key] = data
            self.request.response.redirect(absoluteURL(self.context,
                                                       self.request))

    @button.buttonAndHandler(_(u'Cancel'))
    def handle_cancel(self, action):
        self.request.response.redirect(absoluteURL(self.context, self.request))


class CollectionViewletStatus(object):
    """Return activation/deactivation status of HeaderCollection viewlet."""

    def __init__(self, context, request):
        self.context = context
        self.request = request

    @property
    def can_activate(self):
        return IPossibleCollectionViewlet.providedBy(self.context) and \
            not ICollectionViewlet.providedBy(self.context)

    @property
    def active(self):
        return ICollectionViewlet.providedBy(self.context)


class CollectionViewletToggle(object):
    """Toggle HeaderPlugins viewlet for the current context."""

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        msg_type = 'info'

        if ICollectionViewlet.providedBy(self.context):
            # Deactivate.
            noLongerProvides(self.context, ICollectionViewlet)
            self.context.reindexObject(idxs=['object_provides', ])
            msg = _(u"Collection viewlet deactivated.")
        elif IPossibleCollectionViewlet.providedBy(self.context):
            alsoProvides(self.context, ICollectionViewlet)
            self.context.reindexObject(idxs=['object_provides', ])
            msg = _(u"Collection viewlet activated.")
        else:
            msg = _(
                u"The Collection viewlet does't work with this content "
                u"type. Add 'IPossibleCollectionViewlet' to the provided "
                u"interfaces to enable this feature."
            )
            msg_type = 'error'

        self.context.plone_utils.addPortalMessage(msg, msg_type)
        self.request.response.redirect(self.context.absolute_url())
