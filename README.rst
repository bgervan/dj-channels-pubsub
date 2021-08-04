=============================
Django Channels PubSub
=============================

.. image:: https://badge.fury.io/py/dj-channels-pubsub.svg
    :target: https://badge.fury.io/py/dj-channels-pubsub

.. image:: https://travis-ci.org/bgervan/dj-channels-pubsub.svg?branch=master
    :target: https://travis-ci.org/bgervan/dj-channels-pubsub

.. image:: https://codecov.io/gh/bgervan/dj-channels-pubsub/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/bgervan/dj-channels-pubsub

Django Channels Layer for Google PubSub

Documentation
-------------

The full documentation is at https://dj-channels-pubsub.readthedocs.io.

Quickstart
----------

Install Django Channels PubSub::

    pip install dj-channels-pubsub


Add Environment variables:

::

    export GOOGLE_CLOUD_PROJECT="" # Real project ID required for local emulator too


For the local PubSub Emulator, add:

::

    export PUBSUB_EMULATOR_HOST=localhost:8085

For the local PubSub Emulator with Docker Compose:

::

    export PUBSUB_EMULATOR_HOST=pubsub:8085

::

    pubsub:
    image: google/cloud-sdk:331.0.0
    command: gcloud beta emulators pubsub start --host-port=0.0.0.0:8085
    ports:
      - "8085:8085"
    restart: unless-stopped

Features
--------

* TODO

Running Tests
-------------

Does the code actually work?

::

    source <YOURVIRTUALENV>/bin/activate
    (myenv) $ pip install tox
    (myenv) $ tox


Development commands
---------------------

::

    pip install -r requirements_dev.txt
    invoke -l


Credits
-------

Tools used in rendering this package:

*  Cookiecutter_
*  `cookiecutter-djangopackage`_

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`cookiecutter-djangopackage`: https://github.com/pydanny/cookiecutter-djangopackage
