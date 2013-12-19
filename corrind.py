#!/usr/bin/env python
#coding:utf-8
# Author:  Jianpo Ma
# Purpose:
# Created: 2013/11/24

import logging
import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import os.path
import uuid

from tornado.options import define, options

define("port", default=8112, help='run on the given port', type=int)

