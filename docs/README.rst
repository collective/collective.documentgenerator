.. image:: https://travis-ci.org/collective/collective.documentgenerator.svg?branch=master
   :target: https://travis-ci.org/collective/collective.documentgenerator

.. image:: https://coveralls.io/repos/collective/collective.documentgenerator/badge.png?branch=master
   :target: https://coveralls.io/r/collective/collective.documentgenerator?branch=master

============================
collective.documentgenerator
============================

``collective.documentgenerator`` is an elegant product allowing to easily **produce office documents** based on dynamic templates.

New content types are used to store the different templates:

* **style templates**, that can be common for other templates
* **sub templates**, that can be used in other templates
* **basic templates**
* **advanced templates**, regarding configuration

Templates are created within `libreoffice <http://www.libreoffice.org>`_ software.

Output formats are those that can be produced by libreoffice:

* odt and ods formats
* doc, docx, xls, xlsx formats
* pdf, csv, rtf

You can use a demo profile to easily test the product.

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
  * tal expression as condition (`behavior <https://github.com/collective/collective.behavior.talcondition>`_).
  * enabling flag
  * context variables list

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

Clicking the template link will render it and propose to download the generated document.

Source code
===========

* `Source code @ GitHub <https://github.com/collective/collective.documentgenerator.git>`_
* `Issues @ GitHub <https://github.com/collective/collective.documentgenerator/issues>`_
* `Continuous Integration @ Travis CI <https://travis-ci.org/collective/collective.documentgenerator>`_
* `Code Coverage @ Coveralls.io <https://coveralls.io/r/collective/collective.documentgenerator?branch=master>`_
