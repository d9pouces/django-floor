django-floor
============

A common base for modern and complete Django websites, with many tools integrated.

  * gestion des crontab
  * supervisor -> en attente de supervisor 4
  * websockets -> en attente de django-redis pour Python 3
  * configurations pour Apache / NGinx

  * backup command: media files, database
  * fichiers de conf pour launchd, upstart ou systemd
  * génération des commandes pour créer un utilisateur système, la base de données


Conventions :

  * Nom du projet :
    - paramètre --dfproject
    - variable d'environnement DJANGOFLOOR_PROJECT_NAME
    - nom du script [project_name]-(celery|manage|gunicorn)

  * project-wide settings supplémentaires :
    - variable d'environnement DJANGOFLOOR_PROJECT_SETTINGS
    - project_name.defaults

  * user-defined settings :
    - paramètre --dfconf [nom du fichier.py]
    - [prefix]/etc/project_name/settings.py
    - [project_name]_configuration.py dans le dossier actuel

  * connaître la configuration choisie :
    - [project_name]-manage configuration (si installé)
    - python [project_name]-manage.py configuration (sinon)