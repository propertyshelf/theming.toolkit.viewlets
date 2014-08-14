# -*- coding: utf-8 -*-
"""Collection viewlets that render f.e. a carousel/slideshow"""

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
SLIDER_STEPS = ["1", "2", "3", "4", "5","6","7", "8", "9", "10"]
SLIDER_STEPS_FULL = ["0", "1", "2", "3", "4", "5","6","7", "8", "9", "10"]

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


class ICollectionViewletConfiguration(Interface):
    """FLS Configuration Form."""

    viewlet_title = schema.TextLine(
        required=False,
        title=_(
            u'Carousel Title',
            default=u'Featured Listings',
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

    featuredListingSlider_ItemList = schema.TextLine(
        required=True,
        title=_(
            u'Item List to show',
            default=u'FeaturedListingSlider Item List',
        ),
    )

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
        title=_(u'Bullet Navigator Steps?'),
        values= SLIDER_STEPS
    )
    BNO_Lanes = schema.Choice(
        default=u'1',
        description=_(u'[Optional] Specify lanes to arrange items, default value is 1'),
        required=False,
        title=_(u'Bullet Navigator Lanes'),
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
            u"label_BNO_Lanes",
            default=u"Lanes"),
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
            u'Choose the size of the image in rendered in the List'
        ),
        required=False,
        title=_(u'Slider Image size'),
        values= MLS_IMAGE_SIZES
    )

    featuredListingSlider_height =schema.TextLine(
        default=u"350px",
        required=True,
        title=_(
            u"label_FLS_height",
            default=u"Carousel Stage Height",
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
            default=u"Carousel Stage Width",
        ),
        description=_(u'Set the width of the slider stage box (default:100%). The value can be entered with as css compatible unit (px, %, em, ...).'),  
    )

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

    FLS_ArrowKeyNavigation = schema.Bool(
        default=True,
        required=False,
        title=_(
            u"label_FLS_ArrowKeyNavigation",
            default=u"Allows keyboard (arrow key) navigation or not",
        ),
    )


    FLS_SlideEasing =schema.TextLine(
        default=u"",
        required=False,
        title=_(
            u"label_FLS_effect",
            default=u"Slide Easing Effect",
        ) ,
        description=_(u"Specifies easing for right to left animation")     
    )

    # options for (single) Slide inside SlidesContainer
    FLS_DisplayPieces = schema.Choice(
        default=u"1",
        description=_(u'Number of pieces to display (the slideshow would be disabled if the value is set to greater than 1)'),  
        required=False,
        title=_(
            u"label_FLS_DisplayPieces",
            default=u"Display Pieces",
        ),
        values= SLIDER_STEPS
    )

    FLS_SlideWidth = schema.TextLine(
        description=_(u'Width of every slide in pixels, default value is width of "slides" container'),  
        required=False,
        title=_(
            u"label_FLS_SlideWidth",
            default=u"Width of a single slide (in px)",
        ),
    )

    FLS_SlideHeight = schema.TextLine(
        description=_(u"Height of every slide in pixels, default value is height of 'slides' container"),  
        required=False,
        title=_(
            u"label_FLS_SlideHeight",
            default=u"height of a single slide (in px)",
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
        description=_(u'Index of slide to display when initialize, default value is 0'),  
        required=False,
        title=_(
            u"label_FLS_StartIndex",
            default=u"Slider Start Index",
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

    def generatedSliderScript(self, data):
        """generates the SliderScript from the configuration"""

        generalOptions = self.__generalSliderOptions
        sliderOptions = self.__configuredOptions(data)
        initiate_code = self.__FLSInitCode

        #build the FLS Script
        if generalOptions is not None and sliderOptions is not None and initiate_code is not None:
            genericScript="<script type='text/javascript'>$(window).load(function($) { %s %s %s });</script>"%(generalOptions, sliderOptions, initiate_code)
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
        easing = data.get('FLS_SlideEasing', None)
        #set custom easing function if exist
        if easing is not None: 
            sliderbehavior += "$SlideEasing: %s, "%(easing)
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

        #putting all options together
        all_options = autoplay + sliderbehavior + slideoptions
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
            except(Exception):
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
