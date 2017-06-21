# -*- coding: utf-8 -*-
"""Installer for the collective.documentgenerator package."""

from setuptools import find_packages
from setuptools import setup


long_description = (
    open('docs/README.rst').read()
    + '\n\n' +
    'Contributors\n'
    '============\n'
    + '\n\n' +
    open('docs/CONTRIBUTORS.rst').read()
    + '\n\n' +
    open('docs/CHANGES.rst').read()
    + '\n\n')


setup(
    name='collective.documentgenerator',
    version='2.0.0',
    description="Desktop document generation (.odt, .pdf, .doc, ...) based on appy framework (http://appyframework.org) and OpenOffice/LibreOffice",
    long_description=long_description,
    # Get more from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: 4.3",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
    ],
    keywords='plone document generation generator odt word pdf libreoffice template',
    author='Simon Delcourt',
    author_email='simon.delcourt@imio.be',
    url='http://pypi.python.org/pypi/collective.documentgenerator',
    license='GPL',
    packages=find_packages('src', exclude=['ez_setup']),
    namespace_packages=['collective'],
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'appy',
        'beautifulsoup4',
        'collective.behavior.talcondition',
        'collective.excelexport',
        'collective.z3cform.datagridfield',
        'imio.migrator',
        'plone.api>=1.3.3',
        'plone.app.dexterity',
        'setuptools',
        # fix about orderedselect
        'z3c.form>=3.2.4',
    ],
    extras_require={
        'test': [
            'plone.app.robotframework',
            'plone.app.testing',
        ],
    },
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    """,
)
