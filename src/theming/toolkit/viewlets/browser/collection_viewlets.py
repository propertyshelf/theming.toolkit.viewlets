# -*- coding: utf-8 -*-
"""Collection viewlets that render a carousel/slideshow"""

from AccessControl import SecurityManagement
from Products.ATContentTypes.permission import ChangeTopics
#zope imports
from plone.app.form.widgets.uberselectionwidget import UberSelectionWidget
from plone.app.layout.viewlets.common import ViewletBase
from plone.app.layout.globals.interfaces import IViewView
from plone.memoize.view import memoize

from plone.app.vocabularies.catalog import SearchableTextSourceBinder
from Products.ATContentTypes.interface import IATTopic

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

CONFIGURATION_KEY = 'theming.toolkit.viewlets.collection'

class IPossibleCollectionViewlet(Interface):
    """Marker interface for possible Header Collection viewlet."""

class ICollectionViewlet(IToolkitBaseViewlets):
    """Marker interface for Collection viewlet."""


class HeaderCollectionViewlet(ViewletBase):
    """Show Collection viewlet in header"""

    @property
    def available(self):
        
        return IPossibleCollectionViewlet.providedBy(self.context) and \
            not ICollectionViewlet.providedBy(self.context)

    @property
    def config(self):
        """Get view configuration data from annotations."""
        annotations = IAnnotations(self.context)
        return annotations.get(CONFIGURATION_KEY, {})

    @property
    def get_code(self):
        """Get Plugin Code"""
        

    @property
    def get_title(self):
        """Get Plugin Code"""
        annotations = IAnnotations(self.context)
        config = annotations.get(CONFIGURATION_KEY, {})
        return config.get('viewlet_title', u'')
    

    def update(self):
        if IViewView.providedBy(self.__parent__):
            alsoProvides(self, IViewView)
        super(HeaderCollectionViewlet, self).update()

    def getProviders(self):
        annotations = IAnnotations(self.context)
        config = annotations.get(CONFIGURATION_KEY, {})
        field = config.get('viewlet_collection', None)

        if field is None:
            return None
        return field.get(self.context)

    def results(self, provider):
        results = []
        if provider is not None:
            # by default we assume that only Collections are addable
            # as a carousel provider

            # It doesn't make sense to show *all* objects from a collection
            # - some of them might return hundreeds of objects
            if ICollection.providedBy(provider):
                res = provider.results(b_size=20)
                return res
            return provider.queryCatalog()[:7]
        return results

    def canSeeEditLink(self, provider):
        smanager = SecurityManagement.getSecurityManager()
        return smanager.checkPermission(ChangeTopics, provider)

    def editCarouselLink(self, provider):
        if provider is not None:
            if ICollection.providedBy(provider):
                return provider.absolute_url() + '/edit'
            return provider.absolute_url() + '/criterion_edit_form'
        return None

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

    viewlet_collection = schema.Choice(
        title=_(u"Target collection"),
        description=_(u"Find the collection which provides the items to list"),
        required=False,
        source=SearchableTextSourceBinder({
            'object_provides' : IATTopic.__identifier__},
            default_query='path:')
        )


class CollectionViewletConfiguration(form.Form):
    """HeaderPlugin Configuration Form."""

    fields = field.Fields(ICollectionViewletConfiguration)
    fields['viewlet_collection'].custom_widget = UberSelectionWidget
    ignoreContext = True

    label = _(u"edit 'Header Carousel'")
    description = _(
        u"Adjust the Carousel in this viewlet."
    )
        
    def getContent(self):
        annotations = IAnnotations(self.context)
        return annotations.get(CONFIGURATION_KEY,
                               annotations.setdefault(CONFIGURATION_KEY, {}))

    @button.buttonAndHandler(_(u'Save'))
    def handle_save(self, action):
        data, errors = self.extractData()
        if not errors:
            annotations = IAnnotations(self.context)
            annotations[CONFIGURATION_KEY] = data
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
