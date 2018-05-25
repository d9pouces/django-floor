Default URL patterns
====================

The default root URL configuration fullfills classical needs:

  * i18n JavaScript catalog,
  * static and media files (based on `settings.STATIC_ROOT/STATIC_URL/MEDIA_ROOT/MEDIA_URL`),
  * default files for `/robots.txt` (a template that can be overridden in `templates/djangofloor/robots.txt`),
  * default files for `/favicon.ico`, `/apple-touch-icon.png` and `/apple-touch-icon-precomposed.png`
   (you should override them in your `static/favicon/XXXX`),
  * `df:login`, `df:logout`, `df:password_reset`, `df:set_password`, `df:signup` (these views should be self-explained),
  * `df:signals`, corresponding to a JavaScript file with existing Python signals,
  * `df:system_state`, `df:raise_exception` and `df:generate_log` used by the system state view
    when `settings.DF_SYSTEM_CHECKS` is not empty,
