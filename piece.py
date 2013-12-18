#!/usr/bin/env python
#coding:utf-8
# Author:   Haiyang Peng
# Purpose:
# Created: 2013/7/02

import random
import string
from dbi import t_server
from dbi import session
from node import Server


class KeyWordException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class NothingFoundException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class Piece(Server):
    def __init__(self, name=None, *keywords):
        super(Piece, self).__init__()
        chars = string.ascii_letters + string.digits
        salt = ''.join(random.sample(chars, 8))
        self.knife = Knife(*keywords).knife
        self.name = name if not name else salt
        self.breed()

    def breed(self):
        '''繁殖出整个piece'''
        if not (self.childs is None) and len(self.childs) > 0:
            return len(self.childs)
        result = session.query(t_server)
        for value, col in self.knife.iteritems():
            result = result.filter(col == value)
        result = result.all()
        if result is None or len(result) == 0:
            raise NothingFoundException(self.knife.keys())
        for i in result:
            print i
            #self.add_child(Server(i.id))
        return len(result)


class Knife(object):
    def __init__(self, *keywords):
        self.words = self._all_words()
        self.knife = {}
        for i in keywords:
            if i in self.words.keys():
                self.knife[i] = self.words[i]
            else:
                raise KeyWordException(i)

    def _all_words(self):
        words = []
        words += self._get_word(t_server.region)
        words += self._get_word(t_server.product)
        words += self._get_word(t_server.role)
        words += self._get_word(t_server.dbms)
        words += self._get_word(t_server.vender)
        words += self._get_word(t_server.os_type)
        words += self._get_word(t_server.os_release)
        words += self._get_word(t_server.os_arch)
        words += [('reserve', t_server.is_reserve)]
        words = dict(words)
        return words

    def _get_word(self, col):
        ret = session.query(col).filter(col != None).distinct().all()
        return [(str(x[0]), col) for x in ret]


