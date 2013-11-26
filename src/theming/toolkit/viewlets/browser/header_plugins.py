# -*- coding: utf-8 -*-
"""Editable Header Plugins"""

#zope imports
from plone.app.layout.viewlets.common import ViewletBase
from plone.app.layout.navigation.interfaces import INavigationRoot
#from plone.directives import form
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

CONFIGURATION_KEY = 'theming.toolkit.viewlets.headerplugins'

class IPossibleHeaderPlugins(Interface):
    """Marker interface for possible HeaderPlugin viewlet."""

class IHeaderPlugins(IToolkitBaseViewlets):
    """Marker interface for RecentListings viewlet."""


class HeaderPluginsViewlet(ViewletBase):
    """Show Header plugins."""

    @property
    def available(self):
        return IPossibleHeaderPlugins.providedBy(self.context) and \
            IHeaderPlugins.providedBy(self.context)

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
        return config.get('plugin_code', u'')

    @property
    def get_title(self):
        """Get Plugin Code"""
        annotations = IAnnotations(self.context)
        config = annotations.get(CONFIGURATION_KEY, {})
        return config.get('viewlet_title', u'')

    def update(self):
        """Prepare view related data."""
        super(HeaderPluginsViewlet, self).update()

    @memoize
    def view_url(self):
        """Generate view url."""
        if not self.context_state.is_view_template():
            return self.context_state.current_base_url()
        else:
            return absoluteURL(self.context, self.request) + '/'


class IHeaderPluginsConfiguration(Interface):
    """Header Plugins Configuration Form."""

    viewlet_title = schema.TextLine(
        required=False,
        title=_(
            u'Plugin Title',
            default=u'Plugin Title',
        ),
    )

    plugin_code =schema.Text(
        description=PMF(
            u'help_plugin_code',
            default=u'Please enter the Plugin Code.',
        ),
        required=False,
        title=PMF(u'label_plugin_code', default=u'Plugin Code'),
    )


class HeaderPluginsConfiguration(form.Form):
    """HeaderPlugin Configuration Form."""

    fields = field.Fields(IHeaderPluginsConfiguration)
    label = _(u"edit 'HeaderPlugins'")
    description = _(
        u"Adjust the Header Plugins in this viewlet."
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


class HeaderPluginsStatus(object):
    """Return activation/deactivation status of HeaderPlugins viewlet."""

    def __init__(self, context, request):
        self.context = context
        self.request = request

    @property
    def can_activate(self):
        return IPossibleHeaderPlugins.providedBy(self.context) and \
            not IHeaderPlugins.providedBy(self.context)

    @property
    def active(self):
        return IHeaderPlugins.providedBy(self.context)


class HeaderPluginsToggle(object):
    """Toggle HeaderPlugins viewlet for the current context."""

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        msg_type = 'info'

        if IHeaderPlugins.providedBy(self.context):
            # Deactivate RecentListings viewlet.
            noLongerProvides(self.context, IHeaderPlugins)
            self.context.reindexObject(idxs=['object_provides', ])
            msg = _(u"'HeaderPlugins' viewlet deactivated.")
        elif IPossibleHeaderPlugins.providedBy(self.context):
            alsoProvides(self.context, IHeaderPlugins)
            self.context.reindexObject(idxs=['object_provides', ])
            msg = _(u"'HeaderPlugins' viewlet activated.")
        else:
            msg = _(
                u"The 'HeaderPlugins' viewlet does't work with this content "
                u"type. Add 'IPossibleHeaderPlugins' to the provided "
                u"interfaces to enable this feature."
            )
            msg_type = 'error'

        self.context.plone_utils.addPortalMessage(msg, msg_type)
        self.request.response.redirect(self.context.absolute_url())