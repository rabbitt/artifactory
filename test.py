#!/usr/bin/env python

import os
import sys
import io

import unittest
import multiprocessing
import tempfile
import artifactory
import json
import requests
import datetime
import dateutil

from artifactory import Config, ArtifactoryPath, PureArtifactoryPath, http
from artifactory.paths import _ArtifactoryAccessor, _ArtifactoryFlavour

try:
  # attempt python 3 variant first
  from unittest.mock import MagicMock as MM
except ImportError:
  # fallback to python 2
  from mock import MagicMock as MM

class UtilTest(unittest.TestCase):
    def test_matrix_encode(self):
        params = {"foo": "bar",
                  "qux": "asdf"}

        s = http.encode_matrix_parameters(params)

        self.assertEqual(s, "foo=bar;qux=asdf")

        params = {'baz': ['bar', 'quux'], 'foo': 'asdf'}

        s = http.encode_matrix_parameters(params)

        self.assertEqual(s, "baz=bar;baz=quux;foo=asdf")

    def test_escape_chars(self):
        s = http.escape_chars('a,b|c=d')
        self.assertEqual(s, "a\,b\|c\=d")

    def test_properties_encode(self):
        params = {"foo": "bar,baz", "qux": "as=df"}
        s = http.encode_properties(params)
        self.assertEqual(s, "foo=bar\\,baz|qux=as\\=df")

    def test_properties_encode_multi(self):
        params = {'baz': ['ba\\r', 'qu|ux'], 'foo': 'a,s=df'}
        s = http.encode_properties(params)
        self.assertEqual(s, "baz=ba\\r,qu\|ux|foo=a\,s\=df")


class ArtifactoryFlavorTest(unittest.TestCase):
    flavour = _ArtifactoryFlavour()

    def _check_parse_parts(self, arg, expected):
        f = self.flavour.parse_parts
        sep = self.flavour.sep
        altsep = self.flavour.altsep
        actual = f([x.replace('/', sep) for x in arg])
        self.assertEqual(actual, expected)
        if altsep:
            actual = f([x.replace('/', altsep) for x in arg])
            self.assertEqual(actual, expected)

    def setUp(self):
      Config.load_yaml("---\nhttp://custom/root: {}\n")

    def tearDown(self):
        Config.clear()

    def _check_splitroot(self, arg, expected):
        f = self.flavour.splitroot
        actual = f(arg)
        self.assertEqual(actual, expected)

    def test_splitroot(self):
        check = self._check_splitroot

        check(".com",
              ('', '', '.com'))
        check("example1.com",
              ('', '', 'example1.com'))
        check("example2.com/artifactory",
              ('example2.com/artifactory', '', ''))
        check("example2.com/artifactory/",
              ('example2.com/artifactory', '', ''))
        check("example3.com/artifactory/foo",
              ('example3.com/artifactory', '/foo/', ''))
        check("example3.com/artifactory/foo/bar",
              ('example3.com/artifactory', '/foo/', 'bar'))
        check("artifactory.local/artifactory/foo/bar",
              ('artifactory.local/artifactory', '/foo/', 'bar'))
        check("http://artifactory.local/artifactory/foo/bar",
              ('http://artifactory.local/artifactory', '/foo/', 'bar'))
        check("https://artifactory.a.b.c.d/artifactory/foo/bar",
              ('https://artifactory.a.b.c.d/artifactory', '/foo/', 'bar'))

    def test_splitroot_custom_root(self):
        check = self._check_splitroot

        check("http://custom/root", ('http://custom/root', '', ''))
        check("custom/root", ('custom/root', '', ''))
        check("https://custom/root", ('https://custom/root', '', ''))
        check("http://custom/root/", ('http://custom/root', '', ''))
        check("http://custom/root/artifactory", ('http://custom/root', '/artifactory/', ''))
        check("http://custom/root/foo/bar", ('http://custom/root', '/foo/', 'bar'))
        check("https://foo.bar.com/some-repository/", ('https://foo.bar.com', '/some-repository/', ''))
        check("https://custom/root/foo/baz", ('https://custom/root', '/foo/', 'baz'))


    def test_parse_parts(self):
        check = self._check_parse_parts

        check(['.txt'],
              ('', '', ['.txt']))

        check(['http://b/artifactory/c/d.xml'],
               ('http://b/artifactory', '/c/',
                ['http://b/artifactory/c/', 'd.xml']))

        check(['http://example.com/artifactory/foo'],
              ('http://example.com/artifactory', '/foo/',
               ['http://example.com/artifactory/foo/']))

        check(['http://example.com/artifactory/foo/bar'],
              ('http://example.com/artifactory', '/foo/',
               ['http://example.com/artifactory/foo/', 'bar']))

        check(['http://example.com/artifactory/foo/bar/artifactory'],
              ('http://example.com/artifactory', '/foo/',
               ['http://example.com/artifactory/foo/', 'bar', 'artifactory']))


class PureArtifactoryPathTest(unittest.TestCase):
    cls = PureArtifactoryPath

    def test_root(self):
        P = self.cls

        self.assertEqual(P('http://a/artifactory/b').root,
                         '/b/')

        self.assertEqual(P('http://a/artifactory/').root,
                         '')


    def test_anchor(self):
        P = self.cls
        b = P("http://b/artifactory/c/d.xml")
        self.assertEqual(b.anchor, "http://b/artifactory/c/")

    def test_with_suffix(self):
        P = self.cls

        b = P("http://b/artifactory/c/d.xml")
        c = b.with_suffix(".txt")
        self.assertEqual(str(c), "http://b/artifactory/c/d.txt")


class ArtifactoryAccessorTest(unittest.TestCase):
    """ Test the real artifactory integration """
    cls = _ArtifactoryAccessor

    def setUp(self):
        self.file_stat = """
            {
                "repo" : "ext-release-local",
                "path" : "/org/company/tool/1.0/tool-1.0.tar.gz",
                "created" : "2014-02-24T21:20:59.999+04:00",
                "createdBy" : "someuser",
                "lastModified" : "2014-02-24T21:20:36.000+04:00",
                "modifiedBy" : "anotheruser",
                "lastUpdated" : "2014-02-24T21:20:36.000+04:00",
                "downloadUri" : "http://artifactory.local/artifactory/ext-release-local/org/company/tool/1.0/tool-1.0.tar.gz",
                "mimeType" : "application/octet-stream",
                "size" : "26776462",
                "checksums" : {
                    "sha1" : "fc6c9e8ba6eaca4fa97868ac900570282133c095",
                    "md5" : "2af7d54a09e9c36d704cb3a2de28aff3"
                },
                "originalChecksums" : {
                    "sha1" : "fc6c9e8ba6eaca4fa97868ac900570282133c095",
                    "md5" : "2af7d54a09e9c36d704cb3a2de28aff3"
                },
                "uri" : "http://artifactory.local/artifactory/api/storage/ext-release-local/org/company/tool/1.0/tool-1.0.tar.gz"
            }
        """
        self.dir_stat = """
            {
                "repo" : "libs-release-local",
                "path" : "/",
                "created" : "2014-02-18T15:35:29.361+04:00",
                "lastModified" : "2014-02-18T15:35:29.361+04:00",
                "lastUpdated" : "2014-02-18T15:35:29.361+04:00",
                "children" : [ {
                    "uri" : "/.index",
                    "folder" : true
                }, {
                    "uri" : "/com",
                    "folder" : true
                } ],
                "uri" : "http://artifactory.local/artifactory/api/storage/libs-release-local"
            }
        """

    def test_stat(self):
        a = self.cls()
        P = ArtifactoryPath

        # Regular File
        p = P("http://artifactory.local/artifactory/api/storage/ext-release-local/org/company/tool/1.0/tool-1.0.tar.gz")

        a.rest_get = MM(return_value=(self.file_stat, 200))

        s = a.stat(p)
        self.assertEqual(s.ctime, dateutil.parser.parse("2014-02-24T21:20:59.999+04:00"))
        self.assertEqual(s.mtime, dateutil.parser.parse("2014-02-24T21:20:36.000+04:00"))
        self.assertEqual(s.created_by, "someuser")
        self.assertEqual(s.modified_by, "anotheruser")
        self.assertEqual(s.mime_type, "application/octet-stream")
        self.assertEqual(s.size, 26776462)
        self.assertEqual(s.sha1, "fc6c9e8ba6eaca4fa97868ac900570282133c095")
        self.assertEqual(s.md5, "2af7d54a09e9c36d704cb3a2de28aff3")
        self.assertEqual(s.is_dir, False)

        # Directory
        p = P("http://artifactory.local/artifactory/api/storage/libs-release-local")

        a.rest_get = MM(return_value=(self.dir_stat, 200))

        s = a.stat(p)
        self.assertEqual(s.ctime, dateutil.parser.parse("2014-02-18T15:35:29.361+04:00"))
        self.assertEqual(s.mtime, dateutil.parser.parse("2014-02-18T15:35:29.361+04:00"))
        self.assertEqual(s.created_by, None)
        self.assertEqual(s.modified_by, None)
        self.assertEqual(s.mime_type, None)
        self.assertEqual(s.size, 0)
        self.assertEqual(s.sha1, None)
        self.assertEqual(s.md5, None)
        self.assertEqual(s.is_dir, True)

    def test_listdir(self):
        a = self.cls()
        P = ArtifactoryPath

        # Directory
        p = P("http://artifactory.local/artifactory/api/storage/libs-release-local")

        a.rest_get = MM(return_value=(self.dir_stat, 200))

        children = a.listdir(p)

        self.assertEqual(children, ['.index', 'com'])

        # Regular File
        p = P("http://artifactory.local/artifactory/api/storage/ext-release-local/org/company/tool/1.0/tool-1.0.tar.gz")

        a.rest_get = MM(return_value=(self.file_stat, 200))


        self.assertRaises(OSError, a.listdir, p)

    def test_mkdir(self):
        pass

    def test_deploy(self):
        a = self.cls()
        P = ArtifactoryPath

        p = P("http://b/artifactory/c/d")

        params = {'foo': 'bar', 'baz': 'quux'}

        a.rest_put_stream = MM(return_value=('OK', 200))

        f = io.StringIO()

        a.deploy(p, f, parameters=params)

        url = "http://b/artifactory/c/d;baz=quux;foo=bar"

        a.rest_put_stream.assert_called_with(url, f, headers={}, auth=None, verify=True, cert=None)


class ArtifactoryPathTest(unittest.TestCase):
    """ Test the filesystem-accessing fuctionality """
    cls = ArtifactoryPath

    def test_basic(self):
        P = self.cls
        a = P("http://a/artifactory/")

    def test_auth(self):
        P = self.cls
        a = P("http://a/artifactory/", auth=('foo', 'bar'))
        self.assertEqual(a.auth, ('foo', 'bar'))

    def test_auth_inheritance(self):
        P = self.cls
        b = P("http://b/artifactory/c/d", auth=('foo', 'bar'))
        c = b.parent
        self.assertEqual(c.auth, ('foo', 'bar'))

        b = P("http://b/artifactory/c/d", auth=('foo', 'bar'))
        c = b.relative_to("http://b/artifactory/c")
        self.assertEqual(c.auth, ('foo', 'bar'))

        b = P("http://b/artifactory/c/d", auth=('foo', 'bar'))
        c = b.joinpath('d')
        self.assertEqual(c.auth, ('foo', 'bar'))

        b = P("http://b/artifactory/c/d", auth=('foo', 'bar'))
        c = b / 'd'
        self.assertEqual(c.auth, ('foo', 'bar'))

        b = P("http://b/artifactory/c/d.xml", auth=('foo', 'bar'))
        c = b.with_name("d.txt")
        self.assertEqual(c.auth, ('foo', 'bar'))

        b = P("http://b/artifactory/c/d.xml", auth=('foo', 'bar'))
        c = b.with_suffix(".txt")
        self.assertEqual(c.auth, ('foo', 'bar'))


class TestArtifactoryConfig(unittest.TestCase):
    def test_artifactory_config(self):
        cfg = {
          'http://bar.net/artifactory': {
            'username': 'foo', 
            'password': 'bar'
          }, 
          'foo.net/artifactory': {
            'username': 'admin', 
            'verify': False, 
            'cert': '~/path-to-cert', 
            'password': 'ilikerandompasswords'
          }, 
          'http://artifactory.local/artifactory': {}
        }
        
        Config.load(cfg)
        
        c = Config['foo.net/artifactory']
        self.assertIsInstance(c, dict)
        self.assertEqual(c['username'], 'admin')
        self.assertEqual(c['password'], 'ilikerandompasswords')
        self.assertEqual(c['verify'], False)
        self.assertEqual(c['cert'], os.path.expanduser('~/path-to-cert'))

        c = Config['http://bar.net/artifactory']
        self.assertIsInstance(c, dict)
        self.assertEqual(c['username'], 'foo')
        self.assertEqual(c['password'], 'bar')
        self.assertEqual(c['verify'], True)

        c = Config['bar.net/artifactory']
        self.assertIsInstance(c, dict)
        self.assertEqual(c['username'], 'foo')
        self.assertEqual(c['password'], 'bar')

        c = Config['https://bar.net/artifactory']
        self.assertIsInstance(c, dict)
        self.assertEqual(c['username'], 'foo')
        self.assertEqual(c['password'], 'bar')
        
        c = Config['artifactory.local/artifactory/foo']
        self.assertIsInstance(c, dict)
        self.assertEqual(c['username'], None)
        self.assertEqual(c['password'], None)
        self.assertEqual(c['verify'], True)
        self.assertEqual(c['cert'], None)

        c = Config['foobarbaz']
        self.assertIsNone(c)

if __name__ == '__main__':
    unittest.main()
