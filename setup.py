from setuptools import setup, find_packages
import os

version = '1.0'

setup(name='toolkit.viewlets',
      version=version,
      description="A product that allows to activate a set of viewlets for Plone content items.",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from
      # http://pypi.python.org/pypi?:action=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        ],
      keywords='',
      author='Jens Krause',
      author_email='jens@propertyshelf.com',
      url='http://propertyshelf.com',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['toolkit'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          # -*- Extra requirements: -*-
      ],
      extras_require={
             'test': ['plone.app.testing',]
      },
      entry_points="""
      # -*- Entry points: -*-

      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
