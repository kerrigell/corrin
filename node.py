#!/usr/bin/env python
#coding:utf-8
# Author:   Jianpo Ma
# Purpose:
# Created: 2013/6/17

import sys
import datetime

from fabric.api import run, env, task, parallel, settings, hide, open_shell
from fabric.utils import puts
from fabric.colors import *
from fabric.tasks import execute
from fabric.exceptions import NetworkError
from fabric.contrib.files import exists as fexists
from fabric.state import connections
import traceback
import uuid as muuid
from itertools import izip
import pdb
import pprint
import string
import ConfigParser
import os.path
import time
import threading
import thread
from Queue import Queue

import prettytable


reload(sys)
sys.setdefaultencoding('latin1')

########################################################################
class NodeNet(object):
    """"""
    # the node that watched by someone on this net
    current_node = None
    # db table name
    __dbtable__= None
    # db table class
    __dbclass__ = None
    # the map of objects
    __nodemap__ = {}
    # foreign class
    __foreignclass__ = None

    # encoding 
    encoding = 'gbk'
    #----------------------------------------------------------------------
    
    @classmethod
    def get_dbclass(cls):
        if  cls.__dbclass__ is not None:
            return cls.__dbclass__      
        if cls.__dbtable__ is None:
            return None
        dbclassname=cls.__dbtable__ 
        dbclass = None
        import importlib
        module_name='dbi'
        mo = importlib.import_module(module_name)
        if mo:
            if hasattr(mo, dbclassname):
                dbclass = getattr(mo, dbclassname)
                if dbclass :
                    cls.__dbclass__ = dbclass
                    return dbclass
                else:
                    raise "There is no class of %s in %s module" % ( dbclassname, module_name)
            else:
                return None
        else:
            return None




    def __init__(self, node_id ,  foreignclass=None):
        """Constructor"""
        # search __nodemap__
        if self.__nodemap__.has_key(node_id):
            self=self.__nodemap__[node_id]
            return
        # mapped into db table class
        if self.__dbclass__ is None and self.__dbtable__ is not None:
            self.get_dbclass()
        
        # node relation property
        self.s = self.get_dbclass().get(node_id,first=True) if self.__dbclass__ else None
        if self.s is None:
            raise Exception("Error: Can't find the information record: %s" % node_id)
        self.dbid = None if self.s is None else self.s.id
        self.parent = None
        self.childs = None
        self.root = self
        self.level = 0
        self._iter_step = None
        self._iter_parent = None
        # join __nodemap__
        if self.dbid and not self.__nodemap__.has_key(self.dbid):
            self.__nodemap__[self.dbid] = self
        # cross to foreignclass node map
        if foreignclass:
            self.__foreignclass__ = foreignclass
            self.foreignnode=None
            self.dockapply()
        # init  current node if not exists
        self.set_current_node(self)

        
    def add_child(self, child):
        if child is None or not isinstance(child, self.__class__):
            return False
        if self.childs is None:
            self.childs = {}
        child.root = self.root
        child.level = self.level + 1
        child.parent = self
        self.childs[child.dbid] = child  
        return True
            
    @classmethod
    def get_node(cls, dbid):
        if cls.__nodemap__.has_key(dbid):
            return cls.__nodemap__[dbid]
        dbinfo = cls.get_dbclass().get(dbid,first=True)
        if not dbinfo: return None
        parent_node = cls.get_node(dbinfo.pid)
        if dbinfo.pid != 0 and parent_node is None:
            return None
        self_node = cls(dbid, cls.__foreignclass__)
        if dbinfo.pid != 0:
            parent_node.breed()
            parent_node.add_child(self_node)
        return self_node


    def breed(self, recursion=False):
        '''依据自身.dbid值，繁殖子节点：返回子嗣数量'''
        if not (self.childs is None) and len(self.childs) > 0:
            return len(self.childs)

        for child_info in self.get_dbclass().get(self.dbid,"pid"):
            if self.childs is None:
                self.childs={}
            if self.__nodemap__.has_key(child_info.id):
                continue
            child_node=self.__class__(child_info.id,self.__foreignclass__)
            self.add_child(child_node)
            if recursion:
                child_node.breed(recursion)
        return 0 if self.childs is None else len(self.childs)
                
                
                
        #if result is None or len(result) == 0:
            #self.childs = {}
            #return 0
        #for i in result:
            #child_node = self.__class__(i.id, self.__foreignclass__)
            #self.add_child(child_node)
            #child_count += 1
            #if recursion:
                #child_count += child_node.breed(recursion)
        #return len(self.childs)

    def __iter__(self):
        self._iter_step = self.level - 1
        self._iter_parent = self
        return self

    def next(self):
        if self._iter_step < 0:
            self._iter_step = self.level
            raise StopIteration
        self._iter_parent = self._iter_parent.parent
        self._iter_step -= 1
        return self._iter_parent
    
    @classmethod
    def set_current_node(cls,node,force=False):
        if cls.current_node is None:
            cls.current_node=node
        if force:
            cls.current_node=node

    def print_structure(self):
        print "%s+-%s" % (string.ljust('', self.level * 4), self)
        if self.childs:
            for i in self.childs.values():
                i.print_structure() 
    def pwd(self):
        for i in self:
            print "%s+-%s" % (string.ljust('', i.level * 4), i)
            

    def dockapply(self):
        if (self.s is None or  
           self.__dbclass__ is None or 
           self.__foreignclass__ is None or 
           self.__dbclass__ is None  or 
           not hasattr(self.__dbclass__, string.lower("%s_id" % self.__foreignclass__.__name__))):
            return False
        foreignid = getattr(self.s, string.lower("%s_id" % self.__foreignclass__.__name__))
        if foreignid:
            self.__foreignclass__.dockhandle(self, foreignid)
            return True
        else:
            return False

    @classmethod
    def dockhandle(cls, applicant, searchid):
        the_node = cls.get_node(searchid)
        if the_node is None:
            return False
        else:
            the_node.foreignnode = applicant
            applicant.foreignnode = the_node


    @classmethod
    def cd(cls, dbid):
        dbid = string.strip(dbid)
        cnode = cls.current_node
        if dbid == '.':
            cnode = cls.current_node
        elif dbid == '..':
            if cls.current_node.parent is not None:
                cnode = cls.current_node.parent
        elif dbid == '~':
            cnode = cls.current_node.root
        else:
            cdbid = int(dbid)
            if cdbid is None or cdbid == 0:
                return cls.current_node
            else:
                if cdbid is not None and cdbid != 0:
                    if cls.current_node.childs.has_key(cdbid):
                        cnode = cls.current_node.childs[cdbid]
                    else:
                        cnode=cls.get_node(cdbid)
        if cnode.childs is None:
            cnode.breed()
        cls.current_node = cnode
        return cls.current_node


class Feature(NodeNet):
    """"""
    __nodemap__ = {}
    current_node = None

    def __init__(self, dbid=None, tablename=None, foreignclass=None):
        super(Feature, self).__init__(dbid, tablename,foreignclass)

    def __str__(self):
        return "<%s:%s>" % (self.s.feature, self.s.detail)

    def print_structure(self):
        print "%s+-%s" % (string.ljust('', self.level * 4), "%s---%s->%s" % (
            self, self.foreignnode.__class__.__name__, self.foreignnode) if self.foreignnode else self)
        for i in self.childs.values():
            i.print_structure()

    def __str__(self):
        if self.s is None:
            return 'None'
        return ("%s[%s:%s]%s" % (self.s.detail, self.dbid, '' if self.parent is None else self.parent.s.detail,
                                 '' if self.foreignnode is None else "-->%s" % self.foreignnode))


class ExecuteOut(object):
    def __init__(self, inst=None):
        self.return_code = -99
        self.result = ''
        self.succeed = False
        self.elapsed = 0
        self.instance = inst

    def __str__(self):
        return """Code: %s Result: \n%s""" % (self.return_code, self.result)


class Server(NodeNet):
    """Server.s --->  sqlobject ---> TABLE:servers"""
    __nodemap__ = {}
    current_node = None
    __dbtable__ = 't_server'

    def __init__(self, dbid=0,  foreignclass=None):
        """Constructor"""
        super(Server, self).__init__(dbid,
                                     foreignclass)


    def run(self):
        pass


    def __getitem__(self, index):
        '''Get the item of the access way'''
        #print 'getitem_index: %s' % index
        try:
            for i in range(self.level - index):
                it = it.parent
            return it
        except Exception, e:
            self._print_error(e)

    def __str__(self):
        return (
            "%s:%s:%s[%03d:%s]" % (
            self.s.region, self.s.product, self.s.ip_oper, self.dbid, self.s.description)).encode(
            self.encoding)

    def __len__(self):
        return self.level



    def _print_error(self, e):
        puts('%s Error: #%d %s' % (self.s.ip_oper, e.args[0], e.args[1]))

    def search(self, addr):
        def _search(addr, start):
            if start.s.ip_oper == addr:
                return start
            for value in start.childs.values():
                result = _search(addr, value)
                if result:
                    return result

        root = self if (self.root is None) else self.root
        return _search(addr, root)

    @classmethod
    def disconnect_all(cls):
        for key in connections.keys():
            connections[key].close()
            del connections[key]

    def execute(self, cmd,
                hide_running=True, hide_stdout=True, hide_stderr=False, hide_puts=False, showprefix=None,
                hide_warning=True, password=None, abort_on_prompts=True, hide_server_info=False):
        class FabricAbortException(Exception):
            def __str__(self):
                return repr('Fabric Abort Exception:%s', self.message)
            def __call__(self,x):
                print  "Error Fabric Abort Exception: %s -%s" % (self.message,str(x))


        out = ExecuteOut(inst=self)
        out.return_code = -99
        out.result = ''
        out.succeed = False
        starttime = time.time()
        host_string = '%s@%s' % (self.s.loginuser, '127.0.0.1' if self.root == self else self.s.ip_oper)
        gateway_string = "%s@%s" % (
            self.parent.s.loginuser, self.parent.s.ip_oper) if self.level == 2 and self.parent is not None else None
        try:
            if self.s.role in ['rds']:
                raise Exception("This server role is %s: can't execute any cmd" % self.s.role)

            hiding_clause = (
                'running' if hide_running else None, 'stdout' if hide_stdout else None,
                'stderr' if hide_stderr else None)
            hiding_clause = [x for x in hiding_clause if x]
            with settings(hide(*hiding_clause),
                          host_string=host_string,
                          gateway=gateway_string,
                          skip_bad_hosts=True,
                          abort_exception=FabricAbortException(),
                          connection_attempts=1,
                          disable_known_hosts=True,
                          timeout=5,
                          command_timeout=5,
                          colorize_errors=True,
                          abort_on_prompts=abort_on_prompts,
                          warn_only=hide_warning,
                          password=password if password else None,
                          output_prefix=False,
                          eagerly_disconnect=True,
                          keepalive=5,
                          parallel=True):
                result = run(cmd, shell=False, timeout=5)
                out.result = str(result)
                if hasattr(result, 'return_code'):
                    out.return_code = result.return_code
                if not hide_server_info:
                    puts(yellow(
                        "%s ReturnCode:%s" % (str(self), result.return_code if hasattr(result, 'return_code') else '')),
                         show_prefix=showprefix, flush=True)
                if result.succeeded:
                    if not hide_puts:
                        puts(green(result), show_prefix=showprefix, flush=True)
                    out.succeed = True
                if result.failed:
                    out.succeed = False
                    if not hide_puts:
                        puts(red(result), show_prefix=showprefix, flush=True)
        except NetworkError, e:
            out.succeed = False
            out.result = "Error: %s \n #%s" % (host_string, e)
            if not hide_puts:
                puts(red(out.result))
        except Exception, e:
        #  traceback.print_exc()
            out.succeed = False
            out.result = "Error: %s \n #%s" % (host_string, e)
            if not hide_puts:
                puts(red(out.result))
                #   print '%s Error: #%d %s' % (target.address, e.args[0], e.args[1])
        finally:
            endtime = time.time()
            out.result = string.strip(out.result)
            out.elapsed = endtime - starttime
            return out


    def login(self, cmd=None):
        if self.s.role in ['rds']:
            print "This server role is %s: can't login " % self.s.role
            return
        host_string = '%s@%s' % (self.s.loginuser, '127.0.0.1' if self.root == self else self.s.ip_oper)
        gateway_string = "%s@%s" % (
            self.parent.s.loginuser, self.parent.s.ip_oper) if self.level == 2 and self.parent is not None else None
        try:
            #if self.level > 2:
            #    raise Exception("Don't supply operation on 4 round")
            with settings(host_string=host_string,
                          gateway=gateway_string,
                          eagerly_disconnect=True,
                          remote_interrupt=False):

            #hiding_clause = (
            #'running' if hide_running else None, 'stdout' if hide_stdout else None, 'stderr' if hide_stderr else None)
            #hiding_clause = [x for x in hiding_clause if x]
            #with settings(hide(*hiding_clause), warn_only=True):
            #    #env.skip_bad_hosts=True
            #    env.connection_attempts = 2
            #    #env.disable_known_hosts=True
            #    env.eagerly_disconnect=True
            #    env.abort_on_prompts = True
            #    #env.warn_only=True
            #    env.output_prefix = False if hide_output_prefix else False
                open_shell(cmd)

        except NetworkError, e:
        #pdb.set_trace()
        #traceback.print_exc()
        # print '%s Error: #%d %s' % (target.address, e.args[0], e.args[1])
        #  return ''
        #   puts('%s Error: #%d %s' % (target.address,e.args[0], e.args[1]))
            puts(red("Error: %s \n #%s" % (host_string, e)))
            return 0
        except Exception, e:
        #pdb.set_trace()
        #traceback.print_exc()
        #   puts('%s Error: #%d %s' % (target.address,e.args[0], e.args[1]))
        #   print '%s Error: #%d %s' % (target.address, e.args[0], e.args[1])
            puts(red("Error: %s \n #%s" % (host_string, e)))
            return 0

    @staticmethod
    def _print_result(result, showprefix=None, info=''):
        puts(yellow("%s ReturnCode:%s" % (info, result.return_code if hasattr(result, 'return_code') else '')),
             show_prefix=showprefix, flush=True)
        if result.succeeded:
            puts(green(result), showprefix=showprefix, flush=True)
        if result.failed:
            puts(yellow(red(result), show_prefix=showprefix, flush=True))

            #def infect_execute(self,cmd,extent=False):
            #'''infect a file or command to childs or whole'''
            #if self.childs is None:
            #self.breed()
            #for i in self.childs.values():
            #i.execute(cmd)
            #if extent:
            #i.infect_execute(cmd,extent)

    def get_childs(self, recursion=False):
        serverlist = []
        if self.childs is None:
            self.breed()
        for i in self.childs.values():
            serverlist.append(i)
            if recursion:
                serverlist += i.get_childs(recursion)
        return serverlist

    def exists(self, path):
        host_string = '%s@%s' % (self.s.loginuser, '127.0.0.1' if self.root == self else self.s.ip_oper)
        gateway = self.parent.s.ip_oper if self.level == 2 and self.parent is not None else None
        result = False
        try:
            with settings(host_string=host_string,
                          gateway=gateway,
                          skip_bad_hosts=True,
                          connection_attempts=2,
                          disable_known_hosts=True,
                          eagerly_disconnect=True,
                          abort_on_prompts=True,
                          warn_only=False
            ):
                result = fexists(path)

        except NetworkError, e:
            result = False
        except Exception, e:
            result = False
        finally:
            return result
        return result


    @classmethod
    def piece(cls, line):
        if cls.__dbclass__ is None:
            return None
        #dbids = cls.__dbclass__.piece(line)
        serverlist = []
        for i in cls.get_dbclass().piece(line):
            tnode = cls.get_node(i)
            if tnode:
                serverlist.append(tnode)
        return serverlist

    def add_child_info(self, region, product, role, ip_oper, description, loginuser='root'):
        self.get_dbclass().add(pid=self.dbid,
                              ip_oper=ip_oper,
                              description=description,
                              region=region,
                              product=product,
                              role=role,
                              loginuser=loginuser
        )



    @classmethod
    def walk(cls, source_server, dest_server):
        #seach child
        if source_server is None or dest_server is None or type(source_server) != cls or type(dest_server) != cls:
            return []
        start = [source_server] + [x for x in source_server]
        end = [dest_server] + [x for x in dest_server]
        same = [x for x in start if x in end]
        result = start[:start.index(same[0])] + same[0:1] + end[:end.index(same[0])][::-1]
        #   end=end.reverse()
        #tmp=start + end
        #result=sorted(set(tmp),key=tmp.index)
        return result
    
    def _transfer(self):
            walkpath = self.server.walk(self.server, value)
            for (src_srv, dst_srv) in map(None, walkpath, walkpath[1:]):
                if src_srv is not None and not self.trans_list.has_key(src_srv.dbid):
                    self.trans_list[src_srv.dbid] = [src_srv, 0, None]
                if dst_srv is not None and not self.trans_list.has_key(dst_srv.dbid):
                    self.trans_list[dst_srv.dbid] = [dst_srv, 0, None]
                if dst_srv is None and self.trans_list.has_key(src_srv.dbid):
                    print "%s+-->%s" % (string.ljust(' ', src_srv.level * 4, ) + str(src_srv), str(dst_srv)),
                    if self.trans_list[src_srv.dbid][1] == 1:
                        if src_srv.exists(os.path.join(self.tmppath, self.uuid)):
                            if not src_srv.exists(dest_path):
                                src_srv.execute("mkdir -p %s" % dest_path, hide_stdout=True,
                                                hide_puts=True, hide_server_info=True)
                            exe_result = src_srv.execute("""mv %s %s %s %s""" % (
                                os.path.join(self.tmppath, self.uuid), os.path.join(dest_path, self._lfile)
                                , (" && chmod -R %s %s" % (mode, os.path.join(dest_path, self._lfile))) if mode else ''
                                ,
                                (" && chown -R %s %s" % (owner, os.path.join(dest_path, self._lfile))) if owner else ''
                            ), hide_stdout=True, hide_puts=True, hide_server_info=True)
                            if exe_result.succeed:
                                self.trans_list[src_srv.dbid][1] = 0
                                print 'move finished'
                            else:
                                print 'move failed:%s' % exe_result.result
                        else:
                            print 'No target:%s' % os.path.join(self.tmppath, self.uuid)
                    elif self.trans_list[src_srv.dbid][1] > 1:
                        if src_srv.exists(os.path.join(self.tmppath, self.uuid)):
                            if not src_srv.exists(dest_path):
                                src_srv.execute("mkdir -p %s" % dest_path, hide_stdout=True,
                                                hide_puts=True, hide_server_info=True)
                            exe_result = src_srv.execute("""cp -r  %s %s   %s   %s""" % (
                                os.path.join(self.tmppath, self.uuid), os.path.join(dest_path, self._lfile)
                                , (" && chmod -R %s %s" % (mode, os.path.join(dest_path, self._lfile))) if mode else ''
                                ,
                                (" && chown -R %s %s" % (owner, os.path.join(dest_path, self._lfile))) if owner else ''
                            ), hide_stdout=True, hide_puts=True, hide_server_info=True)
                            if exe_result.succeed:
                            #  self.trans_list[src_srv.dbid][1]=0
                                print 'copy finished'
                            else:
                                print 'copy failed:%s' % exe_result.result
                        else:
                            print 'No target:%s' % os.path.join(self.tmppath, self.uuid)
                    continue
                if src_srv.level > dst_srv.level and self.trans_list.has_key(src_srv.dbid) and self.trans_list.has_key(
                        dst_srv.dbid):
                    if self.trans_list[dst_srv.dbid][1] > 0 or dst_srv.exists(os.path.join(self.tmppath, self.uuid)):
                        self.trans_list[dst_srv.dbid][1] += 1
                    else:
                        print "%s+-->%s" % (string.ljust(' ', src_srv.level * 4, ) + str(src_srv), str(dst_srv)),
                        exe_result = dst_srv.execute(
                            "scp -r %s:%s %s" % ("%s@%s" % (src_srv.s.loginuser, src_srv.s.ip_oper)
                                                 , self.source_path if src_srv == self.server else os.path.join(
                                self.tmppath, self.uuid)
                                                 , os.path.join(self.tmppath,
                                                                self.uuid) if src_srv == self.server else os.path.join(
                                self.tmppath)
                            ), hide_stdout=True, hide_puts=True, hide_server_info=True)
                        if exe_result.succeed:
                            self.trans_list[dst_srv.dbid][1] += 1
                            self.trans_list[dst_srv.dbid][2] = 'OK'
                            print 'ok'
                        else:
                            self.trans_list[dst_srv.dbid][2] = 'Error:%s' % exe_result.result
                            print 'Error:%s' % exe_result.result
                            break
                elif src_srv.level < dst_srv.level and self.trans_list.has_key(
                        src_srv.dbid) and self.trans_list.has_key(dst_srv.dbid):
                    if self.trans_list[dst_srv.dbid][1] > 0 or dst_srv.exists(os.path.join(self.tmppath, self.uuid)):
                        self.trans_list[dst_srv.dbid][1] += 1
                    else:
                        print "%s+-->%s" % (string.ljust(' ', src_srv.level * 4, ) + str(src_srv), str(dst_srv)),
                        exe_result = src_srv.execute("scp -r %s %s:%s" % (
                            self.source_path if src_srv == self.server else os.path.join(self.tmppath, self.uuid)
                            , "%s@%s" % (dst_srv.s.loginuser, dst_srv.s.ip_oper)
                            ,
                            os.path.join(self.tmppath, self.uuid) if src_srv == self.server else os.path.join(
                                self.tmppath)
                        ), hide_stdout=True, hide_puts=True, hide_server_info=True)
                        if exe_result.succeed:
                            self.trans_list[dst_srv.dbid][1] += 1
                            self.trans_list[dst_srv.dbid][2] = 'OK'
                            print 'ok'
                        else:
                            self.trans_list[dst_srv.dbid][2] = 'Error:%s' % exe_result.result
                            print 'Error:%s' % exe_result.result
                            break
    def gets(self):
        pass
    def puts(self):
        pass




########################################################################
####http://blog.csdn.net/treesky/article/details/7088284###
__metaclass__ = type
class Operation(object):
    # db table name
    __dbtable__ = None
    # db table class
    __dbclass__ = None  
    # server instance
    server = None
    def __init__(self,server):
        """Constructor"""
    #    pdb.set_trace()
        if not isinstance(server,Server):
            raise Exception("Init Error: %s is not <Server> instance" % str(server))
        self.server=server
        if self.__dbclass__ is None and self.__dbtable__ is not None :
            self.get_dbclass()
    #@classmethod
    #def get_dbclass(cls,table_name=None):
        #if  cls.__dbclass__ is not None:
            #return cls.__dbclass__      
        #if table_name is None:
            #return None
        ##if table_name is None:
            ##selfclassname = cls.__name__
            ##dbclassname = "t_%s" % string.lower(selfclassname)
        ##else:
        #dbclassname=table_name
        #dbclass = None
        #import importlib
        #mo = importlib.import_module('dbi')
        #if mo:
            #if hasattr(mo, dbclassname):
                #dbclass = getattr(mo, dbclassname)
                #if dbclass :
                    #cls.__dbclass__ = dbclass
                    #return dbclass
            #else:
                #return None
        #else:
            #return None
        
    
    @classmethod
    def get_dbclass(cls):
        if  cls.__dbclass__ is not None:
            return cls.__dbclass__      
        if cls.__dbtable__ is None:
            return None
        dbclassname=cls.__dbtable__ 
        dbclass = None
        import importlib
        module_name='dbi'
        mo = importlib.import_module(module_name)
        if mo:
            if hasattr(mo, dbclassname):
                dbclass = getattr(mo, dbclassname)
                if dbclass :
                    cls.__dbclass__ = dbclass
                    return dbclass
                else:
                    raise "There is no class of %s in %s module" % ( dbclassname, module_name)
            else:
                return None
        else:
            return None

    

class IPsec(Operation):
    __dbtable__ = 't_ipsec'
    def __init__(self, server):
      #  Operation.__init__(self,server,"t_%s" % string.lower(self.__class__.__name__))
        super(IPsec, self).__init__(server)

    def add_filter(self, protocal, source_addr, dport, description, status=0, chain='INPUT'):
        try:
            self.get_dbclass().add(server_id=self.server.dbid,
                              protocal=protocal,
                              source_addr=source_addr,
                              dport=dport,
                              description=description,
                              status=status,
                              chain=chain)
        except:
            pass


    def del_filter(self, dbid):
        pass
    def get_filters(self):
        exec_result=self.server.execute("iptables-save", hide_puts=True, hide_server_info=True)
        if exec_result.succeed:
            dbsession,dbclass = self.get_dbclass()
            for line in exec_result.result.splitlines(True):
                if not  line.startswith('-A'):
                    continue
                line=iter(line.strip().split())
                line=dict(zip(line,line))
                if  (line.has_key('-m') and line['-m'] == 'state') and line.has_key('--state'):
                    continue
                if line['-j'] == 'ACCEPT':
                    self.add_filter(line['-p']  if line.has_key('-p') else 'all',
                                    line['-s'],
                                    line['--dports'] if line.has_key('--dports') else None ,
                                    None,
                                    1,
                                    line['-A'])
            print "Collect from %s: Finished" % self.server
        else:
            print "Collect from %s: Failed -> %s" % (self.server,exec_result.result)
    def clear_filters(self):
        try:
            self.get_dbclass().delete(self.server.dbid,"server_id")
            print "clear finished"
        except:
            pass
 

    def print_filter(self):
        res_title=["dbid", "chain", 'source', 'dport', 'description']
        #res_list = self.get_dbinfo()
        
        res_table=prettytable.PrettyTable(res_title)
        for col_name in res_title[1:]:
            res_table.align[col_name]='l'
        res_table.padding_width = 1
        res_table.encoding = self.server.encoding  
        #for i in res_list:
        for i in self.get_dbclass().get(self.server.dbid,"server_id"):
            res_table.add_row([i.id, i.chain, i.source_addr, i.dport, i.description])
        
        print res_table        


    def make_script(self):
        filterlist = ''
        if self.server.parent is not None:
            if self.server.parent.s.ip_public is None or self.server.parent.s.ip_private is None:
                print 'Please fill in the public and private address. And repeat'
                return None
            parent_iplist = []
            parent_iplist.append(self.server.parent.s.ip_public)
            parent_iplist.append(self.server.parent.s.ip_private)
            parent_iplist.append(self.server.parent.s.ip_oper)
            parent_iplist = [i for i in parent_iplist if i]
            parent_iplist = list(set(parent_iplist))

            for item in parent_iplist:
                filterlist += '''$IPTABLES -I INPUT -s %s -p tcp --dport 22 -j ACCEPT; #cc:%s\n''' % (
                    item, self.server.parent)

        for i in self.get_dbclass().get(self.server.dbid,"server_id"):
            filterlist += '''$IPTABLES -I %s -s %s -p %s -m multiport --dport %s -j ACCEPT; #%s\n''' % (
                i.chain, i.source_addr, i.protocal, i.dport, i.description)

        ipsec_temp = '''
IPTABLES=/sbin/iptables;
$IPTABLES -F;
$IPTABLES -Z;
$IPTABLES -X;

$IPTABLES -t mangle -F;
$IPTABLES -t mangle -Z;
$IPTABLES -t mangle -X;


$IPTABLES -P INPUT  ACCEPT;

$IPTABLES -I INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT;
$IPTABLES -I OUTPUT -m state --state NEW,ESTABLISHED,RELATED -j ACCEPT ;

%s

$IPTABLES -I INPUT -s 127.0.0.1 -j ACCEPT;
$IPTABLES -P INPUT  DROP;
$IPTABLES -P FORWARD DROP ;
$IPTABLES -P OUTPUT ACCEPT ;
service iptables save;
chkconfig --level=2345 iptables on
    
    ''' % filterlist
        return ipsec_temp

    def reload(self):
        script = self.make_script()
        if script:
            self.server.execute(script)

    def status(self):
        cmd = "iptables -nvL"
        return self.server.execute(cmd)
    def script(self):
        print self.make_script()


class Iptables_rules(object):
    # db table class
    __dbclass__ = None
    # db session
    __dbsession__ = None

    #----------------------------------------------------------------------
    @classmethod
    def _get_dbclass(cls):
        if cls.__dbsession__ and cls.__dbclass__:
            return True
        selfclassname = cls.__name__
        dbclassname = "t_%s" % string.lower(selfclassname)
        dbclass = None
        dbsession = None
        import importlib

        mo = importlib.import_module('dbi')
        if mo:
            if hasattr(mo, dbclassname):
                dbclass = getattr(mo, dbclassname)
            if hasattr(mo, 'session'):
                dbsession = getattr(mo, 'session')
            if dbclass and dbsession:
                cls.__dbsession__ = dbsession
                cls.__dbclass__ = dbclass
                return True
            else:
                return False

    @classmethod
    def _get_dbinfo(cls, dbid=None):
        if not cls._get_dbclass():
            return None
        result = None

        if dbid is not None:
            result = cls.__dbsession__.query(cls.__dbclass__).filter(cls.__dbclass__.server_id == dbid).all()
        cls.__dbsession__.close()
        return result

    def _generate_rules(self, raw_rules=None, trx_id=None):
        try:
            status = None
            rules = {trx_id: []}
            Table = None
            for line in raw_rules:
                line = line.strip()
                if line.startswith('# Generated'):
                    status = "started"
                elif line.startswith('*'):
                    Table = line.strip('*')
                elif line.startswith(':'):
                    if status == "started" and Table:
                        Index = 0
                        Chain = line.strip(':').split()[0]
                        Policy = line.strip(':').split()[1]
                        rule = {Table: {Chain: {Index: {'POLICY': Policy}}}}
                        rules[trx_id].append(rule)
                    else:
                        raise "Logical errors during parsing iptables rules"
                elif line.startswith('-'):
                    if status == "started" and Table:
                        Index += 1
                        line = line.split()
                        Chain = line[1]
                        i = iter(line)
                        rule = {Table: {Chain: {Index: dict(zip(i, i))}}}
                        rules[trx_id].append(rule)
                    else:
                        raise "Logical errors during parsing iptables rules"
                elif line.startswith('# Completed'):
                    status = "Ended"
        except:
            pass
        return rules

    def _load_rules(self, trx_id=None):
        pass

    def __init__(self, srv, raw_rules=None, trx_id=None):
        if srv is None:
            raise "Server Is Null"
        if type(srv) != Server:
            raise "param type is not Server"
        self.server = srv
        self.trx_id = trx_id
        self.rules = None
        if raw_rules and self.trx_id:
            self.rules = self._generate_rules(raw_rules=raw_rules, trx_id=self.trx_id)
        elif not raw_rules and self.trx_id:
            self.rules = self._load_rules(trx_id=self.trx_id)
        if self.__class__.__dbsession__ is None or self.__class__.__dbclass__ is None:
            self._get_dbclass()

    def save_rules_to_db(self):
        dbsession = self.__class__.__dbsession__
        dbclass = self.__class__.__dbclass__
        try:
            for rule in self.rules[self.trx_id]:
                for table, table_rule in rule.items():
                    for chain, chain_rule in table_rule.items():
                        for index, rule_args in chain_rule.items():
                            for opt, arg in rule_args.items():
                                dbsession.add(dbclass(
                                    trx_id=self.trx_id,
                                    index=index,
                                    table=table,
                                    chain=chain,
                                    opt=opt,
                                    arg=arg
                                ))
            dbsession.commit()
            dbsession.close()
        except Exception as e:
            print "Error: %s" % e


class Iptables(object):
    # db table class
    __dbclass__ = None
    # db session
    __dbsession__ = None

    #----------------------------------------------------------------------
    @classmethod
    def _get_dbclass(cls):
        if cls.__dbsession__ and cls.__dbclass__:
            return True
        selfclassname = cls.__name__
        dbclassname = "t_%s" % string.lower(selfclassname)
        dbclass = None
        dbsession = None
        import importlib

        mo = importlib.import_module('dbi')
        if mo:
            if hasattr(mo, dbclassname):
                dbclass = getattr(mo, dbclassname)
            if hasattr(mo, 'session'):
                dbsession = getattr(mo, 'session')
            if dbclass and dbsession:
                cls.__dbsession__ = dbsession
                cls.__dbclass__ = dbclass
                return True
            else:
                return False

    @classmethod
    def _get_dbinfo(cls, dbid=None):
        if not cls._get_dbclass():
            return None
        result = None

        if dbid is not None:
            result = cls.__dbsession__.query(cls.__dbclass__).filter(cls.__dbclass__.server_id == dbid).all()
        cls.__dbsession__.close()
        return result

    def __init__(self, srv):
        if srv is None:
            raise "Server Is Null"
        if type(srv) != Server:
            raise "param type is not Server"
        self.server = srv
        self.rules = None
        if self.__class__.__dbsession__ is None or self.__class__.__dbclass__ is None:
            self._get_dbclass()
            self.rules = self._get_dbinfo(dbid=srv.dbid)

    def save_from_server(self):
        all_rules = self.server.execute('iptables-save', hide_puts=True, hide_server_info=True)
        dbsession = self.__class__.__dbsession__
        dbclass = self.__class__.__dbclass__
        if all_rules.succeed:
            trx_id = str(muuid.uuid4()).rsplit('-', 3)[0]
            trx_time = time.strftime("%Y%m%d%H%M%S")
            rules = Iptables_rules(self.server, raw_rules=all_rules.result.splitlines(True), trx_id=trx_id)
            rules.save_rules_to_db()
            dbsession.add(dbclass(
                server_id=self.server.dbid,
                trx_id=trx_id,
                trx_time=trx_time))
        dbsession.commit()
        dbsession.close()


class Nagios(Operation):
    config = None
    centreon = None
    operation_step = [
        ['check current status', 'check'],
        ['upgrade perl from v5.8.5 to v5.8.9', 'upgrade_perl'],
        ['create nagios user', 'create_user'],
        ['instal nrpe and nagios plug-in', 'install_tools'],
        ['deploy all monitor scripts', 'deploy_script'],
        ['open ping and 5666 for nagios monitor servers', 'config_iptables'],
        ['update your nrpe commands', 'update_nrpe_cfg'],
        ['update ntp server address in your nrpe.cfg', 'update_nrpe_ntp'],
        ['change statliate nagios ip', 'change_satellite_ip'],
        ['config xinetd service', 'config_xinetd'],
        ['restart service', 'restart_service'],
        ['review all your commands currently defined in nrpe.cfg', 'review_nrpe'],
        ['test monitor script', 'test_script'],
        ['show nrpe.cfg', 'show_nrpe'],
    ]
    
               #"""cd /tmp && \
               #tar zxf Sys-Statistics-Linux-0.66.tar.gz && \
               #cd Sys-Statistics-Linux-0.66 && \
    install_config = {
        'is_installed_Linux_pm': ['tools', 'Linux_pm', 'client/tools/', '/tmp/',
               """
               perl Makefile.PL 1> /dev/null; \
               make 1> /dev/null && \
               make install 1> /dev/null""",
                                                #make test &> /dev/null && \
                                                #    'is_install_perl-devel'
                                                None],
        
                #"""cd /tmp && \
               #tar zxf nagios-plugins-1.4.15.tar.gz && \
               #cd nagios-plugins-1.4.15 && \                            
        'is_installed_nagios_plugin': ['tools', 'nagios_plugin', 'client/tools/', '/tmp/',
               """./configure --with-nagios-user=nagios \
               --with-nagios-group=nagios \
               --with-openssl=/usr/bin/openssl \
               --enable-perl-modules \
               --enable-redhat-pthread-workaround \
               1>/dev/null && \
               make 1>/dev/null && \
               make install 1>/dev/null""", None],
        
        'is_openssl_devel': [None, None, None, None, None, None],
        
        
        #"""cd /tmp && \
        #rpm -ivh --nodeps xinetd-2.3.14-38.el6.x86_64.rpm """,         
        'is_install_xinetd': ['tools', 'xinetd', 'client/tools/', '/tmp/',
               """""", 
               None],
                      
        #"""cd /tmp &&
        #tar zxf nrpe-2.12.tar.gz &&
        #cd nrpe-2.12 &&                      
        'is_installed_nrpe': ['tools', 'nrpe', 'client/tools/', '/tmp/',
               """./configure 1>/dev/null &&
               make all 1>/dev/null &&
               make install-plugin 1>/dev/null &&
               make install-daemon  1>/dev/null &&
               make install-daemon-config 1>/dev/null &&
               make install-xinetd 1>/dev/null """, None],
        'is_installed_xinetd_nrpe': ['tools', 'xinetd_nrpe', 'client/tools/', '/etc/xinetd.d/', None,
                                                   None],
        
        'is_installed_utils_pm': ['tools', 'utils_pm', 'client/tools/', '/usr/local/nagios/libexec', None,
                                                None]
    }


    @classmethod
    def get_config(cls):
        if cls.config is None:
            cls.config = ConfigParser.SafeConfigParser()
            base_path = os.path.split(os.path.realpath(sys.argv[0]))[0]
            cls.config.read(os.path.join(base_path, "config/monitor.ini"))

    @classmethod
    def get_centreon_info(cls):
        try:
            if cls.centreon is None:
                cls.centreon = {}
                cls.centreon['server_id'] = int(cls.config.get('centreon_server', 'dbid'))
                cls.centreon['cli'] = cls.config.get('centreon_server', 'cli')
                cls.centreon['host_template'] = [i for i, j in cls.config.items('centreon_host_template')]
                cls.centreon['satelliate'] = dict(cls.config.items("centreon_satelite"))
                cls.centreon['host_group'] = [j for i, j in cls.config.items('centreon_server_group')]
            return True
        except Exception, e:
            print "Error: %s" % ( e)
            cls.centreon = None
            return False


    def __init__(self, server):
        super(Nagios, self).__init__(server)
        self.ip_monitor = self.server.s.ip_monitor
        self.get_config()
        self.get_centreon_info()
        self.status = {}
        self.base_dir = self.config.get('basic', 'base_dir')


    def check(self, output=True):
        print "[==>>check monitor status]"
        scripts = self.config.options('script')
        script_shell = ""
        for script in scripts:
            script_shell += """
                echo -n "is_installed_%s:";
                test -x /usr/local/nagios/libexec/%s \
                && echo True || echo False;
                """ % (script, script)
        shell = """
            %s

            echo -n "is_installed_Linux_pm:"
            INC=`perl -e 'print \"@INC\"'`;
            find ${INC} -name 'Linux.pm' -print 2> /dev/null \
            | grep -q 'Linux.pm' && echo True || echo False;
            
            echo -n "is_installed_nagios_plugin:";
            test -d /usr/local/nagios/libexec && echo True || echo False;

            echo -n "is_installed_nrpe:";
            test -d /usr/local/nagios/etc && echo True || echo False;

            echo -n "is_installed_utils_pm:";
            test -e /usr/local/nagios/libexec/utils.pm \
            && echo True || echo False;

            echo -n "version_perl:";
            perl -v |  egrep v[0-9\.]+ -o

            echo -n "is_ping_opened:";
            /sbin/iptables -nvL | grep icmp | grep -q '0.0.0.0\|%s' &>/dev/null\
            && echo True || echo False

            echo -n "is_5666_opened:";
            /sbin/iptables -nvL | grep 5666 | grep -q '%s' &>/dev/null\
            && echo True || echo False

            echo -n "is_configured_nrpe:";
            grep -q '%s' /etc/xinetd.d/nrpe &>/dev/null \
            && echo True || echo False
            
            echo -n "is_openssl_devel:";
            rpm  -qa | grep openssl-devel &>/dev/null \
            && echo True || echo False    
            
            echo -n "is_install_xinetd:";
            rpm  -qa | grep xinetd &>/dev/null \
            && echo True || echo False   
            
            echo -n "is_install_perl-devel:";
            rpm  -qa | grep perl-devel &>/dev/null \
            && echo True || echo False  
            
            echo -n "is_installed_xinetd_nrpe:";
            test -e /etc/xinetd.d/nrpe \
            && echo True || echo False;            
            
            """ % (script_shell, self.ip_monitor, self.ip_monitor, self.ip_monitor)
        raw_status = self.server.execute(shell, hide_puts=True)
        if raw_status.succeed:
            self.status = dict([x.split()[0].split(':') for x in raw_status.result.split('\n') if x])
            if output:
                names = self.status.keys()
                names.sort()
                for name in names:
                    print '%-40s    %s' % (name, self.status[name])

    def upgrade_perl(self, force=False):
        print "[==>>update perl]"
        if len(self.status) == 0:
            self.check(output=False)
            #   base_dir = self.config.get('basic', 'base_dir')
        file_name = self.config.get('tools', 'perl')
        perl_file = os.path.join(self.base_dir, "client/tools/", file_name)
        if True if force else (self.status['version_perl'] == 'v5.8.5' or self.status['version_perl'] == 'v5.8.8'):
            trans = Transfer(self.server.root, perl_file)
            trans.add_dest_server(self.server)
            trans.send('/tmp')
            trans.clear()
            exe_result = self.server.execute("""
                    cd /tmp/ && \
                    tar zxf perl-5.8.9.tar.gz && \
                    cd perl-5.8.9 && \
                    ./Configure -de &> /dev/null && \
                    make &> /dev/null && \
                    make test &> /dev/null && \
                    make install &> /dev/null && \
                    rm -f /usr/bin/perl && ln -s /usr/local/bin/perl /usr/bin/perl                    
                    """, hide_puts=True)
            if exe_result.succeed:
                print 'OK'
            else:
                print 'Error:' + exe_result.result

    def config_iptables(self, force=False):
        print "[==>>config iptables]"
        if len(self.status) == 0:
            self.check(output=False)
        if self.ip_monitor:
            if (True if force else self.status['is_ping_opened'] == 'False'):
                self.server.execute("""
                        /sbin/iptables -I INPUT -s %s -p icmp -j ACCEPT && service iptables save
                        """ % self.ip_monitor, hide_puts=True)
            if (True if force else self.status['is_5666_opened'] == 'False'):
                self.server.execute("""
                        /sbin/iptables -I INPUT -s %s -p tcp --dport 5666 -j ACCEPT && service iptables save
                        """ % self.ip_monitor, hide_puts=True)
        else:
            print "Error: Please entry the monitor ip in overseas db web, and retry"


    def deploy_script(self, force=False):
        print "[==>>deploy monitor script]"
        if not self.server.exists("/usr/local/nagios/libexec"):
            print "Not exists: %s. Please check %s status." % ("/usr/local/nagios/libexec","is_installed_nrpe")
            return
        if len(self.status) == 0:
            self.check(output=False)
            #   base_dir = self.config.get('basic', 'base_dir')
        scripts = self.config.items('script')
        deploy_list=[]
        package_scripts_cms=""
        deploy_cmd=""
        for key, value in scripts:
            if (True if force else self.status['is_installed_%s' % key] == 'False'):
                deploy_list.append(value)
                
        if len(deploy_list)>0:
            exe_result=self.server.root.execute("""cd %s && tar zcvf /tmp/monitor-scripts.tar.gz %s 1>/dev/null""" % (os.path.join(self.base_dir,"client/libexec/"),
                                                                                                           " ".join(deploy_list)
                                                                                                           ),
                                     hide_puts=True)
            if exe_result.succeed:
                trans = Transfer(self.server.root, """/tmp/monitor-scripts.tar.gz""")
                trans.add_dest_server(self.server)
                trans.send('/tmp/')
                trans.clear()
                deploy_cmd="""tar zxvf /tmp/monitor-scripts.tar.gz -C /usr/local/nagios/libexec 1>/dev/null && \
                              chmod -R +x /usr/local/nagios/libexec && \
                              grep -q nagios /etc/sudoers && \
                              sed -i 's/^Defaults    requiretty/#Defaults    requiretty/g' /etc/sudoers && \
                              %s""" % """ && """.join([ """(grep %s /etc/sudoers &>/dev/null || sed -i '/nagios/s/$/,%s/g' /etc/sudoers) || echo \"nagios ALL=NOPASSWD: %s\" >> /etc/sudoers  """ % (i,os.path.join('/usr/local/nagios/libexec', i),os.path.join('/usr/local/nagios/libexec', i)) for i in deploy_list])
                exe_result=self.server.execute(deploy_cmd , hide_puts=True)
                
                if exe_result.succeed:
                    print 'OK'
                else:
                    print 'Error:' + exe_result.result                              
                              


    def create_user(self):
        print "[==>>create negios user]"
        exe_result = self.server.execute("""grep nagios /etc/passwd &> /dev/null \
                || (chattr -i /etc/shadow /etc/passwd && \
                groupadd nagios &&  \
                useradd -M -s /sbin/nologin nagios -g nagios);\
                mkdir -p /usr/local/nagios/libexec/;
                """)
        if exe_result.succeed:
            print '%-30s' % 'OK'
            return True
        else:
            print '%-30s' % 'Error:' + exe_result.result
            return False

    def change_satellite_ip(self):
        print "[==>>change satellite ip]"
        satellite_ip = self.server.s.ip_monitor
        if not satellite_ip:
            tmp_ip = raw_input('You can complete the info on the DBA info web,or you can type nagios satliate ip:')
            if len(tmp_ip) > 7:
                satellite_ip = tmp_ip
            else:
                return
        if not self.server.exists("/etc/xinetd.d/nrpe"):
            print "Not exists: %s. Please check %s status." % ("/etc/xinetd.d/nrpe","is_install_xinetd")
            return
        exe_result = self.server.execute("""grep only_from /etc/xinetd.d/nrpe && \
                                          sed -i 's/only_from.*/only_from       =127.0.0.1 %s/g' /etc/xinetd.d/nrpe""" % satellite_ip)
        if exe_result.succeed:
            print "%-30s" % 'OK'
        else:
            print "%-30s" % 'Error:' + exe_result.result


    def restart_service(self):
        print "[==>>restart nrpe service]"
        exe_result = self.server.execute("""killall nrpe ;/etc/init.d/xinetd restart""")
        if exe_result.succeed:
            print "%-30s" % 'OK'
        else:
            print "%-30s" % 'Error:' + exe_result.result

    def install_tools(self, check_name, force=False):
        def _install_prepare_prefix(spath,sfile):
            slist=[]
            slist.append("cd %s" % spath)
            for ext in [".tar.gz",".rpm"]:
                if ext==".tar.gz" and sfile.endswith(ext):
                    slist.append("tar zxf %s" % sfile)
                    slist.append("cd %s" % string.split(sfile,ext)[0])
                    break
                elif ext==".rpm" and sfile.endswith(ext):
                    slist.append("rpm -ivh --nodeps %s" % sfile)
                    break
            if len(slist)== 1:
                return None
            else:
                return " && ".join(slist)        
        
        
        if len(self.status) == 0:
            self.check(output=False)
        if True if force and self.status.has_key(check_name) else (
            True if check_name and self.status[check_name] == 'False' else  False):
            value = self.install_config[check_name]
            up_condition = value[5]
            if up_condition is not None and self.status.has_key(up_condition) and self.status[up_condition] == 'False':
                print "Please do this operation first:%s" % up_condition
                return False

            config_section = value[0]
            config_key = value[1]
            middle_path = value[2]
            trans_path = value[3]
            exe_cmd = value[4]
            if config_section is None and config_key is None:
                return False
            print "[==>>Install pulgin: %s]" % check_name
            file_name = self.config.get(config_section, config_key)
            trans_file = os.path.join(self.base_dir, middle_path, file_name)
            trans = Transfer(self.server.root, trans_file)
            trans.add_dest_server(self.server)
            trans.send(trans_path)
            trans.clear()
            if exe_cmd:
                cmd_prefix=_install_prepare_prefix(trans_path,file_name)
                if cmd_prefix:
                    exe_cmd="%s && %s " % (cmd_prefix,exe_cmd)
                    exe_result = self.server.execute(exe_cmd, hide_stderr=True)
                    if exe_result.succeed:
                        print "%-30s" % 'OK'
                        self.status[check_name] = 'True'
                        return True
                    else:
                        print "%-30s" % 'Error:' + exe_result.result
                        return False
        else:
            return False


    def test_script(self):
        commands = self.config.items('test_commands')
        command_lines = ""
        for (command, command_line) in commands:
            command_lines += (command_line + ';')
        self.server.execute(command_lines)

    def show_nrpe(self):
        nrpes = self.config.items('nrpe')
        for name, value in nrpes:
            print "%-40s=%90s" % (name, value)

    def update_nrpe_cfg(self, nrpe_name=None):
        print '[==>>Update nrpe command in nrpe.cfg]'
        if not self.server.exists("/usr/local/nagios/etc/nrpe.cfg"):
            print "Not exists %s, Please check %s" % ("/usr/local/nagios/etc/nrpe.cfg","is_installed_nrpe")
            return
        nrpes = self.config.items('nrpe')
        shell = ""
        #  if nrpe_name and nrpe_name in nrpes
        for (name, value) in nrpes:
        #    print 'update nrpe script in nrpe.cfg:%s' % nrpe_name
            nrpe_line = "command[" + name + "]=" + value
            if nrpe_name:
                if nrpe_name == name:
                    shell += """
                            sed -i '/command\[%s/d' \
                            /usr/local/nagios/etc/nrpe.cfg;
                            echo "%s" >> \
                            /usr/local/nagios/etc/nrpe.cfg;
                            """ % (name, nrpe_line)
                    break
            else:
                shell += """
                        sed -i '/command\[%s/d' \
                        /usr/local/nagios/etc/nrpe.cfg;
                        echo "%s" >> \
                        /usr/local/nagios/etc/nrpe.cfg;
                        """ % (name, nrpe_line)
        print '[==>>Update nrpe command in nrpe.cfg: %s]' % (nrpe_name if nrpe_name else "ALL")
        self.server.execute(shell)

    def config_xinetd(self):
        print "[==>>config xinetd service]"
        if len(self.status) == 0:
            self.check(output=False)
        if self.status['is_install_xinetd'] == 'False':
            print 'Please install xinetd service first'
            return
        print 'Start to config xinetd service',
        exe_result = self.server.execute("""(grep nrpe /etc/services &> /dev/null  || echo "nrpe     5666/tcp    #nagios nrpe " >> /etc/services) && \
                                        chkconfig --level 345 xinetd on """)
        if exe_result.succeed:
            print 'OK'
        else:
            print 'Error:' + exe_result.result


    def review_nrpe(self):
        self.server.execute("""
                egrep -v '^#|^$' \
                /usr/local/nagios/etc/nrpe.cfg \
                | egrep '^command\[.*\]'
                """)

    def update_nrpe_ntp(self):
        print "[==>>update ntp server in nrpe.cfg]"
        ntp = string.strip(self.server.s.ip_ntp_server)
        if len(ntp) > 0:
            exe_result = self.server.execute(""" grep check_ntp /usr/local/nagios/etc/nrpe.cfg && \
                sed -i 's/check_ntp_time -H.*-w/check_ntp_time -H %s -w/g' /usr/local/nagios/etc/nrpe.cfg """ % ntp)
            if exe_result.succeed:
                print 'OK'
            else:
                print 'Error:' + exe_result.result
        else:
            print 'Please fill the ntpserver in overseas dbinfo site'

    def deploy(self, force=False):
        #"[==>>check monitor status]"
        self.check()
        # "[==>>create negios user]"
        self.create_user()
        # "[==>>update perl]"
        self.upgrade_perl()
        # "[==>>install tools]"
        tool_list = ['is_installed_Linux_pm',
                     'is_installed_nagios_plugin',
                     'is_openssl_devel',
                     'is_install_xinetd',
                     'is_installed_nrpe',
                     'is_installed_xinetd_nrpe',
                     'is_installed_utils_pm']
        for tool in tool_list:
            self.install_tools(tool, force)

        #"[==>>config iptables]"
        self.config_iptables()

        # "[==>>deploy monitor script]"
        self.deploy_script(force=force)
        #"[==>>update nrpe.cfg]"
        self.update_nrpe_cfg()
        # "[==>>change staliate ip]"
        self.change_satellite_ip()
        #"[==>>update ntp server in nrpe.cfg]"
        self.update_nrpe_ntp()
        # '[==>>config xinetd service]'
        self.config_xinetd()
        # '[==>>restart nrpe service]'
        self.restart_service()
        # '[==>>finished]'
        #   print "deploy nagios monitor completly,Next to restart service"


    def add_to_centreon(self, host_group, *template_names):
        cli = self.centreon['cli']
        satellite_name = None
        if self.server.s.ip_monitor and self.centreon['satelliate'].has_key(self.server.s.ip_monitor):
            satellite_name = self.centreon['satelliate'][self.server.s.ip_monitor]
        else:
            print "Error:Please check out ip_monitor information in web"
            return

        if host_group not in self.centreon['host_group']:
            print 'The host template is not correct:%s' % host_group
            return
        template_str = string.join([i for i in template_names if i in self.centreon['host_template']], '|')
        if len(template_str) <= 0:
            print "Error: template list"
            return

        centreon_server = self.server.get_node(self.centreon['server_id'])
        if centreon_server is None:
            print "getting centreon server is error"
            return

        #nrpes = self.config.items('nrpe')
        #file_name=self.config.get('tools', 'nrpe')
        hostname = string.join([self.server.s.region,
                                self.server.s.product,
                                "db-%s" % self.server.s.role if string.find(self.server.s.role,
                                                                            'db') == -1 else self.server.s.role,
                                self.server.s.ip_oper], '-')
        clicmd = '''%s  -o HOST -a ADD -v "%s"  ''' % (cli, "%s;%s;%s;%s;%s;%s" % (hostname,
                                                                                   hostname,
                                                                                   self.server.s.ip_oper,
                                                                                   template_str,
                                                                                   satellite_name,
                                                                                   host_group)
        )
        exe_result = centreon_server.execute(clicmd)
        if exe_result.succeed:
            print "create finished:%s" % hostname
            print "do apply template"
            clicmd = ''' %s  -o HOST -a applytpl -v "%s" ''' % (cli, hostname)
            exe_result = centreon_server.execute(clicmd)
            if exe_result.succeed:
                print "ok"
            else:
                print 'Error:' + exe_result.result

        else:
            print 'Error:' + exe_result.result

    def del_from_centreon(self):
        hostname = string.join([self.server.s.region,
                                self.server.s.product,
                                "db-%s" % self.server.s.role if string.find(self.server.s.role,
                                                                            'db') == -1 else self.server.s.role,
                                self.server.s.ip_oper], '-')
        cli = self.centreon['cli']
        centreon_server = self.server.get_node(self.centreon['server_id'])
        if centreon_server is None:
            print "getting centreon server is error"
            return
        clicmd = '''%s  -o HOST -a DEL -v "%s" ''' % (cli, hostname)
        exe_result = centreon_server.execute(clicmd)
        if exe_result.succeed:
            print "delete completly :%s" % hostname
        else:
            print 'Error:' + exe_result.result

    @classmethod
    def reload_centreon(cls):
        cli = cls.centreon['cli']
        centreon_server = Server.get_node(cls.centreon['server_id'])
        if centreon_server is None:
            print "getting centreon server is error"
            return
        clicmd = ''' %s -a POLLERLIST  | grep -v Return ''' % cli
        exe_result = centreon_server.execute(clicmd)
        if exe_result.succeed:
            satell_dict = dict([string.split(string.strip(i)) for i in string.split(exe_result.result, '\n')])
            statll_num = raw_input("Please give the number of your choice satelliate:")
            if satell_dict.has_key(statll_num):
                clicmd = []
                for act in ['POLLERGENERATE', 'POLLERTEST', 'CFGMOVE', 'POLLERRESTART ']:
                    clicmd.append(''' %s  -a %s -v "%s" ''' % (cli, act, statll_num))
                clicmd = string.join(clicmd, ' && ')
                centreon_server.execute(clicmd)

        else:
            print 'Error:' + exe_result.result


class SysInfo(Operation):
    __dbtable__ = 't_sysinfo'
    __checklist__ = None


    @classmethod
    def _get_dbinfo(cls, sys_type=None, dbid=None):
        if not cls._get_dbclass():
            return None
        result = None

        if sys_type is not None:
            if dbid is not None:
                result = cls.__dbsession__.query(cls.__dbclass__).filter(
                    cls.__dbclass__.sys_type == sys_type and cls.__dbclass__.id == dbid).first()
            else:
                result = cls.__dbsession__.query(cls.__dbclass__).filter(cls.__dbclass__.sys_type == sys_type).all()
        cls.__dbsession__.close()
        return result

    def __init__(self, server):
        super(SysInfo, self).__init__(server, "t_%s" % string.lower(self.__class__.__name__))
        
        if self.__checklist__ is None:
            self.__class__.__checklist__={i.id: i for i in self.__dbclass__.get(self.server.s.os_type,"sys_type")}
                                          
        self.check_result = {}

    def check_item(self, dbid=None, do_update=False):
        check_info = None
        check_return = None
        if self.__class__.__checklist__.has_key(dbid):
            check_info = self.__class__.__checklist__[dbid]
        else:
            return None
        if self.check_result.has_key(dbid):
            check_return = self.check_result[dbid]
            return None
        if not check_info.record_table and check_info.record_field and check_info.check_cmd:
            return None
        if check_info.need_id:
            need_result = self.check_item(check_info.need_id, do_update=False)
            if need_result not in string.split("%s" % check_info.need_value, ';'):
                return None
        execute_result = self.server.execute(check_info.check_cmd, hide_puts=True)
        if execute_result.succeed and execute_result.return_code == 0:
            # reg result
            check_return = string.strip(execute_result.result)
            self.check_result[dbid] = check_return
            if do_update and check_info.record_field and check_info.record_table:
                self.server.s.update_value(check_info.record_field, check_return)
        return check_return

    def check_all(self, do_update=False):
        for key, value in self.__class__.__checklist__.iteritems():
            print ("Check [%s]=%s" % (value.check_name, self.check_item(value.id, do_update))).encode('gbk')


class Transfer(object):
    def __init__(self, server=None, path=None, *dest_server):
        self._lpath = None
        self._lfile = None
        self.server = None
        self.source_path = None
        self.uuid = None
        # ServerID: [ Server, status, Result]
        self.trans_list = None
        self.dest_servers = []

        if server is not None:
            self.set_source_server(server)
        if path:
            self.set_source_path(path)
        if dest_server:
            self.add_dest_server(empty_old=True, *dest_server)

        self.tmppath = ''
        try:
            self.tmppath = os.environ["TMP"]
        except:
            pass
        if len(self.tmppath) == 0: self.tmppath = '/tmp'

    def set_source_server(self, src_server):
        self.server = src_server

    def set_source_path(self, path):
        if self.trans_list:
            self.clear()
            self.trans_list = None
        (self._lpath, self._lfile) = os.path.split(path)
        self.uuid = str(muuid.uuid1())
        self.source_path = path

    def add_dest_server(self, *srvlist):
        for srv in srvlist:
            if type(srv) == Server:
                if srv.s.role not in ['rds']:
                    self.dest_servers.append(srv)

    def empty_dest_server(self):
        if self.trans_list:
            self.clear()
        self.dest_servers = []

    @classmethod
    def get_from_lftp(cls, server, label, mid_path, dest_dir):
        store_path = '/home/dba/update'
        exe_result = server.execute("""lftp -c \'open %s;cd %s;mirror \"%s\"\' && \
                                        chmod -R 755 "%s" """ % (label,
                                                                 mid_path,
                                                                 dest_dir,
                                                                 os.path.join('/home/dba/update/', dest_dir)))
        if exe_result.succeed:
            store_path = os.path.join(store_path, dest_dir)
            print "Download finished:%s" % store_path
            return store_path
        else:
            print "Download failure"
            return None

    def send(self, dest_path, mode=None, owner=None):
        if len(self.dest_servers) == 0 or not self.source_path or self.server is None:
            return
        self.trans_list = {}
        dest_list = self.dest_servers if len(self.dest_servers) < 2 else sorted(self.dest_servers,
                                                                                key=lambda x: x.level, reverse=True)
        print "Sending: %s" % self.source_path
        #对目标服务器按level进行排序，先传输level数值大的，可以增加
        for value in dest_list:
            #记录uuid使用次数，初始是-1.正常结束时0，每传递加1，有问题为-2【记录机器为传输目标机器】
            #记录传输过程的执行结果，文本记录
            walkpath = self.server.walk(self.server, value)
            for (src_srv, dst_srv) in map(None, walkpath, walkpath[1:]):
                if src_srv is not None and not self.trans_list.has_key(src_srv.dbid):
                    self.trans_list[src_srv.dbid] = [src_srv, 0, None]
                if dst_srv is not None and not self.trans_list.has_key(dst_srv.dbid):
                    self.trans_list[dst_srv.dbid] = [dst_srv, 0, None]
                if dst_srv is None and self.trans_list.has_key(src_srv.dbid):
                    print "%s+-->%s" % (string.ljust(' ', src_srv.level * 4, ) + str(src_srv), str(dst_srv)),
                    if self.trans_list[src_srv.dbid][1] == 1:
                        if src_srv.exists(os.path.join(self.tmppath, self.uuid)):
                            if not src_srv.exists(dest_path):
                                src_srv.execute("mkdir -p %s" % dest_path, hide_stdout=True,
                                                hide_puts=True, hide_server_info=True)
                            exe_result = src_srv.execute("""mv %s %s %s %s""" % (
                                os.path.join(self.tmppath, self.uuid), os.path.join(dest_path, self._lfile)
                                , (" && chmod -R %s %s" % (mode, os.path.join(dest_path, self._lfile))) if mode else ''
                                ,
                                (" && chown -R %s %s" % (owner, os.path.join(dest_path, self._lfile))) if owner else ''
                            ), hide_stdout=True, hide_puts=True, hide_server_info=True)
                            if exe_result.succeed:
                                self.trans_list[src_srv.dbid][1] = 0
                                print 'move finished'
                            else:
                                print 'move failed:%s' % exe_result.result
                        else:
                            print 'No target:%s' % os.path.join(self.tmppath, self.uuid)
                    elif self.trans_list[src_srv.dbid][1] > 1:
                        if src_srv.exists(os.path.join(self.tmppath, self.uuid)):
                            if not src_srv.exists(dest_path):
                                src_srv.execute("mkdir -p %s" % dest_path, hide_stdout=True,
                                                hide_puts=True, hide_server_info=True)
                            exe_result = src_srv.execute("""cp -r  %s %s   %s   %s""" % (
                                os.path.join(self.tmppath, self.uuid), os.path.join(dest_path, self._lfile)
                                , (" && chmod -R %s %s" % (mode, os.path.join(dest_path, self._lfile))) if mode else ''
                                ,
                                (" && chown -R %s %s" % (owner, os.path.join(dest_path, self._lfile))) if owner else ''
                            ), hide_stdout=True, hide_puts=True, hide_server_info=True)
                            if exe_result.succeed:
                            #  self.trans_list[src_srv.dbid][1]=0
                                print 'copy finished'
                            else:
                                print 'copy failed:%s' % exe_result.result
                        else:
                            print 'No target:%s' % os.path.join(self.tmppath, self.uuid)
                    continue
                if src_srv.level > dst_srv.level and self.trans_list.has_key(src_srv.dbid) and self.trans_list.has_key(
                        dst_srv.dbid):
                    if self.trans_list[dst_srv.dbid][1] > 0 or dst_srv.exists(os.path.join(self.tmppath, self.uuid)):
                        self.trans_list[dst_srv.dbid][1] += 1
                    else:
                        print "%s+-->%s" % (string.ljust(' ', src_srv.level * 4, ) + str(src_srv), str(dst_srv)),
                        exe_result = dst_srv.execute(
                            "scp -r %s:%s %s" % ("%s@%s" % (src_srv.s.loginuser, src_srv.s.ip_oper)
                                                 , self.source_path if src_srv == self.server else os.path.join(
                                self.tmppath, self.uuid)
                                                 , os.path.join(self.tmppath,
                                                                self.uuid) if src_srv == self.server else os.path.join(
                                self.tmppath)
                            ), hide_stdout=True, hide_puts=True, hide_server_info=True)
                        if exe_result.succeed:
                            self.trans_list[dst_srv.dbid][1] += 1
                            self.trans_list[dst_srv.dbid][2] = 'OK'
                            print 'ok'
                        else:
                            self.trans_list[dst_srv.dbid][2] = 'Error:%s' % exe_result.result
                            print 'Error:%s' % exe_result.result
                            break
                elif src_srv.level < dst_srv.level and self.trans_list.has_key(
                        src_srv.dbid) and self.trans_list.has_key(dst_srv.dbid):
                    if self.trans_list[dst_srv.dbid][1] > 0 or dst_srv.exists(os.path.join(self.tmppath, self.uuid)):
                        self.trans_list[dst_srv.dbid][1] += 1
                    else:
                        print "%s+-->%s" % (string.ljust(' ', src_srv.level * 4, ) + str(src_srv), str(dst_srv)),
                        exe_result = src_srv.execute("scp -r %s %s:%s" % (
                            self.source_path if src_srv == self.server else os.path.join(self.tmppath, self.uuid)
                            , "%s@%s" % (dst_srv.s.loginuser, dst_srv.s.ip_oper)
                            ,
                            os.path.join(self.tmppath, self.uuid) if src_srv == self.server else os.path.join(
                                self.tmppath)
                        ), hide_stdout=True, hide_puts=True, hide_server_info=True)
                        if exe_result.succeed:
                            self.trans_list[dst_srv.dbid][1] += 1
                            self.trans_list[dst_srv.dbid][2] = 'OK'
                            print 'ok'
                        else:
                            self.trans_list[dst_srv.dbid][2] = 'Error:%s' % exe_result.result
                            print 'Error:%s' % exe_result.result
                            break


    def clear(self,quiet=True):
        if not self.trans_list:
            return
        if not quiet: print "Start to clear temp files"
        for key, value in self.trans_list.iteritems():
            if value[1] > 1:
                if not quiet: print "%5s%100s%5s  %40s" % (key, value[0], value[1], value[2]),
                exe_result = value[0].execute("cd %s; rm -rf %s" % ( self.tmppath, self.uuid), hide_stdout=True,
                                              hide_puts=True, hide_server_info=True)
                if exe_result.succeed:
                    value[1] = 0
                    if not quiet: print 'ok'
                else:
                    value[1] = -2
                    if not quiet: print 'fail'
            else:
                if not quiet: print "%5s%100s%5s  %s" % (key, value[0], value[1], value[2])


class SysInit(object):
    init_list = {'root_passwd': ["""chattr -i /etc/shadow && \
    sed -i -e 's/\(root:\).*\(:.*\)\(:0:.*\)$/\1\$1\$CXGBMKMu\$mhiWu0L6ae1IfV6XgreIR0:15679\3/g' /etc/shadow && \
    chattr +i /etc/shadow"""],
                 'grub_passwd': [""""""]
    }

    def __init__(self, server):
        self.server = server

    def make_authorized(self, password=None):
        auth_path = '''/%s/.ssh''' % (
            'root' if self.server.s.loginuser == 'root' else 'home/%s' % self.server.s.loginuser)
        pub_key = ''
        for way_server in self.server:
            if hasattr(way_server, "authorize_key"):
                pub_key += getattr(way_server, "authorize_key")
                pub_key += '\n'
            else:
                id_pub = ""
                way_auth_path = '''/%s/.ssh''' % (
                    'root' if way_server.s.loginuser == 'root' else 'home/%s' % way_server.s.loginuser)
                for key in ['dsa', 'rsa']:

                    if way_server.exists(os.path.join(way_auth_path, "id_%s.pub" % key)):
                        exe_result = way_server.execute("cat %s" % os.path.join(way_auth_path, "id_%s.pub" % key)
                            , hide_stdout=True, hide_puts=True, abort_on_prompts=False)
                        if exe_result.succeed:
                            id_pub += exe_result.result + '\n'
                id_pub = string.strip(id_pub)
                if way_server.level == 1 and len(id_pub) < 10:
                    print "Please create ssh key in %s, And redo this" % way_server
                    return
                if len(id_pub) > 10:
                    setattr(way_server, "authorize_key", id_pub)
                    pub_key += id_pub
                    pub_key += '\n'
        pub_key = string.strip(pub_key)

        if len(pub_key) > 10:
            auth_file = os.path.join(auth_path, "authorized_keys")
            authcmd = '''test -d %s || mkdir -p %s ;
            test -e %s || touch %s;
            cat %s >> %s.tmp;
            echo "%s" >> %s.tmp && \
            egrep -v '^$' %s.tmp | sort | uniq > %s.tmp1 && mv -f %s{.tmp1,.tmp} && \
            chmod 700 %s && \
            chattr -i %s && \
            mv -f %s.tmp %s && \
            chmod 600 %s  && \
            cat %s''' % (auth_path, auth_path,
                         auth_file, auth_file,
                         auth_file, auth_file,
                         pub_key, auth_file,
                         auth_file, auth_file, auth_file,
                         auth_path,
                         auth_file,
                         auth_file, auth_file,
                         auth_file,
                         auth_file)
            #    password = getpass.getpass('Enter password: ')

            exe_result = self.server.execute(authcmd, hide_warning=False, password=password if password else None,
                                             abort_on_prompts=True)
            if exe_result.succeed:
                pass
            else:
                print 'auth failure:%s' % exe_result.result
                #[[ -e ${current_dir}/config/keys.file ]] && cat ${current_dir}/config/keys.file | egrep -v '^#' >> /root/.ssh/authorized_keys
                #egrep -v '^$' /root/.ssh/authorized_keys | sort | uniq > /root/.ssh/authorized_keys.tmp && mv -f /root/.ssh/authorized_keys{.tmp,}
                #chmod 700 /root/.ssh
                #chmod 600 /root/.ssh/authorized_keys

    def disable_selinux(self):
        cmd = """setenforce 0;
        sed -i \'/^SELINUX=/s/^.*$/SELINUX=disabled/g\' /etc/sysconfig/selinux;
        (grep setenforce /etc/rc.local || echo \"setenforce 0\" >> /etc/rc.local
        """

        exe_result = self.server.execute(cmd)
        if exe_result.succeed:
            print 'selinux disable'

    def change_hostname(self):
        new_name = string.join([self.server.s.region,
                                self.server.s.product,
                                self.server.s.role,
                                string.join(string.split(self.server.s.ip_oper, '.')[-2:], '.')
                               ], '_')
        cmd = """hostname %s;
                 sed -i \'/^HOSTNAME=/s/^.*$/HOSTNAME=%s/g\' /etc/sysconfig/network
                 """ % (new_name, new_name)
        exe_result = self.server.execute(cmd)
        return exe_result

    def amazon_change_access_key(self, access_key, secret_key):
        access_key = string.replace(access_key, '/', '\/')
        secret_key = string.replace(secret_key, '/', '\/')
        cmd = """echo \"Before Change:\";
        cat /root/aws-scripts-mon/awscreds.conf;
        sed -i \'/^AWSAccessKeyId=/s/^.*$/AWSAccessKeyId=%s/g\' /root/aws-scripts-mon/awscreds.conf;
        sed -i \'/^AWSSecretKey=/s/^.*$/AWSSecretKey=%s/g\' /root/aws-scripts-mon/awscreds.conf;
        echo \"End Change:\";
        cat /root/aws-scripts-mon/awscreds.conf
        """ % (access_key, secret_key)
        exe_result = self.server.execute(cmd)
        if exe_result.succeed:
            print "change succeed"

            #mount  -o noatime -o nodiratime  -t xfs -L home /home
            #yum install xfsprogs kmod-xfs
            #virt-what

    def invalid_users(self):
        valid_users = {'oracle': 'oinstall',
                       'mysql': 'mysql',
                       'root': 'root',
                       'cyldj': 'cyldj',
                       'nagios': 'nagios',
                       'netdump': 'netdump',
                       'axis': 'axis',
                       'in_mobile': 'in_mobile'
        }

        self.server.execute(""" grep \'bin/bash\' \/etc\/passwd|egrep -v "^#|%s"|awk -F':' '{print $1,$6}' """
                            % (string.join(valid_users.keys(), '|')))


class MySQL(object):
    def __init__(self, server=None):
        self.server = None
        if server:
            self.server = server
        self.instances = []

    def get_info(self):
        shell = """
            echo -n "instances:"
            INC=`perl -e 'print \"@INC\"'`;
            find ${INC} -name 'Linux.pm' -print 2> /dev/null \
            | grep -q 'Linux.pm' && echo True || echo False;
        """

    def get_instance_list(self):
        exe_result = self.server.execute(
            """ ls -1Fd \/home\/mysql* 2>\/dev\/null | egrep '/$' | egrep "mysql_[0-9]{4}/|mysql\/" """)
        if exe_result.succeed:
            for ins in string.split(string.replace(exe_result.result, '\r', ''), '\n'):
                self.instances.append(os.path.join(ins, 'mysql.sock'))
            return True
        else:
            print 'Error:%s' % exe_result.result
            return False

    def merage(self, db_name, sport, dest_server, dport, bk_nodata=False):
        print 'starting to merget from %s to %s' % (self.server, dest_server)
        backup_file = self.backup(db_name=db_name, port=sport, no_data=bk_nodata)
        if backup_file:
            (lpath, lfile) = os.path.split(backup_file)
            trans_path = '/home/databackup'
            trans = Transfer(self.server, backup_file)
            trans.add_dest_server(dest_server)
            trans.send(trans_path)
            trans.clear()
            target_path = os.path.join(trans_path, lfile)
            if dest_server.exists(target_path):
                dest_mysql = MySQL(dest_server)
                if dest_mysql.recover((db_name if string.find(db_name, ',') == -1 else None) if db_name else None,
                                      port=dport, backupfile=target_path):
                    print 'Merage finished :OK'
            else:
                print 'No files in %s :%s' % (dest_server, target_path)
                print 'Merage is broken'


    def backup(self, db_name=None, port=3306, char_set='utf8', no_data=False):
        if len(self.instances) == 0:
            if not self.get_instance_list():
                return None
        link_str = None
        for ins in self.instances:
            if string.find(ins, str(port)) != -1:
                link_str = ins
                break
        if link_str:
            changetime = time.strftime('%Y%m%d_%H%M%S', time.localtime(time.time()))
            #地区_产品_IP段_引擎_端口_方法-库_名-时间-full|inc.tar.gz
            backup_file = "%s_%s_%s_%s_%s-%s-%s_%s_%s.sql.gz" % (self.server.s.region,
                                                                 self.server.s.product,
                                                                 self.server.s.ip_oper,
                                                                 'mysql',
                                                                 str(port),
                                                                 'dump',
                                                                 string.replace(db_name, ',',
                                                                                '.') if db_name else 'ALL',
                                                                 changetime,
                                                                 'full')
            store_path = '/home/databackup/'
            backup_path = os.path.join(store_path, backup_file)
            dump_param = " --default-character-set=%s  --single-transaction  -R --triggers -q " % char_set
            if no_data and db_name: dump_param += ' --no-data '
            dump_param += ((" -B %s ") % db_name) if db_name else ' -A '
            backup_cmd = """mkdir -p %s ;mysqldump -S %s %s | gzip > %s""" % (store_path,
                                                                              link_str,
                                                                              dump_param,
                                                                              backup_path)
            print 'starting to backup database in %s' % self.server
            exe_result = self.server.execute(backup_cmd)
            if exe_result.succeed and string.find(exe_result.result, 'error') == -1:
                print 'Backup finished: %s' % backup_path
                return backup_path
            else:
                print 'Backup failure:%s' % exe_result.result
                return None

    def recover(self, dbname, port, backupfile, char_set='utf8'):
        if len(self.instances) == 0:
            if not self.get_instance_list():
                return False
        link_str = None
        for ins in self.instances:
            if string.find(ins, str(port)) != -1:
                link_str = ins
                break
                #(fpath,fname)=os.path.split(backupfile)

                #uncompress={'.tar.gz':['tar zxvf %s -C %s' % (backupfile,fpath)],
                #'.gz':
                #for unc in ['.tar.gz','.gz','.zip']
                #if fext=='.gz':
                #uncompress='gzip -d %s' % backupfile
        recover_cmd = """cat %s | gunzip | mysql -S %s --default-character-set=%s  """ % (backupfile,
                                                                                          link_str,
                                                                                          char_set)
        #           dbname if dbname else '')
        exe_result = self.server.execute(recover_cmd)
        if exe_result.succeed:
            print 'Recover database of [%s] on %s finished' % (dbname, self.server)
            return True
        else:
            print 'Recover database of [%s] on %s failure' % (dbname, self.server)
            return False


    """
    mysqldump -S /home/mysql_3306/mysql.sock  --default-character-set=utf8 --single-transaction -R --triggers -q -B $DOD_CONFIG > $DOD_CONFIG_bak_`date +%Y%m%d%H%M`.sql
    """

    def update(self, dbname, port, sqlfile, char_set='utf8'):
        pass


class Axis(object):
    def __init__(self, server):
        self.server = server
        self.runuser = 'axis'

    def install(self, satellite_ip):
        sudo_cmd = '/usr/bin/ipmitool lan print,/usr/bin/ipmitool fru list'
        cmd = '''chattr -i /etc/shadow;
        useradd axis;
        chattr +i /etc/shadow;
        chmod u+s /usr/sbin/dmidecode;
        (grep axis /etc/sudoers &> /dev/null \
        || sed -i '/axis/s/$/,%s/g' /etc/sudoers) \
        || echo \"axis ALL=NOPASSWD: %s\" \
        >> /etc/sudoers ;
        grep gs_axis_idc_server /etc/hosts &> /dev/null \
        || echo \"%s    gs_axis_idc_server\">> /etc/hosts
        ''' % (sudo_cmd, sudo_cmd, satellite_ip)
        exe_result = self.server.execute(cmd, hide_stdout=True)
        if exe_result.succeed:
            print 'init env finished'
            tran = Transfer(self.server.root, '/tmp/zo9Z/AxisAgent')
            tran.add_dest_server(self.server)
            tran.send('/home/axis/', owner='axis:axis')
            tran.clear()

    def start(self):
        cmd = """chown -R axis:axis /home/axis/AxisAgent;
        chmod 750 /home/axis/AxisAgent/AxisAgent;
        su - axis -c 'cd /home/axis/AxisAgent/;./AxisAgent  &>/dev/null &' ;
        ps -ef | grep AxisAgent | grep -v grep """
        exe_result = self.server.execute(cmd, hide_stdout=True)
        if exe_result.succeed:
            print 'start finished'
        else:
            print exe_result.result

    def stop(self):
        cmd = """ps -ef | grep AxisAgent | grep -v grep  | awk \'{print $2}\' | xargs kill -9 """
        exe_result = self.server.execute(cmd, hide_stdout=True)
        if exe_result.succeed:
            print 'stop finished'

    def uninstall(self):
        self.stop()
        cmd = """chattr -i /etc/shadow;
        userdel -r axis;
        chattr +i /etc/shadow;"""
        exe_result = self.server.execute(cmd, hide_stdout=True)
        if exe_result.succeed:
            print 'uninstall finished'

    def check(self):
        cmd = """ps -ef | grep AxisAgent | grep -v grep """
        exe_result = self.server.execute(cmd)






        #grep -q nagios /etc/sudoers && \
        #(grep %s /etc/sudoers &> /dev/null \
        #|| sed -i '/nagios/s/$/,%s/g' /etc/sudoers) \
        #|| echo \"nagios ALL=NOPASSWD: %s\" \
        #>> /etc/sudoers        


class Piece(object):
    def __init__(self):
        pass


class Crontab(Operation):
    __dbtable__ = 't_crontab'
    groups = ['backup', 'hardware_monitor', 'game_count', 'finance_query', 'ntp''clean_data', 'other', 'temp']



    def __init__(self, server):
        super(Crontab, self).__init__(server)
        


    def available(self):
        if self.server.s.role == 'rds' or self.server.s.os_type == 'Windows':
            return False
        else:
            return True

    def collect(self):
        print "%50s" % self.server,
        exe_result = self.server.execute(
            """crontab -u %s -l 2>/dev/null | grep -v \# | grep -v \= | sed /^$/d""" % self.server.s.loginuser,
            hide_puts=True, showprefix=True)
        if exe_result.succeed:
            count = 0
            for line in string.split(exe_result.result, '\n'):
                line = string.strip(line)
                if len(line):
                    pmin, phour, pday, pmon, pweek = line.split()[0:5]
                    process = ' '.join(line.split()[5:]).replace("\'", "\"")
                    status = 1
                    user = self.server.s.loginuser
                    try:
                        self.get_dbclass().add(server_id=self.server.dbid,
                                              pminute=pmin,
                                              phour=phour,
                                              pday=pday,
                                              pmonth=pmon,
                                              pweek=pweek,
                                              process=process,
                                              status=status,
                                              user=self.server.s.loginuser,
                                              description='')
                    except:
                        continue


                    count += 1
            print '  %50s' % ('Collected the number of crontab:%s' % count)

    def list(self):     
        res_table=prettytable.PrettyTable(["id", "min", 'hou', 'day', 'mon', 'wee', 'process', 'user', 'status', 'description'])
        for col_name in ['hou','day','mon','process','description']:
            res_table.align[col_name]='l'
        res_table.padding_width = 1
        res_table.encoding = self.server.encoding  
        for i in self.get_dbclass().get(self.server.dbid,"server_id"):
            res_table.add_row([i.id, i.pminute, i.phour, i.pday, i.pmonth, i.pweek, i.process, i.user, i.status, i.description])
        print res_table

    def _sed_reg(self, db_row):
        sed_reg = ""
        try:
            sed_reg += ".*"
            sed_reg += string.replace(db_row.pminute, '*', '\*').replace('/', '\/') + '.*'
            sed_reg += string.replace(db_row.phour, '*', '\*').replace('/', '\/') + '.*'
            sed_reg += string.replace(db_row.pday, '*', '\*').replace('/', '\/') + '.*'
            sed_reg += string.replace(db_row.pmonth, '*', '\*').replace('/', '\/') + '.*'
            sed_reg += string.replace(db_row.pweek, '*', '\*').replace('/', '\/') + '.*'
            sed_reg += string.replace(db_row.process, '*', '\*').replace('/', '\/') + '.*'
        except:
            pass
        return sed_reg

    def delete(self, *dbid):
        import time

        '''cat /var/spool/cron/root'''
        for instance in self.get_dbclass().get(dbid):
            changetime = time.strftime('%Y%m%d_%H%M%S', time.localtime(time.time()))
            sed_reg = self._sed_reg(instance)

            cmd = """cp /var/spool/cron/%s /var/spool/cron/%s.%s && \
                sed -i '/%s/d' /var/spool/cron/%s""" % (self.server.s.loginuser, self.server.s.loginuser, changetime,
                                                        sed_reg, self.server.s.loginuser)
            exe_result = self.server.execute(cmd)
            if exe_result.succeed:
                print 'delete succeed of ID:%s' % instance.id
                self.__dbclass__.delete(instance.id)
            else:
                print 'delte failure of ID:%s and Error:%s' % (instance.id, exe_result.result)


    def disable(self, *dbid):
        for instance in self.get_dbclass().get(dbid):
            changetime = time.strftime('%Y%m%d_%H%M%S', time.localtime(time.time()))
            sed_reg = self._sed_reg(instance)

            cmd = """cp /var/spool/cron/%s /var/spool/cron/%s.%s && \
                sed -i '/%s/s/^/#/' /var/spool/cron/%s""" % (
                self.server.s.loginuser, self.server.s.loginuser, changetime,
                sed_reg, self.server.s.loginuser)
            exe_result = self.server.execute(cmd)
            if exe_result.succeed:
                print 'disable succeed of ID:%s' % instance.id
                self.__dbclass__.set_attrs(instance.id,status=0)
            else:
                print 'disable failure of ID:%s and Error:%s' % (instance.id, exe_result.result)


    def enable(self, *dbid):
        for instance in self.get_dbclass().get(dbid):
            changetime = time.strftime('%Y%m%d_%H%M%S', time.localtime(time.time()))
            sed_reg = self._sed_reg(instance)

            cmd = """cp /var/spool/cron/%s /var/spool/cron/%s.%s && \
                sed -i '/%s/s/^#*//' /var/spool/cron/%s""" % (
                self.server.s.loginuser, self.server.s.loginuser, changetime,
                sed_reg, self.server.s.loginuser)
            exe_result = self.server.execute(cmd)
            if exe_result.succeed:
                print 'enable succeed of ID:%s' % instance.id
                self.get_dbclass().set_attrs(instance.id,status=0)
            else:
                print 'enable failure of ID:%s and Error:%s' % (instance.id, exe_result.result)


    def create(self, process, minute, hour, day, month, week, status, description, group):
        dbsession = self.__class__.__dbsession__
        dbclass = self.__class__.__dbclass__
        minute = minute if minute else '*'
        hour = hour if hour else '*'
        day = day if day else '*'
        month = month if month else '*'

    def change_description(self, description, dbid):
        for instance in self.__dbclass__.get( dbid):
            print 'description for ID:%s to %s' % (instance.id, description)
            self.get_dbclass().set_attrs(dbid,description=description)


    def show(self):
        exe_result = self.server.execute("""crontab -l""")

    def change_group(self, group_name, *dbid):
        for instance in self.__dbclass__.get( dbid):
            print 'change_group for ID:%s to %s' % (instance.id, group_name)
            self.get_dbclass().set_attrs(dbid,group=group_name)
            instance.group = group_name



# "wget --no-check-certificate -O - http://bootstrap.saltstack.org | sh"  
#"sed -i '/^\#master: /s/^.*$/master: syndic.vn.salt.cyoper/g' /etc/salt/minion && echo '10.6.6.42  syndic.vn.salt.cyoper'>> /etc/hosts"  
# "/etc/init.d/salt-minion restart"

#后来发现scp这东西应该属于openssh-clients这个包，运行：
#yum install openssh-clients
