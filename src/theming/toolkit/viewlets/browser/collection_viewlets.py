# -*- coding: utf-8 -*-
"""Collection viewlets that render a carousel/slideshow"""


#zope imports
from plone.app.layout.viewlets.common import ViewletBase
from plone.memoize.view import memoize

from plone.app.vocabularies.catalog import SearchableTextSourceBinder

from z3c.form import form,field, button
from zope import schema
from zope.annotation.interfaces import IAnnotations
from zope.interface import Interface, alsoProvides, noLongerProvides
from zope.traversing.browser.absoluteurl import absoluteURL

#local import
from theming.toolkit.viewlets.browser.interfaces import IToolkitBaseViewlets
from theming.toolkit.viewlets.i18n import _

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
            
       # return IPossibleCollectionViewlet.providedBy(self.context)

    @property
    def config(self):
        """Get view configuration data from annotations."""
        annotations = IAnnotations(self.context)
        return annotations.get(CONFIGURATION_KEY, {})

    @property
    def get_code(self):
        """Get Plugin Code"""
        annotations = IAnnotations(self.context)
        config = annotations.get(CONFIGURATION_KEY, {})
        return config.get('viewlet_collection', u'')

    @property
    def get_title(self):
        """Get Plugin Code"""
        annotations = IAnnotations(self.context)
        config = annotations.get(CONFIGURATION_KEY, {})
        return config.get('viewlet_title', u'')

    def update(self):
        """Prepare view related data."""
        super(HeaderCollectionViewlet, self).update()

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
        description=_(
            u'Find the Collection providing the content'
        ),
        required=False,
        source=SearchableTextSourceBinder({
            'object_provides': 'plone.app.collection.interfaces.ICollection',
        }, 
        default_query='path:',
        ),
        title=_(u'Content Collection'),
    )


class CollectionViewletConfiguration(form.Form):
    """HeaderPlugin Configuration Form."""

    fields = field.Fields(ICollectionViewletConfiguration)
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
