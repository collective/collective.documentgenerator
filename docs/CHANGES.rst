Changelog
=========

2.0.0 (2017-06-21)
------------------

- Make package compatible with both Plone4 and Plone5 at the same time :
  - Created Plone version specific profiles (plone4 and plone5);
  - Removed support for AT in the Plone5 version;
  - Adapted demo profile to work with Dexterity (plone.app.contenttypes).
  [gbastien]
- Run every tests in 'french' so we are sure that translations work everywhere.
  [gbastien]
- Added parameter `raiseOnError_for_non_managers` to be able to raise a Plone
  error instead generating the document where errors are included.  This avoid
  generating a document containing errors where some data may be lost like in
  PDF where errors are not viewable or even in ODT when users do not understand
  that errors in comments are important.  This will enable the `raiseOnError`
  parameter of appy.pod.renderer.Renderer.
  [gbastien]
- Call styles update at pod template creation
  [sgeulette]
- Raise exception when style update fails
  [sgeulette]
- Corrected mimetype of demo templates. Update style only for odt.
  [sgeulette]

1.0.6 (2017-05-31)
------------------

- Added do_rendering field in IMergeTemplatesRowSchema schema. If selected, the subtemplate is rendered first
  and the path is the value in context dict. Else the subtemplate object is the value in context dict.
  [sgeulette]
- Return generation context from rendering methods to use it in tests
  [sgeulette]
- Added unit testing for do_rendering feature
  [odelaere, sgeulette]
- Improved validation for ConfigurablePodTemplate
  [odelaere]
- Added validation to avoid generation context corruption at generation time
  [odelaere]
- Manage boolean values in context variables
  [sgeulette]
- Removed meta_type attribute causing error when pasting
  [sgeulette]
- Do not lose filename when updating a Pod template with it's styles template
  [gbastien]
- Ease override of term title of the `collective.documentgenerator.StyleTemplates` vocabulary
  [gbastien]
- Define a correct portal_type description for StyleTmplate so it is displayed in the folder_factories
  [gbastien]
- Modified generated filename, before it was POD template title and format, now it it build using POD template title,
  context title and format
  [gbastien]

1.0.5 (2017-03-10)
------------------

- Added parameter 'html' in display_html_as_text witch is mutually exclusive with 'field_name' to add ability to use a date field or an html formatted string with display_html_as_text.
  [odelaere]
- Added parameter 'text' in display_text_as_html witch is mutually exclusive with 'field_name' to add ability to use a date field or a string with display_text_as_html.
  [odelaere]
- Added parameter 'date' in display_date witch is mutually exclusive with 'field_name' to add ability to use a date field or a date object with display_date.
  [odelaere]
- Added parameter `optimize_tables` to be able to use the `optimalColumnWidths`
  functionnality of appy.pod.
  [gbastien]

1.0.4 (2017-02-14)
------------------

- Update styles templates only with force param.
  [sgeulette]
- Make sure `current_md5` is stored as unicode or it fails to validate when
  manually validating stored data.
  [gbastien]

1.0.3 (2017-02-10)
------------------

- Added utils method to update templates.
  [sgeulette]

1.0.2 (2017-02-07)
------------------

- Fix widget for fields `IConfigurablePODTemplate.pod_formats` and
  `IConfigurablePODTemplate.pod_portal_types` to avoid override by another
  package like it is the case when using `collective.z3cform.select2`.
  Use CheckBoxWidget for `IConfigurablePODTemplate.pod_portal_types` to ease
  selection when displaying several elements.
  [gbastien]
- Set appy renderer on view element stored in generation context.
  Useful when view has been overrided in generation context getter.
  [sgeulette]

1.0.1 (2017-01-13)
------------------

- Removed useless parameter in getDGHV method.
  [sgeulette]

1.0.0 (2017-01-12)
------------------

- Raise NotImplementedError in not implemented methods.
  [sgeulette]
- Rename display_html by render_xhtml and display_text by display_text_as_html.
  [sgeulette]
- Add display_html_as_text
  [sgeulette]
- Add get_state
  [sgeulette]
- Add context_var method to safely get an optional context variable
  [sgeulette]

0.14 (2016-12-19)
-----------------

- Use correct name for entry to documentgenerator configuration
  in the control panel.
  [gbastien]
- Added formats `.doc` and `.docx` to the demo template
  `test_template_multiple`.
  [gbastien]
- Set default value for oo_port and uno_path from environment variable
  [sgeulette]

0.13 (2016-12-09)
-----------------

- Validate path to python by importing `unohelper` instead importing
  `uno` because `uno` could have been installed using `pip install uno`
  but is not sufficient to generate the document.
  [gbastien]
- Added `.docx` format in which it is possible to generate template.
  [gbastien]
- Set oo_port from environment variable at install
  [sgeulette]

0.12 (2016-12-07)
-----------------

- Pass every parameters to DocumentGenerationHelperView.translate
  that zope.i18n.translate manages.
  [gbastien]
- Made context variable value not required
  [sgeulette]

0.11 (2016-11-22)
-----------------

- Replaced unrestrictedTraverse by getMultiAdapter.
  [sgeulette]
- Added context variables field on configurablepodtemplate, and validator.
  Added those variables in generation context.
  [sgeulette]
- Moved fr setting from default profile to testing
  [sgeulette]

0.10 (2016-10-05)
-----------------

- Use forceOoCall in renderer to call libreoffice to render b.e. table of contents in odt
  [sgeulette]
- Changed viewlet podtemplate search. Defined template in zcml.
  [sgeulette]
- Add content icons
  [sgeulette]
- Manage correctly datetime.date and datetime.datetime
  [sgeulette]
- Add display_widget method
  [sgeulette]
- Rename display_text to display_html (for rich text fields)
  [sgeulette]
- Add display_text for text fields to render intelligent html
  [sgeulette]
- Add method to get attribute value
  [sgeulette]
- Add method to get helper view on another object
  [sgeulette]
- Remove context parameter from helper methods to avoid changing context
  [sgeulette]
- Get generation view name from a method.
  [sgeulette]
- Use RadioFieldWidget for Bool field 'enabled' so it is displayed on the
  pod_template view when it is False.
  [gbastien]

0.9 (2016-06-22)
----------------

- Handle case of rendering value of single selection widget.
  [sdelcourt]


0.8 (2016-06-03)
----------------

- In `DocumentGenerationView._render_document`, pass `portal` as `imageResolver`
  to `appy.pod.renderer.Renderer` so private images can be accessed by
  LibreOffice in XHTML fields.
  [gbastien]


0.7 (2016-03-22)
----------------

- Pass `**kwargs` to DocumentGenerationView._render_document so it is possible to pass
  arbitrary parameters to appy.pod.renderer.Renderer that is called in _render_document
  and to which we also pass the `**kwargs`.
  This way, it is possible for example to turn `Renderer.raiseOnError` to True.
  [gbastien]
- Added meta_type for content_types `PODTemplate`, `ConfigurablePODTemplate`, `SubTemplate`
  and `StyleTemplate`, this way it can be used to filter out objectValues/objectIds.
  [gbastien]
- Added a validator on the configurablePODTemplates which check if the chosen generations
  formats are corrects with the kind of file provided.
  [boulch, DieKatze]


0.6 (2016-01-21)
----------------

- CSS fix, display POD templates in the viewlet using display: inline-block;
  instead of display: inline; so attached tags may be aligned on it.
  [gbastien]
- Added 'description' to the list of available data to display in the generationlinks viewlet.
  The POD template description is now displayed when hovering the POD template title.
  [gbastien]


0.5 (2015-12-02)
----------------

- Added `ConfigurablePODTemplateCondition._extra_expr_ctx` method so it is easy
  to extend the context of the ITALCondition expression without overriding
  the `evaluate` method.
  [gbastien]


0.4 (2015-12-02)
----------------

- Make sure to not query a `None` to ensure compatibility with ZCatalog 3.
  [gbastien]
- Take into account the `oo_port` paramater defined in the registry.
  [gbastien]


0.3 (2015-09-30)
----------------

- Extend the base helper view to do @@plone, @@plone_portal_state view available
  and added a method 'translate' to be able to translate a msgid in a given domain.
  [gbastien]
- Refactored the DocumentGenerationHelperView.display_date method to use
  toLocalizedDate and adapted AT and DX implementations.
  [gbastien]
- Refactor the generation view to pass the arguments `pod_template` and `output_format`
  directly to the view call or its methods.
  [gbastien, sdelcourt]


0.2 (2015-09-22)
----------------
- Renamed field `pod_portal_type` to `pod_portal_types` as this field
  is a multiselection field.
  [gbastien]
- Renamed `doc_uid` parameter used by the `document-generation` view to
  `template_uid`, more obvious, and makes it available in the viewlet
  link infos dict.
  [gbastien]
- Added field IConfigurablePODTemplate.pod_formats to be able to select the
  format we want to generate the POD template in.
  [gbastien]
- When evaluating the tal_condition on the template, pass extra_expr_ctx
  to the TAL expression so `context` and `here` become the element on which the TAL
  expression is actually evaluated instead of the pod_template and `template`
  is the pod_template
  [gbastien]


0.1 (2015-07-17)
----------------

- Nothing changed yet.


0.1 (2015-07-17)
----------------
- Initial release.
  [gbastien]

- ...

- Update bootstrap
  use https://raw.githubusercontent.com/buildout/buildout/master/bootstrap/bootstrap.py
  [fngaha]
