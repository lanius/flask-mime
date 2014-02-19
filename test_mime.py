# -*- coding: utf-8 -*-

import unittest

from flask import Flask
from flask_mime import Mime, to_unicode


class RoutingTestCase(unittest.TestCase):

    def setUp(self):
        app = Flask(__name__)
        mimetype = Mime(app)

        @mimetype('text/html')
        @app.route('/path')
        def path_html():
            return 'html'

        @mimetype('application/json')
        @app.route('/path')
        def path_json():
            return 'json'

        @mimetype('text/html')
        @app.route('/')
        def slash_html():
            return 'html'

        @mimetype('application/json')
        @app.route('/')
        def slash_json():
            return 'json'

        @mimetype('application/json')
        @app.route('/reverse')
        def reverse_json():
            return 'json'

        @mimetype('text/html')
        @app.route('/reverse')
        def reverse_html():
            return 'html'

        @mimetype('text/plain')
        @app.route('/q')
        def q_text():
            return 'text'

        @mimetype('application/json')
        @app.route('/q')
        def q_json():
            return 'json'

        @mimetype('text/html')
        @app.route('/post', methods=['POST'])
        def post_html():
            return 'html'

        @mimetype('application/json')
        @app.route('/post', methods=['POST'])
        def post_json():
            return 'json'

        @app.route('/nomimetype')
        def no_mimetype():
            return 'no mimetype'

        self.app = app

    def get_with_accept(self, path, accept):
        c = self.app.test_client()
        rv = c.get(path, headers={'Accept': accept})
        return rv

    def post_with_accept(self, path, accept):
        c = self.app.test_client()
        rv = c.post(path, headers={'Accept': accept})
        return rv

    def test_basic(self):
        rv = self.get_with_accept('/path', 'text/html')
        self.assertEqual(to_unicode(rv.data), 'html')

        rv = self.get_with_accept('/path', 'application/json')
        self.assertEqual(to_unicode(rv.data), 'json')

    def test_not_acceptable(self):
        rv = self.get_with_accept('/path', 'text/plain')
        self.assertEqual(rv.status_code, 406)

    def test_slash(self):
        rv = self.get_with_accept('/', 'text/html')
        self.assertEqual(to_unicode(rv.data), 'html')

        rv = self.get_with_accept('/', 'application/json')
        self.assertEqual(to_unicode(rv.data), 'json')

    def test_reverse(self):
        rv = self.get_with_accept('/reverse', 'text/html')
        self.assertEqual(to_unicode(rv.data), 'html')

        rv = self.get_with_accept('/reverse', 'application/json')
        self.assertEqual(to_unicode(rv.data), 'json')

    def test_with_q(self):
        rv = self.get_with_accept(
            '/q', 'text/html, text/plain;q=0.9, application/json;q=0.5')
        self.assertEqual(to_unicode(rv.data), 'text')

    def test_post(self):
        rv = self.post_with_accept('/post', 'text/html')
        self.assertEqual(to_unicode(rv.data), 'html')

        rv = self.post_with_accept('/post', 'application/json')
        self.assertEqual(to_unicode(rv.data), 'json')

    def test_no_mimetype(self):
        rv = self.get_with_accept('/nomimetype', 'text/html')
        self.assertEqual(to_unicode(rv.data), 'no mimetype')


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(RoutingTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
