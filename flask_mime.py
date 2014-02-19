# -*- coding: utf-8 -*-

"""
    flask_mime
    ~~~~~~~~~~

    Provides MIME type based request dispatching mechanism to applications.
"""

from functools import wraps

from werkzeug.routing import (
    Rule as _Rule, Map as _Map, MapAdapter as _MapAdapter,
    RequestRedirect, RequestSlash, RequestAliasRedirect,
    _simple_rule_re
)
from werkzeug.http import parse_accept_header
from werkzeug.datastructures import MIMEAccept
from werkzeug.urls import url_quote, url_join
from werkzeug.exceptions import NotFound, MethodNotAllowed, NotAcceptable
from werkzeug._compat import to_unicode, string_types, native_string_result


class Rule(_Rule):
    """Overridden for adding the mimetype attribute."""

    def __init__(self, string, defaults=None, subdomain=None, methods=None,
                 build_only=False, endpoint=None, strict_slashes=None,
                 redirect_to=None, alias=False, host=None, mimetype=None):
        _Rule.__init__(self, string, defaults, subdomain, methods, build_only,
                       endpoint, strict_slashes, redirect_to, alias, host)
        self.mimetype = mimetype

    @native_string_result
    def __repr__(self):
        if self.map is None:
            return u'<%s (unbound)>' % self.__class__.__name__
        tmp = []
        for is_dynamic, data in self._trace:
            if is_dynamic:
                tmp.append(u'<%s>' % data)
            else:
                tmp.append(data)
        return u'<%s %s%s%s -> %s>' % (
            self.__class__.__name__,
            repr((u''.join(tmp)).lstrip(u'|')).lstrip(u'u'),
            self.methods is not None and u' (%s)' % u', '.join(
                self.methods) or u'',
            u' (%s)' % self.mimetype,
            self.endpoint
        )


class Map(_Map):
    """Overridden for returning the custom MapAdapter."""

    def __init__(self, rules=None, default_subdomain='', charset='utf-8',
                 strict_slashes=True, redirect_defaults=True,
                 converters=None, sort_parameters=False, sort_key=None,
                 encoding_errors='replace', host_matching=False):
        _Map.__init__(self, rules, default_subdomain, charset, strict_slashes,
                      redirect_defaults, converters, sort_parameters,
                      sort_key, encoding_errors, host_matching)

    def bind(self, server_name, script_name=None, subdomain=None,
             url_scheme='http', default_method='GET', path_info=None,
             query_args=None):
        org_adapter = _Map.bind(self, server_name, script_name, subdomain,
                                subdomain, url_scheme, default_method,
                                path_info, query_args)
        return self._convert_adapter(org_adapter)

    def bind_to_environ(self, environ, server_name=None, subdomain=None):
        org_adapter = _Map.bind_to_environ(self, environ,
                                           server_name, subdomain)
        return self._convert_adapter(org_adapter, environ)

    def _convert_adapter(self, adapter, environ=None):
        mimetypes = parse_accept_header(
            environ.get('HTTP_ACCEPT'), MIMEAccept
        ) if environ else None
        return MapAdapter(adapter.map, adapter.server_name,
                          adapter.script_name, adapter.subdomain,
                          adapter.url_scheme, adapter.path_info,
                          adapter.default_method, adapter.query_args,
                          mimetypes)


class MapAdapter(_MapAdapter):
    """Overridden for adding MIME type based rule matching mechanism. The most
    part of code remains that of werkzeug 0.9."""

    def __init__(self, map, server_name, script_name, subdomain,
                 url_scheme, path_info, default_method, query_args=None,
                 mimetypes=None):
        _MapAdapter.__init__(self, map, server_name, script_name,
                             subdomain, url_scheme, path_info,
                             default_method, query_args)
        self.mimetypes = mimetypes

    def match(self, path_info=None, method=None, return_rule=False,
              query_args=None):
        self.map.update()
        if path_info is None:
            path_info = self.path_info
        else:
            path_info = to_unicode(path_info, self.map.charset)
        if query_args is None:
            query_args = self.query_args
        method = (method or self.default_method).upper()

        path = u'%s|/%s' % (self.map.host_matching and self.server_name or
                            self.subdomain, path_info.lstrip('/'))

        have_match_for = set()
        candidates_by_mimetype = []  # [(q, rule, rv),]
        mimetype_mismatched = False
        for rule in self.map._rules:
            try:
                rv = rule.match(path)
            except RequestSlash:
                raise RequestRedirect(self.make_redirect_url(
                    url_quote(path_info, self.map.charset,
                              safe='/:|+') + '/', query_args))
            except RequestAliasRedirect as e:
                raise RequestRedirect(
                    self.make_alias_redirect_url(path, rule.endpoint,
                                                 e.matched_values, method,
                                                 query_args))
            if rv is None:
                continue
            if rule.methods is not None and method not in rule.methods:
                have_match_for.update(rule.methods)
                continue
            if rule.mimetype is not None:
                q = self.mimetypes[rule.mimetype]
                if q == 0:  # mismatch
                    mimetype_mismatched = True
                    continue
                elif q < 1:  # find the most suitable rule later
                    candidates_by_mimetype.append((q, rule, rv))
                    continue
                else:  # best match
                    pass

            if self.map.redirect_defaults:
                redirect_url = self.get_default_redirect(rule, method, rv,
                                                         query_args)
                if redirect_url is not None:
                    raise RequestRedirect(redirect_url)

            if rule.redirect_to is not None:
                if isinstance(rule.redirect_to, string_types):
                    def _handle_match(match):
                        value = rv[match.group(1)]
                        return rule._converters[match.group(1)].to_url(value)
                    redirect_url = _simple_rule_re.sub(_handle_match,
                                                       rule.redirect_to)
                else:
                    redirect_url = rule.redirect_to(self, **rv)
                raise RequestRedirect(str(url_join('%s://%s%s%s' % (
                    self.url_scheme,
                    self.subdomain and self.subdomain + '.' or '',
                    self.server_name,
                    self.script_name
                ), redirect_url)))

            if return_rule:
                return rule, rv
            else:
                return rule.endpoint, rv

        if have_match_for:
            raise MethodNotAllowed(valid_methods=list(have_match_for))
        if candidates_by_mimetype:
            # find the rule that has the highest q
            _, rule, rv = sorted(
                candidates_by_mimetype, key=lambda t: t[0], reverse=True
            )[0]
            if return_rule:
                return rule, rv
            else:
                return rule.endpoint, rv
        elif mimetype_mismatched:
            raise NotAcceptable()

        raise NotFound()


class Mime(object):
    """Provides a functon to register a MIME type for request dispatching."""

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.url_rule_class = Rule
        app.url_map = Map()

    def __call__(self, mimetype):
        def decorator(view_func):
            endpoint = None
            for ep, func in self.app.view_functions.items():
                if func == view_func:
                    endpoint = ep
            if endpoint is None:
                raise Exception('any endpoint are not found.')

            for r in self.app.url_map.iter_rules(endpoint):
                r.mimetype = mimetype

            @wraps(view_func)
            def wrapper(*args, **kwargs):
                return view_func(*args, **kwargs)

            return wrapper

        return decorator
