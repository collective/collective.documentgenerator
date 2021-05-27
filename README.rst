.. image:: https://github.com/collective/collective.documentgenerator/actions/workflows/python-package.yml/badge.svg?branch=master
    :target: https://github.com/collective/collective.documentgenerator/actions/workflows/python-package.yml

.. image:: https://coveralls.io/repos/collective/collective.documentgenerator/badge.svg?branch=master
   :alt: Coveralls badge
   :target: https://coveralls.io/r/collective/collective.documentgenerator?branch=master

.. image:: http://img.shields.io/pypi/v/collective.documentgenerator.svg
   :alt: PyPI badge
   :target: https://pypi.org/project/collective.documentgenerator


============================
collective.documentgenerator
============================

``collective.documentgenerator`` is an elegant product allowing to easily **produce office documents** based on dynamic templates.

New content types are used to store the different templates:

* **style templates**, that can be common for other templates
* **sub templates**, that can be used in other templates
* **mailing loop templates**, that can be used by other templates to do a loop for mailing
* **basic templates**
* **advanced templates**, regarding configuration

Templates are created within `LibreOffice <http://www.libreoffice.org>`_ software.

Output formats are those that can be produced by LibreOffice:

* odt and ods formats
* doc, docx, xls, xlsx formats
* pdf, csv, rtf

You can use a demo profile to easily test the product.


Translations
------------

This product has been translated into

- French.

- Spanish.

You can contribute for any message missing or other new languages, join us at
`Plone Collective Team <https://www.transifex.com/plone/plone-collective/>`_
into *Transifex.net* service with all world Plone translators community.


Installation
============

Install ``collective.documentgenerator`` by adding it to your buildout:

   [buildout]

    ...

    eggs =
        collective.documentgenerator


and then running "bin/buildout"


Usage
=====


**How to add a new POD template?**
----------------------------------

In your Plone site, you can add two sorts of main templates :

- PODTemplate : composed of title, description and odt file to be uploaded
- ConfigurablePODTemplate : adding configurable fields to basic template

  * output formats selection
  * portal types selection
  * style template selection
  * subtemplate selection
  * TAL expression as condition (`behavior <https://github.com/collective/collective.behavior.talcondition>`_).
  * enabling flag
  * context variables list
  * mailing loop template

If you want, you can organize your templates in one or more folder.


**How to write the template ?**
-------------------------------

The `appy framework <http://appyframework.org>`_ is used to interpret the template and render it using the context.

You can find a `documentation <http://appyframework.org/podWritingTemplates.html>`_ explaining the syntax that can be used.

You can do the following things:

- use basic python expression to access context fields or methods
- do an if... then... else...
- do a loop for a paragraph, a section, a table, a row, a cell
- transform xhtml to text

Base helper methods can be used in templates and custom methods can be added.


**How to generate a document?**
-------------------------------

A viewlet displays all the available PODTemplate and ConfigurablePODTemplate following the current context.
Clicking the template link will call the 'document-generation' view.

- Calling 'document-generation' view

  * render template and propose to download the generated document
  * parameters: template UID and document type
  * this is the default view used in the viewlet

- Calling 'persistent-document-generation' view

  * render template and create a file with the generated document
  * parameters: template UID and document type

- Calling 'mailing-loop-persistent-document-generation' view

  * loop on persisted rendered document and create a file containing all documents
  * parameters: document UID

**Search and replace**
----------------------

Documentation about the search and replace feature is here :
`docs/search_replace.rst <https://github.com/collective/collective.documentgenerator/tree/master/docs/search_replace.rst>`_


Plone versions
--------------

It is working and tested on Plone 4.3, Plone 5.0, 5.1 and 5.2 (Python2.7).


Contribute
==========

* `Source code @ GitHub <https://github.com/collective/collective.documentgenerator.git>`_
* `Issues @ GitHub <https://github.com/collective/collective.documentgenerator/issues>`_
* `Continuous Integration @ Travis CI <https://travis-ci.org/collective/collective.documentgenerator>`_
* `Code Coverage @ Coveralls.io <https://coveralls.io/r/collective/collective.documentgenerator?branch=master>`_


License
=======

The project is licensed under the GPLv2.
