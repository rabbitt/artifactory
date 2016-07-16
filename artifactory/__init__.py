#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:expandtab
#
# ==================================================================
#
# Copyright (c) 2005-2014 Parallels Software International, Inc.
# Released under the terms of MIT license (see LICENSE for details)
#
# ==================================================================
#
# pylint: disable=no-self-use, maybe-no-member

""" artifactory: a python module for interfacing with JFrog Artifactory

This module is intended to serve as a logical descendant of pathlib
(https://docs.python.org/3/library/pathlib.html), a Python 3 module
 for object-oriented path manipulations. As such, it implements
everything as closely as possible to the origin with few exceptions,
such as stat().

There are PureArtifactoryPath and ArtifactoryPath that can be used
to manipulate artifactory paths. See pathlib docs for details how
pure paths can be used.
"""

from . import exceptions

from copy import deepcopy as copy
__all__ = copy(exceptions.__all__)

from .exceptions import *
from .utils import export
from .paths import ArtifactoryPath, PureArtifactoryPath
from .config import Config

export(ArtifactoryPath)
export(PureArtifactoryPath)
