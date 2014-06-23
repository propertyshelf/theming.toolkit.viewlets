# -*- coding: utf-8 -*-
"""Collection viewlets that render a carousel/slideshow"""

from plone.app.layout.viewlets.common import ViewletBase
from plone.memoize.view import memoize

from Products.CMFPlone import PloneMessageFactory as PMF

from z3c.form import form,field, button
from zope import schema
from zope.annotation.interfaces import IAnnotations
from zope.interface import Interface, alsoProvides, noLongerProvides
from zope.traversing.browser.absoluteurl import absoluteURL

#local import
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

class IPossibleCollectionViewlet(Interface):
    """Marker interface for possible Header Collection viewlet."""

class ICollectionViewlet(IToolkitBaseViewlets):
    """Marker interface for Collection viewlet."""


class FeaturedListingCollectionViewlet(ViewletBase):
    """Show Collection viewlet in header"""

    @property
    def available(self):
        
        return IPossibleCollectionViewlet.providedBy(self.context) and \
            not ICollectionViewlet.providedBy(self.context)

    @property
    def config(self):
        """Get view configuration data from annotations."""
        annotations = IAnnotations(self.context)
        key = self.getConfigurationKey
        return annotations.get(key, {})

    @property
    def get_code(self):
        """Get Plugin Code"""
        

    @property
    def get_title(self):
        """Get Plugin Code"""
        annotations = IAnnotations(self.context)
        key = self.getConfigurationKey
        config = annotations.get(key, {})
        return config.get('viewlet_title', u'')

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
    

    def update(self):
        """
        if IViewView.providedBy(self.__parent__):
            alsoProvides(self, IViewView)
        """
        super(FeaturedListingCollectionViewlet, self).update()


    def getProviders(self):
        """Get Listing Provider"""
        annotations = IAnnotations(self.context)
        key = self.getConfigurationKey
        config = annotations.get(key, {})
        field = config.get('featuredListingSlider_ItemList', None)
        
        if field is None:
            return None

        try:
            return field.get(self.context)
        except:
            return None

    def results(self, provider):
        results = []
        if provider is not None:
            # by default we assume that only Collections are addable
            # as a carousel provider

            # It doesn't make sense to show *all* objects from a collection
            # - some of them might return hundreeds of objects
            if ICollection.providedBy(provider):
                res = provider.results()
                return res
            return provider.queryCatalog()
        return results

    

    def get_tile(self, obj):
        # note to myself
        # When adapter is uesd this means we check whether obj has any special
        # instructions about how to be handled in defined view or interface
        # for multi adapter the same is true except more object than just the
        # obj are check for instructions
        #have to use traverse to make zpt security work
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
    """Header Plugins Configuration Form."""

    viewlet_title = schema.TextLine(
        required=False,
        title=_(
            u'Viewlet Title',
            default=u'Viewlet Title',
        ),
    )
 
    featuredListingSlider_ItemList =schema.TextLine(
        default=u"",
        required=False,
        title=_(
            u"label_FLS_offset",
            default=u"Add a list of Listings",
        )      
    )

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
            default=u"Slider Animation featuredListingSlider_duration",
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

    use_custom_js = schema.Bool(
        default=False,
        required=False,
        title=_(
            u"label_use_custom_js",
            default=u"Use local Slider Javascript",
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

    label = _(u"Configure your MLS FeaturedListingSlider'")
    description = _(
        u"Adjust the slider settings."
    )

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
        
        
    def getContent(self):
        annotations = IAnnotations(self.context)
        key = self.getConfigurationKey
        return annotations.get(key,
                               annotations.setdefault(key, {}))

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
