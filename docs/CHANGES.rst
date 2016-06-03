Changelog
=========

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
