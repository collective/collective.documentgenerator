Users
=====

How to add a new POD template
-----------------------------

In your Plone site, you can add two sorts of template :

 - PODTemplate : composed of title, description and odt file to be uploaded
 - ConfigurablePODTemplate : the same field than PODTemplate to which we add a filter on the type of the object,
   a field that contain a tal expression and an enabled field.

    .. figure:: images/AddPODTTemplateMenu.png 

       Add element.

Il you want, you can organize your PODTemplate and ConfigurablePODTemplate in one or more folder.

How to create a new odt file using appy
---------------------------------------

You can find the documentation here  `appy <http://appyframework.org/podWritingTemplates.html>`_

How to generate document
------------------------

A viewlet display all the available PODTemplate and ConfigurablePODTemplate on a Plone Object.

    .. figure:: images/viewlet.png

       Viewlet

