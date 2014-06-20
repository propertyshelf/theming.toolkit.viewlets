# -*- coding: utf-8 -*-
"""Interface definitions."""

# zope imports
from plone.theme.interfaces import IDefaultPloneLayer
from zope.interface import Interface


class IToolkitViewlets(IDefaultPloneLayer):
    """Marker interface that defines a Zope 3 browser layer."""


class IToolkitBaseViewlets(Interface):
    """Marker interface for all toolkit viewlets"""

class IToolkitFeaturedListingSlider(Interface):
    """Marker interface Featured Listing Slider contents"""
