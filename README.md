Djangofloor
==========
 
Djangofloor helps you to quickly create Django applications that are also easy to deploy. To reach these goals, Djangofloor provides:

  * an extension to the base Django's setting, allowing to split your configuration into several files (default values provided by Djangofloor, constants values for your project, deployement parameters, local values for development),
  * an unified signal dispatcher, using bi-directionnal websockets through Celery and Redis. You can call Python and Javascript signals from the Python or the Javascript side, 
  * auto-configuration for a few widespread Django apps (Django-Debug-Toolbar, Django-Redis-Sessions, Django-Pipeline) if they are present,
  * a base template using the well-known Bootstrap3 (but of course you can use any other templates),
  * valid default Django settings (like logs),
  * create new Django projects that are working and deployable out-of-the-box (even if you finally replace all default templates and views). 

Creating a new project
----------------------

Creating a working new project only requires a couple lines:

    pip install djangofloor
    djangofloor-createproject
      Your new project name [MyProject] NewProject
      Python package name [newproject]
      Initial version [0.1]
      Root project path [.] /tmp/newproject
    cd /tmp/newproject
    python setup.py deploy
    newproject-django migrate
    newproject-django runserver

    npm install yuglify -g

  * extensible config system

  * images @2x retina
  * language
  * cache (server/client-side): new decorator?
  * responsive
  * minification: django-pipeline
  * websockets: built-in
  * REST API: Django REST Framework
  * nginx or apache configuration
  * uwsgi or gunicorn
  * build de .deb

  * python 3  
  * logs
        
  * easy initial conf
  * create favicon


python3-redis - Persistent key-value database with network interface (Python 3 library)

base templates:
    - search button
    - create account window
    - logo
    - footer
    
WebSocket:
  - on génère un ID de fenêtre avec une liste de topics associés et une expiration
  - chaque topic à une liste d'ID
  - le websocket communique sur la file associée à cet ID
  pb : un message est envoyé à topic1 et topic2, un client est abonné aux deux ; comment dédoubler ? cache de 20 ou 30 derniers messages avec id unique ?
  - à la réception d'un event sur une websocket -> on génère une tâche Celery (toujours la même, qui va traiter le signal (ou les signaux ?))
  - comment générer la request à partir de l'ID de fenêtre ? les infos doivent être en RAM (petit cache) ou en dans Redis
  - une seule fonction pour ajouter des événements aux websockets via du pubsub
  
  
 editor.md/languages/en.js