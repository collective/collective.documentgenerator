Users
=====

**How to add a new POD template?**
----------------------------------

In your Plone site, you can add two sorts of template :

- PODTemplate : composed of title, description and odt file to be uploaded
- ConfigurablePODTemplate : adding configurable fields to basic template

  * output formats selection
  * portal types selection
  * style template selection
  * subtemplate selection
  * tal expression as condition (`behavior <https://github.com/collective/collective.behavior.talcondition>`_).
  * enabling flag

    .. figure:: images/AddPODTTemplateMenu.png

       Add element

If you want, you can organize your templates in one or more folder.

**How to write the template ?**
-------------------------------

The `appy framework <http://appyframework.org>`_ is used to interpret the template and render it using the context.

You can find a `documentation <http://appyframework.org/podWritingTemplates.html>`_ explaining the syntax that can be used.

You can do the following things:

- use context field
- use python expression
- do an if... then... else...
- do a loop for a paragraph, a section, a table, a row, a cell
- transform xhtml to text

Base helper methods can be used in templates and custom methods can be added.

**How to generate document?**
-----------------------------

A viewlet displays all the available PODTemplate and ConfigurablePODTemplate following the current context.

Clicking the template link will render it and propose to download the generated document.

    .. figure:: images/viewlet.png

       Viewlet


**How to launch libreoffice in drived capability mode (needed for style templates, format conversion)**
------------------------------------------------------------------------

On desktop pc (First run the command, before normally using libreoffice):
soffice "--accept=socket,host=localhost,port=2002;urp;"

On server:
soffice --invisible --headless "--accept=socket,host=localhost,port=2002;urp;"
