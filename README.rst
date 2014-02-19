
Flask-Mime
==========

Flask-Mime is Flask extension that enables applications to dispatch requests based on Accept header of it.


Install
-------

Install the extension with the following command:

.. code-block:: bash

    $ pip install Flask-Mime


Usage
-----

Create a Mime object and define routes with MIME types:

.. code-block:: python

    from flask import Flask, render_template, jsonify
    from flask_mime import Mime

    app = Flask(__name__)
    mimetype = Mime(app)

    @mimetype('text/html')
    @app.route('/')
    def index_html():
        return render_template('index.html')

    @mimetype('application/json')
    @app.route('/')
    def index_json():
        return jsonify(data={'content': 'index'})


Each requests are dispatched depending on the value of Accept header, even though they have same request path:

.. code-block:: python

    client = app.test_client()
    client.get('/', headers={'Accept': 'text/html'})  # returns html
    client.get('/', headers={'Accept': 'application/json'})  # returns json


Note
----

Note that MIME type based request dispatching mechanism may have negative influence for some applications, for example, which has a cache system.
