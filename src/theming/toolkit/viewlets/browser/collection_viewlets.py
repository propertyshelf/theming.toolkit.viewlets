# -*- coding: utf-8 -*-
"""Collection viewlets that render f.e. a carousel/slideshow"""

import copy

from plone.app.layout.viewlets.common import ViewletBase
from plone.memoize.view import memoize
from plone.registry.interfaces import IRegistry

from Products.CMFPlone import PloneMessageFactory as PMF

from z3c.form import button, field, form, group
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
SLIDER_STEPS = ["1", "2", "3", "4", "5","6","7", "8", "9", "10"]
SLIDER_STEPS_FULL = ["0", "1", "2", "3", "4", "5","6","7", "8", "9", "10"]

ARROW_STYLE ={}
ARROW_STYLE['arrow01']='<span u="arrowleft" class="jssora01l" style="width: 45px; height: 45px; top: 127.5px; left: 8px;"/><span u="arrowright" class="jssora01r" style="width: 45px; height: 45px; top: 127.5px; right: 8px;"/>'
ARROW_STYLE['arrow02']='<span u="arrowleft" class="jssora02l" style="width: 55px; height: 55px; top: 122.5px; left: 8px;"/><span u="arrowright" class="jssora02r" style="width: 55px; height: 55px; top: 122.5px; right: 8px;"/>'
ARROW_STYLE['arrow03']='<span u="arrowleft" class="jssora03l" style="width: 55px; height: 55px; top: 122.5px; left: 8px;"/><span u="arrowright" class="jssora03r" style="width: 55px; height: 55px; top: 122.5px; right: 8px;"/>'
ARROW_STYLE['arrow04']='<span u="arrowleft" class="jssora04l" style="width: 28px; height: 40px; top: 130px;   left: 8px;"/><span u="arrowright" class="jssora04r" style="width: 28px; height: 40px; top: 130px;   right: 8px;"/>'
ARROW_STYLE['arrow05']='<span u="arrowleft" class="jssora05l" style="width: 40px; height: 40px; top: 130px;   left: 8px;"/><span u="arrowright" class="jssora05r" style="width: 40px; height: 40px; top: 130px;   right: 8px;"/>'
ARROW_STYLE['arrow06']='<span u="arrowleft" class="jssora06l" style="width: 45px; height: 45px; top: 127.5px; left: 8px;"/><span u="arrowright" class="jssora06r" style="width: 45px; height: 45px; top: 127.5px; right: 8px;"/>'
ARROW_STYLE['arrow07']='<span u="arrowleft" class="jssora07l" style="width: 50px; height: 50px; top: 125px;   left: 8px;"/><span u="arrowright" class="jssora07r" style="width: 50px; height: 50px; top: 125px;   right: 8px;"/>'
ARROW_STYLE['arrow08']='<span u="arrowleft" class="jssorb08l" style="width: 50px; height: 50px; top: 8px; left: 275px;"/><span u="arrowright" class="jssorb08r" style="width: 50px; height: 50px; bottom: 8px; left: 275px;"/>'
ARROW_STYLE['arrow09']='<span u="arrowleft" class="jssora09l" style="width: 50px; height: 50px; top: 125px; left: 8px;"/><span u="arrowright" class="jssora09r" style="width: 50px; height: 50px; top: 125px; right: 8px;"/>'
ARROW_STYLE['arrow10']='<span u="arrowleft" class="jssora10l" style="width: 28px; height: 40px; top: 130px; left: 8px;"/><span u="arrowright" class="jssora10r" style="width: 28px; height: 40px; top: 130px; right: 8px;"/>'
ARROW_STYLE['arrow11']='<span u="arrowleft" class="jssora11l" style="width: 37px; height: 37px; top: 131.5px; left: 8px;"/><span u="arrowright" class="jssora11r" style="width: 37px; height: 37px; top: 131.5px; right: 8px;"/>'
ARROW_STYLE['arrow12']='<span u="arrowleft" class="jssora12l" style="width: 30px; height: 46px; top: 127px; left: 0px;"/><span u="arrowright" class="jssora12r" style="width: 30px; height: 46px; top: 127px; right: 0px;"/>'
ARROW_STYLE['arrow13']='<span u="arrowleft" class="jssora13l" style="width: 40px; height: 50px; top: 125px; left: 0px;"/><span u="arrowright" class="jssora13r" style="width: 40px; height: 50px; top: 125px; right: 0px;"/>'
ARROW_STYLE['arrow14']='<span u="arrowleft" class="jssora14l" style="width: 30px; height: 50px; top: 125px; left: 0px;"/><span u="arrowright" class="jssora14r" style="width: 30px; height: 50px; top: 125px; right: 0px;"/>'
ARROW_STYLE['arrow15']='<span u="arrowleft" class="jssora15l" style="width: 20px; height: 38px; top: 131px; left: 18px;"/><span u="arrowright" class="jssora15r" style="width: 20px; height: 38px; top: 131px; left: 18px;"/>'
ARROW_STYLE['arrow16']='<span u="arrowleft" class="jssora16l" style="width: 22px; height: 36px; top: 132px; left: 18px;"/><span u="arrowright" class="jssora16r" style="width: 22px; height: 36px; top: 132px; right: 18px;"/>'
ARROW_STYLE['arrow18']='<span u="arrowleft" class="jssora18l" style="width: 29px; height: 29px; top: 135.5px; left: 8px;"/><span u="arrowright" class="jssora18r" style="width: 29px; height: 29px; top: 135.5px; right: 8px;"/>'
ARROW_STYLE['arrow19']='<span u="arrowleft" class="jssora19l" style="width: 50px; height: 50px; top: 125px; left: 8px;"/><span u="arrowright" class="jssora19r" style="width: 50px; height: 50px; top: 125px; right: 8px;"/>'
ARROW_STYLE['arrow20']='<span u="arrowleft" class="jssora20l" style="width: 55px; height: 55px; top: 122.5px; left: 8px;"/><span u="arrowright" class="jssora20r" style="width: 55px; height: 55px; top: 122.5px; right: 8px;"/>'
ARROW_STYLE['arrow21']='<span u="arrowleft" class="jssora21l" style="width: 55px; height: 55px; top: 122.5px; left: 8px;"/><span u="arrowright" class="jssora21r" style="width: 55px; height: 55px; top: 122.5px; right: 8px;"/>'

BULLET_STYLE ={}
BULLET_STYLE['bullet01']='<div u="navigator" class="jssorb01" style="position:absolute; bottom:16px; right:10px;"><div u="prototype" style="position:absolute; width:12px; height:12px;"/></div>'
BULLET_STYLE['bullet02']='<div u="navigator" class="jssorb02" style="position:absolute; bottom:16px; left:6px;" ><div u="prototype"  style="position:absolute; width:21px; height:21px; text-align:center; line-height:21px; color:White; font-size:12px;"><div u="numbertemplate" /></div></div>'
BULLET_STYLE['bullet03']='<div u="navigator" class="jssorb03" style="position:absolute; bottom:16px; left:6px;" ><div u="prototype"  style="position:absolute; width:21px; height:21px; text-align:center; line-height:21px; color:white; font-size:12px;"><div u="numbertemplate" /></div></div>'
BULLET_STYLE['bullet05']='<div u="navigator" class="jssorb05" style="position:absolute; bottom:16px; right:6px;"><div u="prototype"  style="position:absolute; width:16px; height:16px;" /></div>'
BULLET_STYLE['bullet06']='<div u="navigator" class="jssorb06" style="position:absolute; bottom:16px; left:6px;" ><div u="prototype"  style="position:absolute; width:18px; height:18px;" /></div>'
BULLET_STYLE['bullet07']='<div u="navigator" class="jssorb07" style="position:absolute; bottom:16px; left:6px;" ><div u="prototype"  style="position:absolute; width:20px; height:20px;" /></div>'
BULLET_STYLE['bullet09']='<div u="navigator" class="jssorb09" style="position:absolute; bottom:16px; right:10px;"><div u="prototype" style="position:absolute; width:12px; height:12px;" /></div>'
BULLET_STYLE['bullet10']='<div u="navigator" class="jssorb10" style="position:absolute; bottom:16px; right:6px;" ><div u="prototype" style="position:absolute; width:11px; height:11px;" /></div>'
BULLET_STYLE['bullet11']='<div u="navigator" class="jssorb11" style="position:absolute; bottom:16px; right:6px;" ><div u="prototype" style="position:absolute; width:11px; height:11px;" /></div>'
BULLET_STYLE['bullet12']='<div u="navigator" class="jssorb12" style="position:absolute; bottom:16px; right:6px;" ><div u="prototype" style="position:absolute; width:16px; height:16px;"/></div>'
BULLET_STYLE['bullet13']='<div u="navigator" class="jssorb13" style="position:absolute; bottom:16px; right:6px;" ><div u="prototype" style="position:absolute; width:21px; height:21px;" /></div>'
BULLET_STYLE['bullet14']='<div u="navigator" class="jssorb14" style="position:absolute; bottom:16px; right:6px;"><div u="prototype" style="position:absolute; width:12px; height:12px;" /></div>'
BULLET_STYLE['bullet16']='<div u="navigator" class="jssorb16" style="position:absolute;bottom:16px;right:6px;"><div u="prototype" style="position:absolute; width:21px; height:21px;" /></div>'
BULLET_STYLE['bullet17']='<div u="navigator" class="jssorb17" style="position:absolute;bottom:16px;right:6px;"><div u="prototype" style="position:absolute; width:16px; height:16px;" /></div>'
BULLET_STYLE['bullet18']='<div u="navigator" class="jssorb18" style="position:absolute;bottom:16px;right:6px;"><div u="prototype" style="position:absolute; width:24px; height:24px;text-align:center;line-height:24px;font-size:16px;"><div u="numbertemplate" class="n" /></div></div>'
BULLET_STYLE['bullet20']='<div u="navigator" class="jssorb20" style="position:absolute;bottom:16px;left:6px;"><div u="prototype" style="position:absolute; width:19px; height:19px;text-align:center;line-height:19px;color:White;font-size:12px;"><div u="numbertemplate"/></div></div>'
BULLET_STYLE['bullet21']='<div u="navigator" class="jssorb21" style="position:absolute;bottom:16px;left:6px;"><div u="prototype" style="position:absolute; width:19px; height:19px;text-align:center;line-height:19px;color:White;font-size:12px;" /></div>'


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
        """Get Slider JS Code depending on its settings"""

        settings = self.Settings
        script_mode = settings.get('use_custom_js', None)
        if script_mode is True:
            return settings.get('featuredListingSliderJS', None)
        else:
            return settings.get('genericJS', None)

    @property
    def get_ArrowNavigator(self):
        """Get Arrow Navigator"""
        settings = self.Settings
        script_mode = settings.get('AN_useCustomTemplate', None)
        if script_mode is True:
            return settings.get('AN_customTemplate', None)
        else:
            return settings.get('AN_genericTemplate', None)

    @property
    def get_BulletPointNavigator(self):
        """Get Arrow Navigator"""
        settings = self.Settings
        script_mode = settings.get('BNO_useCustomTemplate', None)
        if script_mode is True:
            return settings.get('BNO_customTemplate', None)
        else:
            return settings.get('BNO_genericTemplate', None)

    @property
    def get_css(self):
        """Get custom css"""
        settings = self.Settings
        return settings.get('featuredListingSliderCSS', None)
        
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
            else:
                msg = _(u"No MLS results found. Please check the configuration")
                self.context.plone_utils.addPortalMessage(msg, 'error')

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

    @property
    def StageHeight(self):
        """Return the height of the Slider Stage"""
        settings = self.Settings
        return settings.get('featuredListingSlider_height', None)

    @property
    def StageWidth(self):
        """Return the height of the Slider Stage"""
        settings = self.Settings
        return settings.get('featuredListingSlider_width', None)

    @property
    def StageCss(self):
        """Return a css string for the slider stage"""
        css_string='overflow: hidden; cursor: move; position: relative;'
        if self.StageHeight is not None:
            css_string+=' height:'+self.StageHeight+';'

        if self.StageWidth is not None:
            css_string+=' width:'+self.StageWidth+';'

        return css_string

    @property
    def haveBulletPointNavigator(self):
        """Check config if BulletPointNavigator should be rendered"""
        settings = self.Settings
        return settings.get('FLS_BulletNavigator', False)

    @property
    def BulletPointCss(self):
        """deliver the CSS for the BulletPoint Prototype"""
        settings = self.Settings
        return settings.get('BNO_PrototypeCSS', None)

    @property
    def haveArrowNavigator(self):
        """Check config if ArrowNavigator should be rendered"""
        settings = self.Settings
        return settings.get('FLS_ArrowNavigator', False)


class ICollectionViewletConfiguration(Interface):
    """FLS Configuration Form."""

    
class IItemProvider(Interface):
    """which items show up in the slider?"""
    viewlet_title = schema.TextLine(
        required=False,
        title=_(
            u'label_CarouselTitle',
            default=u'Slider Headline',
        ),
    )

    featuredListingSlider_ItemList = schema.TextLine(
        required=True,
        title=_(
            u'label_ItemList',
            default=u'Content Provider',
        ),
        description=_(
            u'Please enter the PATH to the Collection which holds the items for the Slider. Example{ /Plone/en/listing-collection }'
        ),
    )

    isMLSListingSlider = schema.Bool(
        default=True,
        required=False,
        title=_(
            u"label_FLS_isFLS",
            default=u"Is a MLS Listing Slider?",
        ),
        description=_(
            u'To ensure the Slider shows the correct content please check this checkbox if you want to show Listings from your MLS. If the checkbox is not active, the Slider will try to find internal Plone content as Slides'
        ),
    )

   
    featuredListingSlider_Limit =schema.TextLine(
        default=u"",
        required=False,
        title=_(
            u"label_FLS_limit",
            default=u"Limit Content Provider Items",
        ),
        description=_(u'To avoid endless loading times, limit the Items from the Content Provider above.')
    )

    featuredListingSlider_ImageSize = schema.Choice(
        description=_(
            u'Choose the size of the image in rendered in the List'
        ),
        required=False,
        title=_(u'Slider Image size'),
        values= MLS_IMAGE_SIZES
    )

    featuredListingSlider_offset =schema.TextLine(
        default=u"",
        required=False,
        title=_(
            u"label_FLS_offset",
            default=u"Set a offset for the Listing Items in the List",
        )      
    )

    
class IPlayerOptions(Interface):
    """Set the Options for the player behavior"""

    FLS_SlideDuration = schema.TextLine(
        default=u"500",
        required=False,
        title=_(
            u"label_FLS_SlideDuration",
            default=u"Slide Duration",
        )    ,
        description=_(
            u'Specifies default duration for right to left animation in milliseconds'
        ),  
    )

    FLS_autoplay = schema.Bool(
        default=True,
        required=False,
        title=_(
            u"label_FLS_autoplay",
            default=u"Activate Autoplay on this Slider",
        ),
    )

    FLS_AutoPlayInterval = schema.TextLine(
        default=u"6000",
        description=_(u'Interval (in milliseconds) to go for next slide since the previous stopped if the slider is auto playing'),  
        required=False,
        title=_(
            u"label_FLS_AutoPlayInterval",
            default=u"Auto Play Interval",
        ),
    )

    FLS_AutoPlaySteps = schema.Choice(
        default=u"1",
        description=_(u'Steps to go for each navigation request (this options applys only when slideshow disabled).'),  
        required=False,
        title=_(
            u"label_FLS_AutoPlaySteps",
            default=u"Auto Play Steps",
        ),
        values= SLIDER_STEPS
    )

    FLS_SlideShow = schema.Bool(
        default=True,
        required=False,
        title=_(
            u"label_FLS_SlideShow",
            default=u"Activate Slideshow Options",
        ),
        description=_(
            u'Use complex transitions instead of a simple slide effect'
        ),
    )

    SS_Transitions =schema.TextLine(
        default=u"",
        required=False,
        title=_(
            u"label_SS_transition",
            default=u"SlideShow Transition Effects",
        ) ,
        description=_(u"Paste custom Transition Effects here")     
    )

    SS_TransitionsOrder = schema.Choice(
        default=u"1",
        description=_(u'The way to choose between multiple transition, (1): Sequence [default], (0): Random'),  
        required=False,
        title=_(
            u"label_SS_TransitionOrder",
            default=u"TransitionsOrder",
        ),
        values= ["0", "1"]
    )

    SS_ShowLink = schema.Bool(
        default=False,
        required=False,
        title=_(
            u"label_SS_ShowLink",
            default=u"Show Slide Link?",
        ),
        description=_(u'Whether to bring slide link on top of the slider when slideshow is running, [default = false]'),  
        
    )


    FLS_PauseOnHover= schema.Choice(
        default=u"3",
        description=_(u'Whether to pause when mouse over if a slider is auto playing, (0): no pause, (1): pause for desktop, (2): pause for touch device, (3): pause for desktop and touch device'),  
        required=False,
        title=_(
            u"label_FLS_PauseOnHover",
            default=u"Pause on Hover",
        ),
        values= ["0", "1", "2","3"]
    )

    FLS_FillMode = schema.Choice(
        default=u"5",
        description=_(u'The way to fill image in slide, (0): stretch, (1): contain (keep aspect ratio and put all inside slide), (2): cover (keep aspect ratio and cover whole slide), (4): actual size, (5): contain for large image, actual size for small image'),  
        required=False,
        title=_(
            u"label_FLS_FillMode",
            default=u"Image filling Mode",
        ),
        values= ["0", "1", "2", "4", "5"]
    )

    FLS_Loop =schema.Choice(
        default=u"1",
        required=False,
        title=_(
            u"label_FLS_Loop",
            default=u"Slider Loop Behaviour",
        ),
        description=_(u'Enable loop(circular) of carousel or not, 0: stop, 1: loop, 2 rewind'),
        values= ["0", "1", "2"]
    )

    FLS_PlayOrientation = schema.Choice(
        default=u"1",
        required=False,
        title=_(
            u"label_FLS_PlayOrientation",
            default=u"Slider Play Orientation",
        ),
        description=_(u'Orientation to play slide (for auto play, navigation), 1: horizental, 2: vertical, 5: horizental reverse, 6: vertical reverse'),
        values= ["1", "2", "5", "6"]
    )


class ISlideConfig(Interface):
    """Setting for Slide Customizations"""
    # options for Stage & Slides
    featuredListingSlider_height =schema.TextLine(
        default=u"350px",
        required=True,
        title=_(
            u"label_FLS_height",
            default=u"Stage Height",
        )    ,
        description=_(
            u'Set the height of the slider stage box (default:350px). The value can be entered with as css compatible unit (px, %, em, ...).'
        ),  
    )

    featuredListingSlider_width =schema.TextLine(
        default=u"100%",
        required=True,
        title=_(
            u"label_FLS_width",
            default=u"Stage Width",
        ),
        description=_(u'Set the width of the slider stage box (default:100%). The value can be entered with as css compatible unit (px, %, em, ...).'),  
    )

    FLS_DisplayPieces = schema.Choice(
        default=u"1",
        description=_(u'Number of pieces to display (the slideshow would be disabled if the value is set to greater than 1)'),  
        required=False,
        title=_(
            u"label_FLS_DisplayPieces",
            default=u"How many Slides?",
        ),
        values= SLIDER_STEPS
    )

    FLS_SlideWidth = schema.TextLine(
        description=_(u'Width of every slide in pixels, default value is width of "slides" container'),  
        required=False,
        title=_(
            u"label_FLS_SlideWidth",
            default=u"Slide Width (in px)",
        ),
    )

    FLS_SlideHeight = schema.TextLine(
        description=_(u"Height of every slide in pixels, default value is height of 'slides' container"),  
        required=False,
        title=_(
            u"label_FLS_SlideHeight",
            default=u"Slide Height (in px)",
        ),
    )

    FLS_SlideSpacing = schema.TextLine(
        description=_(u'Space between each slide in pixels'),  
        required=False,
        title=_(
            u"label_FLS_SlideSpacing",
            default=u"Space betwee single slides (in px)",
        ),
    )


    FLS_StartIndex = schema.Choice(
        default=u"0",
        description=_(u'Index of the slide to display start, default value is 0'),  
        required=False,
        title=_(
            u"label_FLS_StartIndex",
            default=u"Index Start Slide",
        ),
        values= SLIDER_STEPS_FULL
    )

    FLS_ParkingPosition = schema.TextLine(
        description=_(u'The offset position to park slide (this options applys only when slideshow disabled)'),  
        required=False,
        title=_(
            u"label_FLS_ParkingPosition",
            default=u"Slide Parking Position ",
        ),
    )


class IBulletPointNavigator(Interface):
    """contains our BulletPointNavigator fields"""

    FLS_BulletNavigator = schema.Bool(
        default=True,
        required=False,
        title=_(
            u"label_FLS_BulletNavigator",
            default=u"Activate BulletPointNavigator",
        ),
        description=_(
            u'The activated Navigator adds a BulletPoint Navigation to the Slider'
        ),
    )

    BNO_BulletStyle = schema.Choice(
        default=u'bullet01',
        description=_(u'Choose a style for the Bullet Point Navigator'),
        required=False,
        title=_(u'Bullet Point Style'),
        values= [   "bullet01", "bullet02", "bullet03", "bullet05", "bullet06", 
                    "bullet07", "bullet09", "bullet10", "bullet11", "bullet12", 
                    "bullet13", "bullet14", "bullet16", "bullet17", "bullet18",  
                    "bullet20", "bullet21"
                ]
    )

    BNO_ChanceToShow = schema.Choice(
        default=u'2',
        description=_(u'[Required] 0: Never, 1: Mouse Over, 2: Always'),
        required=False,
        title=_(u'When to show Bullet Navigator?'),
        values= ["0", "1", "2"]
    )
    BNO_AutoCenter = schema.Choice(
        default=u'1',
        description=_(u'[Optional] Auto center navigator in parent container, 0: None, 1: Horizontal, 2: Vertical, 3: Both'),
        required=False,
        title=_(u'Auto Center?'),
        values= ["0", "1", "2", "3"]
    )
    BNO_Steps = schema.Choice(
        default=u'1',
        description=_(u'[Optional] Steps to go for each navigation request, default value is 1'),
        required=False,
        title=_(u'Bullet Navigator Steps'),
        values= SLIDER_STEPS
    )
    BNO_Lanes = schema.Choice(
        default=u'1',
        description=_(u'[Optional] Specify lanes to arrange items, default value is 1'),
        required=False,
        title=_(u'Bullet Navigator Lanes'),
        values= SLIDER_STEPS
    )
    BNO_Orientation = schema.Choice(
        default=u"1",
        required=False,
        title=_(
            u"label_BNO_Orientation",
            default=u"Orientation"),
        description=_(u'[Optional] The orientation of the navigator, 1 horizontal, 2 vertical, default value is 1'), 
        values=["1", "2"]
    )
    BNO_SpacingX = schema.TextLine(
        default=u'0',
        required=False,
        title=_(
            u'label_BNO_SpacingX',
            default=u'SpacingX'),
        description=_(u'[Optional] Horizontal space between each item in pixel, default value is 0')
    )
    BNO_SpacingY = schema.TextLine(
        default=u'0',
        required=False,
        title=_(
            u'label_BNO_SpacingY',
            default=u'SpacingY'),
        description=_(u'[Optional] Vertical space between each item in pixel, default value is 0')
    )

    BNO_genericTemplate =schema.Text(
        default=u"",
        description=PMF(
            u'help_BNO_genericTemplate',
            default=u'This template is auto-generated from the settings',
        ),
        required=False,
        title=PMF(u'label__BNO_genericTemplate', default=u'Generated BulletPointNavigator Template'),
        readonly=True
    )
    BNO_useCustomTemplate = schema.Bool(
        default=False,
        required=False,
        title=_(
            u"label_BNO_use_custom_template",
            default=u"Use customized Navigator Template.",
        ),
    )
    BNO_customTemplate =schema.Text(
        default=u"",
        description=PMF(
            u'help_BNO_customTemplate',
            default=u'This template can be adjusted',
        ),
        required=False,
        title=PMF(u'label__BNO_customTemplate', default=u'Custom Bullet Point Navigation'),
    )


class IArrowNavigator(Interface):
    """Arrow Navigation Options"""

    FLS_ArrowNavigator = schema.Bool(
        default= True,
        required= False,
        title= _(
            u"label_FLS_ArrowNavigator",
            default=u"Activate ArrowNavigator",
        ),
        description= _(
            u'The activated Navigator adds a Arrow Navigator (prev & next) to the Slider'
        ),
    )

    AN_ArrowStyle = schema.Choice(
        default=u'arrow01',
        description=_(u'Choose a style for the navigation arrows'),
        required=False,
        title=_(u'Arrow Style'),
        values= [   "arrow01", "arrow02", "arrow03", "arrow04", "arrow05", 
                    "arrow06", "arrow07", "arrow08", "arrow09", "arrow10", 
                    "arrow11", "arrow12", "arrow13", "arrow14", "arrow15",  
                    "arrow16", "arrow18", "arrow19", "arrow20", "arrow21"
                ]
    )

    AN_ChanceToShow = schema.Choice(
        default=u'2',
        description=_(u'0: Never, 1: Mouse Over, 2: Always'),
        required=False,
        title=_(u'When to show Arrow Navigator?'),
        values= ["0", "1", "2"]
    )

    AN_AutoCenter = schema.Choice(
        default=u'2',
        description=_(u'0 None, 1 Horizontal, 2 Vertical, 3 Both'),
        required=False,
        title=_(u'Auto center arrows in parent container?'),
        values= ["0", "1", "2", "3"]
    )

    AN_Steps = schema.Choice(
        default=u'1',
        description=_(u'[Optional] Steps to go for each navigation request, default value is 1'),
        required=False,
        title=_(u'Arrow Navigator Steps'),
        values= SLIDER_STEPS
    )

    AN_Scale = schema.Bool(
        default= True,
        required= False,
        title= _(
            u"label_AN_Scale",
            default=u"Scale Arrows?",
        ),
        description= _(
            u'Scales arrow navigator or not while slider scale.'
        ),
    )

    AN_genericTemplate =schema.Text(
        default=u"",
        description=PMF(
            u'help_FLS_genericTemplate',
            default=u'This template is auto-generated from the settings',
        ),
        required=False,
        title=PMF(u'label__FLS_genericTemplate', default=u'Generated ArrowNavigator Template'),
        readonly=True
    )

    AN_useCustomTemplate = schema.Bool(
        default=False,
        required=False,
        title=_(
            u"label_use_custom_template",
            default=u"Use customized Navigator Template.",
        ),
    )

    AN_customTemplate =schema.Text(
        default=u"",
        description=PMF(
            u'help_FLS_customTemplate',
            default=u'This template can be adjusted',
        ),
        required=False,
        title=PMF(u'label__FLS_customTemplate', default=u'Custom Arrow Navigation'),
    )


class IThumbnailNavigator(Interface):
    """Thumbnail Navigator Options"""

    FLS_ThumbnailNavigator = schema.Bool(
        default=True,
        required=False,
        title=_(
            u"label_FLS_ThumbnailNavigator",
            default=u"Activate Thumbnail Navigator",
        ),
        description=_(
            u'The activated Navigator adds a Thumbnail Navigation to the Slider'
        ),
    )

    TNO_ThumbnailStyle = schema.Choice(
        default=u'thumb01',
        description=_(u'Choose a style for the Thumbnail'),
        title=_(u'Thumbnail Style'),
        values= [   'thumb01', 'thumb02', 'thumb03', 'thumb04',
                    'thumb05', 'thumb06', 'thumb07', 'thumb08',
                    'thumb09', 'thumb010', 'thumb11', 'thumb12',
                ]
    )

    TNO_Loop =schema.Choice(
        default=u"1",
        required=False,
        title=_(
            u"label_TNO_Loop",
            default=u"Thumbnail Loop Behaviour",
        ),
        description=_(u'Enable loop(circular) of carousel or not, (0): stop, (1): loop, (2): rewind'),
        values= ["0", "1", "2"]
    )

    TNO_ChanceToShow = schema.Choice(
        default=u'2',
        description=_(u'[Required] 0: Never, 1: Mouse Over, 2: Always'),
        required=False,
        title=_(u'When to show Thumbnail Navigator?'),
        values= ["0", "1", "2"]
    )
    TNO_ActionMode = schema.Choice(
        default=u'1',
        description=_(u'(0): None, (1): act by click [default], (2): act by mouse hover, (3): both'),
        required=False,
        title=_(u'Action Mode?'),
        values= ["0", "1", "2", "3"]
    )
    TNO_AutoCenter = schema.Choice(
        default=u'1',
        description=_(u'[Optional] Auto center thumbnails in parent container, 0: None, 1: Horizontal, 2: Vertical, 3: Both'),
        required=False,
        title=_(u'Auto Center?'),
        values= ["0", "1", "2", "3"]
    )

    TNO_Lanes = schema.Choice(
        default=u'1',
        description=_(u'[Optional] Specify lanes to arrange thumbnails [default=1]'),
        required=False,
        title=_(u'Thumbnail Lanes'),
        values= SLIDER_STEPS
    )

    TNO_SpacingX = schema.TextLine(
        default=u'0',
        required=False,
        title=_(
            u'label_TNO_SpacingX',
            default=u'SpacingX'),
        description=_(u'[Optional] Horizontal space between each item in pixel, default value is 0')
    )

    TNO_SpacingY = schema.TextLine(
        default=u'0',
        required=False,
        title=_(
            u'label_TNO_SpacingY',
            default=u'SpacingY'),
        description=_(u'[Optional] Vertical space between each item in pixel, default value is 0')
    )

    TNO_DisplayPieces = schema.Choice(
        default=u'1',
        description=_(u'[Optional] Number of pieces to display [default=1]'),
        required=False,
        title=_(u'Display Pieces'),
        values= SLIDER_STEPS
    )

    TNO_ParkingPosition = schema.TextLine(
        description=_(u'The offset position to park thumbnail'),  
        required=False,
        title=_(
            u"label_TNO_ParkingPosition",
            default=u"Thumbnail Parking Position ",
        ),
    )

    TNO_Orientation = schema.Choice(
        default=u"1",
        required=False,
        title=_(
            u"label_BNO_Orientation",
            default=u"Orientation"),
        description=_(u'[Optional] The orientation of the navigator, 1 horizontal, 2 vertical, default value is 1'), 
        values=["1", "2"]
    )

    TNO_Scale = schema.Bool(
        default= True,
        required= False,
        title= _(
            u"label_TNO_Scale",
            default=u"Scale Thumbnails?",
        ),
        description= _(
            u'Scales thumbnail navigator or not while slider scale? [default=true]'
        ),
    )

    TNO_DisableDrag = schema.Bool(
        default= False,
        required= False,
        title= _(
            u"label_TNO_DisableDrag",
            default=u"Disable Drag?",
        ),
        description= _(
            u'Disable drag or not? [default=false]'
        ),
    )

    TNO_genericTemplate =schema.Text(
        default=u"",
        description=PMF(
            u'help_BNO_genericTemplate',
            default=u'This template is auto-generated from the settings',
        ),
        required=False,
        title=PMF(u'label__BNO_genericTemplate', default=u'Generated BulletPointNavigator Template'),
        readonly=True
    )

    TNO_useCustomTemplate = schema.Bool(
        default=False,
        required=False,
        title=_(
            u"label_TNO_use_custom_template",
            default=u"Use customized Navigator Template?",
        
        ),
    )

    TNO_customTemplate =schema.Text(
        default=u"",
        description=PMF(
            u'help_TNO_customTemplate',
            default=u'This template can be adjusted',
        ),
        required=False,
        title=PMF(u'label__TNO_customTemplate', default=u'Custom Thumbnail Navigation'),
    )


class ICaptionSlider(Interface):
    """Caption Slider Options"""

    FLS_CaptionSlider = schema.Bool(
        default=True,
        required=False,
        title=_(
            u"label_CaptionSlider",
            default=u"Activate Caption Slider",
        ),
        description=_(
            u'Use transitions for the text'
        ),
    )

    CS_CaptionTransitions =schema.TextLine(
        default=u"{$Duration:900,x:0.6,$Easing:{$Left:$JssorEasing$.$EaseInOutSine},$Opacity:2}",
        required=False,
        title=_(
            u"label_CS_transition",
            default=u"Caption Slider Transition Effects",
        ) ,
        description=_(u"Paste custom Transition Effects here")     
    )

    CS_PlayInMode = schema.Choice(
        default=u"1",
        description=_(u'(0): None (no play), (1): Chain (goes after main slide)[default], (3): Chain Flatten (goes after main slide and flatten all caption animations)'),  
        required=False,
        title=_(
            u"label_CS_PlayInMode",
            default=u"PlayInMode",
        ),
        values= ["0", "1", "3"]
    )

    CS_PlayOutMode = schema.Choice(
        default=u"1",
        description=_(u'(0): None (no play), (1): Chain (goes before main slide)[default], (3): Chain Flatten (goes before main slide and flatten all caption animations)'),  
        required=False,
        title=_(
            u"label_CS_PlayOutMode",
            default=u"PlayOutMode",
        ),
        values= ["0", "1", "3"]
    )

class IExtendedNavigation(Interface):
    """Configure drag behavior and arrow keys"""

    FLS_ArrowKeyNavigation = schema.Bool(
        default=True,
        required=False,
        title=_(
            u"label_FLS_ArrowKeyNavigation",
            default=u"Allows keyboard (arrow key) navigation or not",
        ),
    )
    
    FLS_DragOrientation = schema.Choice(
        default=u"1",
        required=False,
        title=_(
            u"label_FLS_DragOrientation",
            default=u"Slider Drag Orientation",
        ),
        description=_(u'Orientation to drag slide, 0 no drag, 1 horizental, 2 vertical, 3 either (Note that the $DragOrientation should be the same as $PlayOrientation when $DisplayPieces is greater than 1, or parking position is not 0)'),
        values= ["0", "1", "2", "3"]
    )

    FLS_MinDragOffsetToSlide = schema.TextLine(
        default=u"20",
        required=False,
        title=_(
            u"label_FLS_effect",
            default=u"MinDragOffsetToSlide",
        ) ,
        description=_(u"Minimum drag offset to trigger slide in px")     
    )


class IExpertConfig(Interface):
    """The slider expert configuration"""

    FLS_UISearchMode = schema.Choice(
        default=u"1",
        description=_(u'The way (0 parellel, 1 recursive, default value is 1) to search UI components (slides container, loading screen, navigator container, arrow navigator container, thumbnail navigator container etc).'),  
        required=False,
        title=_(
            u"label_FLS_UISearchMode",
            default=u"UISearchMode",
        ),
        values= ["0", "1"]
    )

    AN_Class = schema.TextLine(
        default=u'$JssorArrowNavigator$',
        required=True,
        title=_(
            u'label_AN_Class',
            default=u'Arrow Class'),
        description=_(u'Class to create arrow navigator instance. Default: $JssorArrowNavigator$')
    )

    SS_Class = schema.TextLine(
        default=u'$JssorSlideshowRunner$',
        required=True,
        title=_(
            u'label_SS_Class',
            default=u'SlideShow Class'),
        description=_(u'Class to create instance of slideshow.[default= $JssorSlideshowRunner$]')
    )

    CS_Class = schema.TextLine(
        default=u'$JssorCaptionSlider$',
        required=True,
        title=_(
            u'label_CS_Class',
            default=u'CaptionSlider Class'),
        description=_(u'Class to create instance to animate caption.[default= $JssorCaptionSlider$]')
    )

    TN_Class = schema.TextLine(
        default=u'$JssorThumbnailNavigator$',
        required=True,
        title=_(
            u'label_TN_Class',
            default=u'Thumbnail Navigator Class'),
        description=_(u'Class to create thumbnail navigator instance.[default= $JssorThumbnailNavigator$]')
    )

class ICustomCode(Interface):
    """enable custom javascripts and css"""

    use_custom_js = schema.Bool(
        default=False,
        required=False,
        title=_(
            u'label_use_custom_js',
            default=u'Use my custom Slider Javascript',
        ),
        description=u'For the ultimate tweak you can use a fully customized JavaScript if you wish. The generated Code is available for Copy&Paste ease the start.'
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

    featuredListingSliderCSS =schema.Text(
        default=u"",
        description=PMF(
            u'help_FLS_css',
            default=u'Custom CSS this carousel',
        ),
        required=False,
        title=PMF(u'label_featuredListingSliderCSS', default=u'Custom CSS styles'),
    )

    genericJS =schema.Text(
        default=u"",
        description=PMF(
            u'help_FLS_genJS',
            default=u'This Javascript Code is auto-generated from the settings',
        ),
        required=False,
        title=PMF(u'label__FLS_genJS', default=u'Generated Slider code'),
    )


class FormBaseGroup(group.Group):
    """Base groupt providing custom getContent for Annotations"""
    label = u''
    fields = None

    def getContent(self):
        # Default to sharing content with parent
        return self.__parent__.getContent()

class ItemProviderGroup(FormBaseGroup):
    """Item for the Slider Form Group"""
    label = u'Slider Contents'
    fields = field.Fields(IItemProvider)


class PlayerOptionsGroup(FormBaseGroup):
    """Player Options Form Group"""
    label = u'Player Options'
    fields = field.Fields(IPlayerOptions)


class ExtendedNavigationGroup(FormBaseGroup):
    """Extended Navigation Form Group"""
    label = u'Extended Navigation'
    fields = field.Fields(IExtendedNavigation)


class SlideConfigGroup(FormBaseGroup):
    """Slide Config Form Group"""
    label = u'Stage & Slide Settings'
    fields = field.Fields(ISlideConfig)


class BulletNavigatorGroup(FormBaseGroup):
    """BulletPointNavigator Form Group"""
    label = u'BulletPointNavigator Options'
    fields = field.Fields(IBulletPointNavigator)


class ArrowNavigatorGroup(FormBaseGroup):
    """ArrowNavigator Form Group"""
    label = u'Arrow Navigator [<] [>]'
    fields = field.Fields(IArrowNavigator)


class ThumbnailNavigatorGroup(FormBaseGroup):
    """ThumbnailNavigator Form Group"""
    label = u'Thumbnails'
    fields = field.Fields(IThumbnailNavigator)


class CaptionSliderGroup(FormBaseGroup):
    """CaptionSlider Form Group"""
    label = u'Caption Settings'
    fields = field.Fields(ICaptionSlider)


class ExpertGroup(FormBaseGroup):
    """Expert Config Form Group"""
    label = u'Geek Settings'
    fields = field.Fields(IExpertConfig)


class CustomCodeGroup(FormBaseGroup):
    """CustomCode Form Group"""
    label = u'Customize it! '
    fields = field.Fields(ICustomCode)


class CollectionViewletConfiguration(group.GroupForm, form.Form):
    """HeaderPlugin Configuration Form."""

    fields = field.Fields(ICollectionViewletConfiguration)
    groups = (ItemProviderGroup, PlayerOptionsGroup, SlideConfigGroup, BulletNavigatorGroup, ArrowNavigatorGroup, ThumbnailNavigatorGroup, CaptionSliderGroup, ExtendedNavigationGroup, ExpertGroup, CustomCodeGroup)

    ignoreContext = False

    label = _(u"Configure your PS Slider.")
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

    def generatedSliderScript(self, data):
        """generates the SliderScript from the configuration"""

        #generalOptions = self.__generalSliderOptions
        sliderOptions = self.__configuredOptions(data)
        initiate_code = self.__FLSInitCode

        #build the FLS Script
        if sliderOptions is not None and initiate_code is not None:
            genericScript="<script type='text/javascript'>$(document).ready(function($) { %s %s });</script>"%(sliderOptions, initiate_code)
            return genericScript
        else:
            return None


    @property
    def getStageNames(self):
        """Delivers a dict containing the ids for the slider stage"""
        key = self.getConfigurationKey
        stage_dict= {}

        if key==CONFIGURATION_KEY_ABOVE:
            #top slider
            stage_dict['wrapper']='#fls-top-wrapper'
            stage_dict['slides']='#fls-top-wrapper .fls-slides'
            stage_dict['stageid']='#slider1_container'
            stage_dict['id']='slider1_container'
            stage_dict['js_name']='jssor_slider_top'

            return stage_dict

        elif key==CONFIGURATION_KEY_BELOW:
            #bottom slider
            stage_dict['wrapper']='#fls-bottom-wrapper'
            stage_dict['slides']='#fls-bottom-wrapper .fls-slides'
            stage_dict['stageid']='#slider2_container'
            stage_dict['id']='slider2_container'
            stage_dict['js_name']='jssor_slider_bottom'

            return stage_dict

        elif key == CONFIGURATION_KEY:
            #no FLS?
            return None
        else:
            return None

    @property
    def __generalSliderOptions(self):
        """returns a string with the general Slider options"""
        # empty for now, with extended Config useful
        script=''
        return script

    def __BulletPointNavigatorOptions(self, data):
        """returns the BulletPoint Navi Options or empty string"""
        BPN = data.get('FLS_BulletNavigator', True)
        if BPN is True:
            """Build BulletPoint Config together"""
            BPN_options = "$Class: $JssorBulletNavigator$, "
            BPN_options += "$ChanceToShow: %s, "%(data.get('BNO_ChanceToShow', 2))
            BPN_options += "$AutoCenter: %s, "%(data.get('BNO_AutoCenter', 1))
            BPN_options += "$Lanes: %s, "%(data.get('BNO_Lanes', 1))
            BPN_options += "$Steps: %s, "%(data.get('BNO_Steps', 1))
            BPN_options += "$Orientation: %s, "%(data.get('BNO_Orientation', 1))
            BPN_options += "$SpacingX: %s, "%(data.get('BNO_SpacingX', 0))
            BPN_options += "$SpacingY: %s, "%(data.get('BNO_SpacingY', 0))
            #wrap the BulletNavigatorOptions
            BPN_options = "$BulletNavigatorOptions: { " + BPN_options + "}, "
            return BPN_options
        else:
            return ''

    def __ArrowNavigatorOptions(self, data):
        """get string of arrow navigation options"""

        AN_options = ''
        AN = data.get('FLS_ArrowNavigator', True)
        if AN is True:
            #Build Arrow Navi Config together
            AN_options += "$Class: %s, "%(data.get('AN_Class', '$JssorArrowNavigator$'))
            AN_options += "$ChanceToShow: %s, "%(data.get('AN_ChanceToShow', 2))
            AN_options += "$AutoCenter: %s, "%(data.get('AN_AutoCenter', 2))
            AN_options += "$Steps: %s, "%(data.get('AN_Steps', 1))
            if data.get('AN_Scale', True):
                AN_options += "$Scale: true "
            else:
                AN_options += "$Scale: false "
            #wrap the ArrowNavigatorOptions
            AN_options = "$ArrowNavigatorOptions: { " + AN_options + "}, "

            return AN_options
        else:
            return False

    def __ThumbnailNavigatorOptions(self, data):
        """get string of thumbnail navigation options"""

        TN_options = ''
        TN = data.get('FLS_ThumbnailNavigator', True)
        if TN is True:
            #Build Thumbnail Config
            TN_options += "$Class: %s, "%(data.get('TN_Class', '$JssorThumbnailNavigator$'))
            TN_options += "$Loop: %s, "%(data.get('TNO_Loop', 1))
            TN_options += "$ActionMode: %s, "%(data.get('TNO_ActionMode', 1))
            TN_options += "$AutoCenter: %s, "%(data.get('TNO_AutoCenter', 2))
            TN_options += "$Lanes: %s, "%(data.get('TNO_Lanes',1))
            TN_options += "$ChanceToShow: %s, "%(data.get('TNO_ChanceToShow', 2))
            TN_options += "$SpacingX: %s, "%(data.get('TNO_SpacingX', 0))
            TN_options += "$SpacingY: %s, "%(data.get('TNO_SpacingY', 0))
            TN_options += "$DisplayPieces: %s,"%(data.get('TNO_DisplayPieces',1))
            TN_options += "$ParkingPosition: %s,"%(data.get('TNO_ParkingPosition',0))
            TN_options += "$Orientation: %s,"%(data.get('TNO_Orientation',1))

            if data.get('TNO_Scale', True):
                TN_options += "$Scale: true, "
            else:
                TN_options += "$Scale: false, "

            if data.get('TNO_DisableDrag', False):
                TN_options += "$DisableDrag: true, "
            
            #wrap the ThumbnailNavigatorOptions
            TN_options = "$ThumbnailNavigatorOptions: { " + TN_options + "}, "

            return TN_options
        else:
            return ''

    def __SlideshowOptions(self, data):
        """get string of Slideshow options"""

        SS_options = ''
        SS = data.get('FLS_SlideShow', False)

        if SS is True:
            #Build BulletPoint Config together
            SS_options = "$Class: %s, "%(data.get('SS_Class', '$JssorSlideshowRunner$'))
            SS_options += "$Transitions: [%s], "%(data.get('SS_Transitions', '{$Duration:1000,$Cols:8,$Clip:1}'))
            SS_options += "$TransitionsOrder: %s, "%(data.get('SS_TransitionsOrder', '1'))
            
            if data.get('SS_ShowLink', True):
                SS_options += "$ShowLink: true "
            else:
                SS_options += "$ShowLink: false "
        
            #wrap the SlideshowOptions
            SS_options = "$SlideshowOptions: { " + SS_options + "}, "

        return SS_options

    def __CaptionSliderOptions(self, data):
        """get string of CaptionSlider options"""

        CS_options = ''
        CS = data.get('FLS_CaptionSlider', False)

        if CS is True:
            #Build Config together
            CS_options = "$Class: %s, "%(data.get('CS_Class', '$JssorCaptionSlider$'))
            CS_options += "$CaptionTransitions: [%s], "%(data.get('CS_CaptionTransitions', '{$Duration:900,x:0.6,$Easing:{$Left:$JssorEasing$.$EaseInOutSine},$Opacity:2}'))
            CS_options += "$PlayInMode: %s, "%(data.get('CS_PlayInMode', '1'))
            CS_options += "$PlayOutMode: %s, "%(data.get('CS_PlayOutMode', '1'))
            
            #wrap the CaptionSlider Options
            CS_options = "$CaptionSliderOptions: { " + CS_options + "}, "

        return CS_options
        
    def __generateANTemplate(self, data):
        """generate the template for the arrows"""    
        return ARROW_STYLE[data.get('AN_ArrowStyle', 'arrow01')]

    def __generateBNTemplate(self, data):
        """generate the template for the bullet points"""    
        return BULLET_STYLE[data.get('BNO_BulletStyle', 'bullet01')]

    def __configuredOptions(self, data):
        """returns a string with the options from the configuration"""
        #check for autoplay

        bool_ap = data.get('FLS_autoplay', True)
        if bool_ap is True:
            autoplay="$AutoPlay: true, "
            # get the other AutoPlay options
            autoplay += "$AutoPlaySteps: %s, "%(data.get('FLS_AutoPlaySteps', u'1'))
            autoplay += "$AutoPlayInterval: %s, "%(data.get('FLS_AutoPlayInterval', u'6000'))
            autoplay += "$PauseOnHover: %s, "%(data.get('FLS_PauseOnHover', u'3'))

        else:
            autoplay="$AutoPlay: false, "
        #general Slider behavior
        sliderbehavior  = "$SlideDuration: %s, "%(data.get('FLS_SlideDuration', u'500'))
        sliderbehavior += "$FillMode: %s, "%(data.get('FLS_FillMode', u'5'))
        sliderbehavior += "$Loop: %s, "%(data.get('FLS_Loop', u'1'))
        sliderbehavior += "$DisplayPieces: %s, "%(data.get('FLS_DisplayPieces', u'1'))
        # "translate" python bool to JS code
        if data.get('FLS_ArrowKeyNavigation', True):
            akn="true"
        else:
            akn="false"
        sliderbehavior += "$ArrowKeyNavigation: %s, "%(akn)
        sliderbehavior += "$PlayOrientation: %s, "%(data.get('FLS_PlayOrientation', u'1'))
        sliderbehavior += "$DragOrientation: %s, "%(data.get('FLS_DragOrientation', u'1'))
        sliderbehavior += "$MinDragOffsetToSlide: %s, "%(data.get('FLS_MinDragOffsetToSlide', u'20'))
        sliderbehavior += "$UISearchMode: %s, "%(data.get('FLS_UISearchMode', u'1'))

        #slide options
        slideoptions = ""
        slideheight = data.get('FLS_SlideHeight', None)
        if slideheight is not None:
            slideoptions += "$SlideHeight: %s, "%(slideheight)

        slidewidth = data.get('FLS_SlideWidth', None)
        if slidewidth is not None:
            slideoptions += "$SlideWidth: %s, "%(slidewidth)

        slidespacing = data.get('FLS_SlideSpacing', None)
        if slidespacing is not None:
            slideoptions += "$SlideSpacing: %s, "%(slidespacing)

        parkingposition = data.get('FLS_ParkingPosition', None)
        if parkingposition is not None:
            slideoptions += "$ParkingPosition: %s, "%(parkingposition) 

        slideoptions += "$StartIndex: %s, "%(data.get('FLS_StartIndex', u'0'))

        # BulletPoint Navigation
        BPN = self.__BulletPointNavigatorOptions(data)    
        #Arrow Navigator
        AN = self.__ArrowNavigatorOptions(data)
        if AN is False:
            AN = ''

        # Slideshow Options
        SS = self.__SlideshowOptions(data)
        # Caption Transitions
        CT = self.__CaptionSliderOptions(data)

        # putting all options together
        all_options = autoplay + sliderbehavior + slideoptions + BPN + AN + SS + CT
        options ="var options={%s};"%(all_options)
        return options

    @property    
    def __FLSInitCode(self):
        """return string with the initiation code"""
        stage_dict = self.getStageNames;

        if stage_dict is None:
            return None
        else:
            script="try{";
            #do the resizing
            script += " resize2pixel('%s');"%(stage_dict['wrapper'])
            script += " resize2pixel('%s');"%(stage_dict['slides'])
            script += " resize2pixel('%s');"%(stage_dict['stageid'])
            
            #define the slider
            script += " var %s = new $JssorSlider$('%s', options);"%(stage_dict['js_name'], stage_dict['id'])
            #catch JS Errors
            script +=" } catch(error){console.log(err);}"

            return script


    @button.buttonAndHandler(_(u'Save'))
    def handle_save(self, action):
        data, errors = self.extractData()
        if not errors:
            try:
                data['genericJS']= self.generatedSliderScript(data)
                data['AN_genericTemplate']= self.__generateANTemplate(data)
                data['BNO_genericTemplate']= self.__generateBNTemplate(data)
    
            except(Exception):
                import pdb
                pdb.set_trace()
                self.context.plone_utils.addPortalMessage("There was a problem with the script generation", 'warning')
               
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
    GROUP_INTERFACES = (ICollectionViewletConfiguration, IItemProvider, IPlayerOptions, ISlideConfig, IBulletPointNavigator, IExtendedNavigation, IExpertConfig, ICustomCode)


    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        msg_type = 'info'

        if ICollectionViewlet.providedBy(self.context):
            # Deactivate.
            noLongerProvides(self.context, ICollectionViewlet)
            # we need to REMOVE all custom group interfaces from our context object
            for ginterface in self.GROUP_INTERFACES:
                if ginterface.providedBy(self.context):
                    noLongerProvides(self.context, ginterface)

            self.context.reindexObject(idxs=['object_provides', ])
            msg = _(u"Collection viewlet deactivated.")
        elif IPossibleCollectionViewlet.providedBy(self.context):
            alsoProvides(self.context, ICollectionViewlet)

            # we need to add all missing custom group interfaces to our context object
            for ginterface in self.GROUP_INTERFACES:
                if not ginterface.providedBy(self.context):
                    alsoProvides(self.context, ginterface) 

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
