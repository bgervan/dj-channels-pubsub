=====
Usage
=====

To use Django Channels PubSub in a project, add it to your `INSTALLED_APPS`:

.. code-block:: python

    INSTALLED_APPS = (
        ...
        'dj_channels_pubsub.apps.DjChannelsPubsubConfig',
        ...
    )

Add Django Channels PubSub's URL patterns:

.. code-block:: python

    from dj_channels_pubsub import urls as dj_channels_pubsub_urls


    urlpatterns = [
        ...
        url(r'^', include(dj_channels_pubsub_urls)),
        ...
    ]
