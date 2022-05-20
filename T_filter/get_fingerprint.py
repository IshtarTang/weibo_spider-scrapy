# coding=utf-8

"""
This module provides some useful functions for working with
scrapy.http.Request objects
"""
from __future__ import print_function
from scrapy import Request
import hashlib
import weakref
from scrapy.utils.python import to_bytes
from w3lib.url import canonicalize_url
import re
import logging

_fingerprint_cache = weakref.WeakKeyDictionary()


def request_fingerprint(request, include_headers=None):
    """
    Return the request fingerprint.

    The request fingerprint is a hash that uniquely identifies the resource the
    request points to. For example, take the following two urls:

    http://www.example.com/query?id=111&cat=222
    http://www.example.com/query?cat=222&id=111

    Even though those are two different URLs both point to the same resource
    and are equivalent (ie. they should return the same response).

    Another example are cookies used to store session ids. Suppose the
    following page is only accessible to authenticated users:

    http://www.example.com/members/offers.html

    Lot of sites use a cookie to store the session id, which adds a random
    component to the HTTP Request and thus should be ignored when calculating
    the fingerprint.

    For this reason, request headers are ignored by default when calculating
    the fingeprint. If you want to include specific headers use the
    include_headers argument, which is a list of Request headers to include.

    """
    # 一点小修改，如果爬的微博页，直接用uid当签名
    # 本来想再改些的，但是想想感觉不合适，算了

    url1 = request.url
    wb_match = re.search("weibo.com(/+\d+/\w+)\?*", url1)
    if wb_match:
        fingerprint = wb_match.group(1)
        # logging.info("fig {}".format(fingerprint))
        return fingerprint

    if include_headers:
        include_headers = tuple(to_bytes(h.lower())
                                for h in sorted(include_headers))
    cache = _fingerprint_cache.setdefault(request, {})
    if include_headers not in cache:
        fp = hashlib.sha1()
        fp.update(to_bytes(request.method))
        fp.update(to_bytes(canonicalize_url(request.url)))
        fp.update(request.body or b'')
        if include_headers:
            for hdr in include_headers:
                if hdr in request.headers:
                    fp.update(hdr)
                    for v in request.headers.getlist(hdr):
                        fp.update(v)
        cache[include_headers] = fp.hexdigest()

    fingerprint = cache[include_headers]
    return fingerprint
