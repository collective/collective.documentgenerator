# -*- coding: utf-8 -*-
"""Installer for the collective.documentgenerator package."""

from setuptools import find_packages
from setuptools import setup


long_description = (
    open('README.rst').read() + '\n\n' + open('CHANGES.rst').read() + '\n\n')


setup(
    name='collective.documentgenerator',
    version='3.23',
    description="Desktop document generation (.odt, .pdf, .doc, ...) based on appy framework (http://appyframework.org) and OpenOffice/LibreOffice",
    long_description=long_description,
    # Get more from https://pypi.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: 4.3",
        "Framework :: Plone :: 5.0",
        "Framework :: Plone :: 5.1",
        "Framework :: Plone :: Addon",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
    ],
    keywords='plone document generation generator odt word pdf libreoffice template',
    author='Simon Delcourt',
    author_email='simon.delcourt@imio.be',
    url='https://pypi.org/project/collective.documentgenerator',
    license='GPL',
    packages=find_packages('src', exclude=['ez_setup']),
    namespace_packages=['collective'],
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'appy>=1.0.4',
        'beautifulsoup4',
        'collective.behavior.talcondition',
        'collective.excelexport',
        'collective.z3cform.datagridfield',
        'future>=0.14.0',
        'imio.migrator',
        'phonenumbers',
        'plone.api>=1.3.3',
        'plone.app.dexterity',
        'plone.app.lockingbehavior',
        'setuptools',
        'z3c.table',
        # fix about orderedselect
        'z3c.form>=3.2.4',
        'imio.helpers>=0.18',
        'imio.migrator>=1.11'
    ],
    extras_require={
        'test': [
            'plone.app.robotframework',
            'plone.app.testing',
            'imio.pyutils'
        ],
    },
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    [console_scripts]
    search_replace=collective.documentgenerator.search_replace.utils:main
    """,
)
