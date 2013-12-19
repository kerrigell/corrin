#!/usr/bin/env python
#coding:utf-8
# Author:  Jianpo Ma
# Purpose:
# Created: 2013/3/29

import os, sys
import string
import time
import datetime
import os.path
import shlex
from optparse import OptionParser



import traceback
import pdb

import ConfigParser

import cmd2 as cmd
from cmd2 import options, make_option
import prettytable

import colors
from node import Server
from node import Feature
from node import Nagios
from node import IPsec
from node import SysInfo
from node import Transfer
from node import Iptables


class PizzaShell(cmd.Cmd):
    def __init__(self):
        cmd.Cmd.__init__(self)
        self.centerid=None
        self.encoding=None
        try:
            config =ConfigParser.SafeConfigParser()
            base_path = os.path.split(os.path.realpath(sys.argv[0]))[0]
            config.read(os.path.join(base_path, "config/pizza.ini"))
            self.centerid=config.get('pizza','centerid')
            self.encoding=config.get('pizza','encoding')
        except Exception,e:
            pass
            
        #using
        Server.encoding=self.encoding
        self.server = Server(self.centerid if self.centerid else None)
        self.server.breed()
        #   self.feature=Feature(foreignclass=Server)
        #  self.feature.breed(True)
        self.piecis = {}
        self.mode = Server	
        self.__set_prompt(self.mode.current_node)
        
        


    def do_cd(self, line):
        line = string.strip(line)
        dbid = line
        if string.find(line, '[') != -1:
            (dbid, info) = string.split(line, '[')
            (dbid, info) = string.split(info, ':')[0:2]
        cnode = self.mode.cd(dbid)
        self.__set_prompt(cnode)


    def complete_cd(self, text, line, begidx, endidx):
        import readline
        readline.set_completer_delims(' \t\n`~!@#$%^&*()-=+[{]}\\|;\'",<>;?')
        tlist = [str(i) for i in self.mode.current_node.childs.values() if string.find(str(i), line[3:]) == 0]
        return tlist

    def do_login(self, line):
        if self.mode == Server:
            self.mode.current_node.login()

    def do_mode(self, line):
        line = string.strip(line)
        if line == 'product':
            self.mode = Feature
        elif line == 'server':
            self.mode = Server
        self.__set_prompt(self.mode.current_node)


    def complete_mode(self, text, line, begidx, endidx):
        modelist = ['product', 'server']
        return [f for f in modelist if f.startswith(text)]
        #def do_put(self,line):
        #'''put a file to target server from ccs'''
        #(lfile, taddr, rpath)=string.split(line)
        #if not (os.path.isfile(lfile) and os.path.exists(lfile)):
        #print 'Error: not exists or not a file %s' % lfile
        #return
        #tsrv=self.root.search(taddr)
        #if tsrv == None:
        #print 'Error: not find %s' % taddr
        #return
        #print 'Send a file from %s to %s' % (self.root, tsrv)
        #self.root.putfile(lfile,tsrv,rpath)
        #print 'Send finished'

        #def help_put(self):
        #print '\n'.join(['put <localfile> <targetserver> <remotepath>','put a file to target server from ccs'])

        #def complete_put(self,text,line,begidx,endidx):
        #import readline
        #pos=len(string.split(line))
        #if pos == 2 or pos == 4:
        ## import rlcompleter
        ## readline.parse_and_bind("tab: complete")
        #readline.set_completer_delims(' \t\n`~!@#$%^&*()-=+[{]}\\|;:\'",<>;?')
        #import glob
        #return glob.glob('%s*' % text)
        #if pos == 3:
        #'''search server list like aaa.*'''
        #readline.set_completer_delims(' \t\n`~!@#$%^&*()-=+[{]}\\|;:\'",<>;?')
        #return self.root.search_list(text)


    def do_cmd(self, line):
        if not len(line) > 0:
            return
        shl=shlex.shlex(line,posix=True)
        shl.whitespace_split=True
        optparse=OptionParser()
        optparse.add_option('-p', '--piece', type='string', help='piece name')
        optparse.add_option('--recursion', action='store_true', help='get childs  with recursion')
        optparse.add_option('-c', '--childs', action='store_true', help='get childs ')
        (opts,args)=optparse.parse_args([ i for i in shl])
        
        
        oper_list = self._get_operation_list(self.server.current_node,
                                             inPiece=opts.piece if opts.piece else None,
                                             inCurrent=True,
                                             inChilds=True if opts.childs else False,
                                             useRecursion=True if opts.recursion else False,
                                             objClass=None)
        self.__process_list(oper_list,"execute",string.join(args,';'),hide_server_info=True,hide_puts=True)
        
        #print 'Server Count:%s' % len(oper_list)
        #for oper in oper_list:
            #print "%s" % oper
            #oper.execute(string.join(args,';'),hide_server_info=True)



            #@options([make_option('-p','--piece',type='string',help='piece name'),
            #make_option('--desc_path',type='string',help='piece name')])
            #def do_get(self,arg,opts=None):
            #for path in string.split(arg):
            #if not os.path.exists(path):
            #print self.colorize('Error: Path not exist','red')
            #continue
            #else:
            #for s in self._get_operation_list(opts):
            #s.download(path,targetpath=opts.desc_path if opts.desc_path else None)
            #def complete_get(self,text,line,begidx,endidx):
            #import readline
            #readline.set_completer_delims(' \t\n`~!@#$%^&*()-=+[{]}\\|;:\'",<>;?')
            #import glob
            #return glob.glob('%s*' % text)


    @options([make_option('-c', '--create', action='store_true', help='create piece'),
              make_option('-p', '--ploy', type='string', help='the ploy for choice servers'),
              make_option('-l', '--list', action='store_true', help='list piece'),
              make_option('-d', '--delete', action='store_true', help='delete piece'),
              make_option('-n', '--name', type='string', help='piece name')])
    def do_piece(self, arg, opts=None):
        arg = ''.join(arg)
        if opts.create and opts.name and opts.ploy:
            piece = {'ploy': opts.ploy,
                     'createtime': time.ctime(),
                     'servers': []}
            if self.mode == Server:
                slist = self.mode.piece(opts.ploy)
                piece['servers'] = slist
                self.piecis[opts.name] = piece
                if slist:
                    for i in slist:
                        print i
        elif opts.list:
            for i in self.piecis.keys():
                print i
                if opts.name:
                    print ' '.ljust(4, ' '), 'CreateTime:', self.piecis[i]['createtime']
                    for j in self.piecis[i]['servers']:
                        print ' '.ljust(4, ' '), j
        elif opts.run:
            pass
    def __set_prompt(self,node):
        self.prompt= """%s%s%s%s>""" % (colors.blue("Pizza",prompt=True),
                                 '[',
                                 colors.magenta(str(node),prompt=True),
                                 ']')
             
    def __process_list(self,inst_list,fun,*args,**kwargs):
        results=[]
        cross_print=False
        error_count=0
        elapsed_sum=0
        proc_fun=fun
        try:
            for num,instance in enumerate(inst_list):
                proc_item=instance
                proc_res=None
                if hasattr(proc_item,proc_fun):
                    proc_res=getattr(proc_item,proc_fun)(*args,**kwargs)
                if proc_res and (not cross_print) and string.find(proc_res.result,'\n') != -1:
                    cross_print = True
                if proc_res is None or proc_res.succeed == False:
                    error_count += 1
                if proc_res is not None:
                    elapsed_sum += proc_res.elapsed
                results.append([num+1,instance,proc_res])
            self.__print_result(results,len(inst_list),error_count,elapsed_sum,cross_print)
        except Exception,e:
            print "Error:%s" % e
        finally:
            Server.disconnect_all()
    def __print_result(self,results,inst_count,error_count,elapsed_sum,cross_print=False):
        def __print_table(results,encoding="gbk"):
            res_table=prettytable.PrettyTable(["Num","Instance","Elapsed","Result"])
            res_table.align["Result"]="l"
            res_table.align["Instance"]="l"
            res_table.align["Elapsed"]="l"
            res_table.padding_width=1
            res_table.encoding=encoding
            for (num,instance,result) in results:
                if result.succeed:
                    color="cyan"
                else:
                    color="red"
                res_table.add_row([num,
                                   instance  if result.succeed else colors.red(str(instance)),
                                   datetime.timedelta(seconds=result.elapsed),
                                   result.result if result.succeed else colors.red(str(result.result))
                                   ])
            print res_table
        def __print_cross(results,encoding="gbk"):
            for (num,instance,result) in results:
                print "Num:%5s [%40s] Elapsed:%20s" % (num,
                                         instance  if result.succeed else colors.red(str(instance)),
                                         datetime.timedelta(seconds=result.elapsed))
                print colors.green(str(result.result)) if result.succeed else colors.red(str(result.result))
            
                    
                    
        print "Count/Error: %s/%s     Elapsed: %s" % (colors.yellow(str(inst_count)),
                                                      colors.red(str(error_count)),
                                                      datetime.timedelta(seconds=elapsed_sum))  
        if cross_print:
            __print_cross(results,self.encoding)
        else:
            __print_table(results,self.encoding)

        

        
            
    def _get_operation_list(self, node,
            inPiece=None,
            inCurrent=False,
            inChilds=False,
            useRecursion=False,
            objClass=None):
        server_list = []
        if inPiece and self.piecis.has_key(inPiece):
            for s in self.piecis[inPiece]['servers']:
                server_list.append(s)
        if inChilds:
            server_list += node.get_childs(useRecursion)
        if inCurrent:
            server_list.append(node)
        object_list = []
        if objClass:
            object_list = [objClass(i) for i in server_list]
        return object_list if objClass else server_list



        #if opts is not None and hasattr(opts,'piece') and self.piecis.has_key(opts.piece):
        #for value in self.piecis[opts.piece]['servers']:
        #serverlist.append(value)
        #else:
        #serverlist.append(self.server.current_node)
        #return serverlist

        #def _get_childs_list(self,recursion=False):
        #serverlist=[]
        #if self.server.current_node.childs is None:
        #self.server.current_node.breed()
        #for i in self.server.current_node.childs.values():
        #serverlist.append(i)
        #return serverlist


    @options([make_option('-p', '--piece', type='string', help='piece name'),
              make_option('--recursion', action='store_true', help='get childs  with recursion'),
              make_option('-c', '--childs', action='store_true', help='get childs '),
              make_option('--check', action='store_true', help='check'),
              make_option('-d', '--deploy', action='store_true', help='deploy everything automatically'),
              make_option('-s', '--step', action='store_true', help='deploy monitor step by step'),
              make_option('--force', action='store_true', help='install tools force'),
              make_option('--restart_nrpe', action='store_true', help='restart service'),
              make_option('--show_nrpe', action='store_true', help='deploy monitor step by step'),
              make_option('--add_to_centreon', action='store_true', help='deploy monitor step by step'),
              make_option('--del_from_centreon', action='store_true', help='deploy monitor step by step'),
              make_option('--reload_centreon', action='store_true', help='deploy monitor step by step')
              ])
    def do_nagios(self, args, opts=None):
        Nagios.get_config()
        Nagios.get_centreon_info()        
        if opts.reload_centreon:
            Nagios.reload_centreon()
            return
        monitor_list = self._get_operation_list(self.server.current_node,
                                                inPiece=opts.piece if opts.piece else None,
                                                inCurrent=True,
                                                inChilds=True if opts.childs else False,
                                                useRecursion=True if opts.recursion else False,
                                                objClass=Nagios)


        oper = None
        oper_param = None

        if opts.step:
            sauce = self.select([x[0] for x in Nagios.operation_step], 'Please choice what you want?')
            dopers = dict(Nagios.operation_step)
            if dopers.has_key(sauce):
                oper = dopers[sauce]
                if oper == 'update_nrpe':
                    nrpt_item = raw_input('Please give the name of nrpe:')
                    if nrpt_item:
                        oper_param=[ nrpt_item]
                if oper == 'deploy_script' or oper == 'upgrade_perl' or oper == 'install_tools':
                    force_install = raw_input('Force install tools?(yes|no)')
                    if force_install == 'yes':
                        oper_param=[True]
        elif opts.check:
            oper = 'check'
        elif opts.deploy:
            oper = 'deploy'
            if opts.force:
                oper_param=[True] 
        elif opts.show_nrpe:
            oper = 'show_nrpe'
        elif opts.restart_nrpe:
            oper = 'restart_service'
        elif opts.add_to_centreon:
            oper = 'add_to_centreon'
            tpl_dict=dict(enumerate(Nagios.centreon['host_template']))
            print "Host Template List:"
            for key,value in tpl_dict.iteritems():
                print "%s %2s. %s" % (string.ljust('',4),key,value)
            tplin=raw_input("Please get numbers of template:")
            tpl_list=[]
            for num in string.split(tplin,','):
                if tpl_dict.has_key(int(num)):
                    tpl_list.append(tpl_dict[int(num)])
            host_group=self.select(Nagios.centreon['host_group'])
            oper_param=[host_group] + tpl_list

        elif opts.del_from_centreon:
            oper= 'del_from_centreon'
        for item in monitor_list:
            if oper:
                operfun = getattr(item, oper)
                if oper_param and len(oper_param)>0:
                    operfun(*oper_param)
                else:
                    operfun()
            

    @options([make_option('-a', '--add', action='store_true', help='add ipsec filter'),
              make_option('--chain', type='choice', choices=['INPUT', 'OUTPUT', 'FORWARD'], help='protocal'),
              make_option('--source', type='string', help='source address'),
              make_option('--protocal', type='choice', choices=['tcp', 'udp', 'imcp', 'all'], help='protocal'),
              make_option('--dport', type='string', help='dport'),
              #    make_option('--description',type='string',help='filter description'),
              make_option('-d', '--delete', action='store_true', help='delete ipsec filter'),
              make_option('-l', '--list', action='store_true', help='list ipsec'),
              make_option('--script', action='store_true', help='show  ipsec script'),
              make_option('--status', action='store_true', help='show  current ipsec status'),
              make_option('--reload', action='store_true', help='reload ipsec')
    ])
    def do_ipsec(self, args, opts=None):
        cipsec = IPsec(self.server.current_node)
        if opts.add:
            if opts.protocal and opts.source and opts.dport:
                cipsec.add_filter(opts.protocal, opts.source, opts.dport, args,
                                  chain=opts.chain if opts.chain else 'INPUT')
            else:
                print '''Need surport correct value for those:
        [--chain=]
        --source=
        --protocal=
        --dport=
        --description='''
            return
        if opts.list:
            ripsec = cipsec.list()
            print "%5s%8s%20s%20s  %s" % ("dbid", "Chain", 'Source', 'dport', 'description')
            for i in ripsec:
                print "%5s%8s%20s%20s  %s" % (i.id, i.chain, i.source_addr, i.dport, i.description)
            return
        if opts.script:
            print cipsec.make_script()
            return
        if opts.reload:
            print 'start reload ipsec',
            cipsec.reload()
            print 'ok'
            return
        if opts.delete:
            ripsec = cipsec.list()
            print "      %5s%8s%20s%20s  %s" % ("dbid", "Chain", 'Source', 'dport', 'description')
            infolist = []
            for i in ripsec:
                infolist.append("%5s%8s%20s%20s  %s" % (i.id, i.chain, i.source_addr, i.dport, i.description))
            sauce = self.select(infolist)
            print "delete filter",
            cipsec.del_filter(int(string.split(sauce)[0]))
            print "ok"
            return
        if opts.status:
            self.server.current_node.execute("iptables -nvL")
            return

    @options([
        make_option('-p', '--piece', type='string', help='piece name'),
        make_option('--recursion', action='store_true', help='get childs  with recursion'),
        make_option('-c', '--childs', action='store_true', help='get childs '),
        make_option('-s', '--save', action='store_true', help='Store iptables rules from onlie server to database')
    ])
    def do_iptables(self, args, opts=None):
        iptables_list = self._get_operation_list(
            self.server.current_node,
            inPiece=opts.piece if opts.piece else None,
            inCurrent=True,
            inChilds=True if opts.childs else False,
            useRecursion=True if opts.recursion else False,
            objClass=Iptables
        )
        if opts.save:
            for iptables in iptables_list:
                iptables.save_from_server()
            return


    @options([make_option('-p', '--piece', type='string', help='piece name'),
              make_option('--recursion', action='store_true', help='get childs  with recursion'),
              make_option('-c', '--childs', action='store_true', help='get childs '),
              make_option('--check_all', action='store_true', help='check all'),
              make_option('--update', action='store_true', help='update database')])
    def do_info(self, arg, opts=None):
        info_list = self._get_operation_list(self.server.current_node,
                                             inPiece=opts.piece if opts.piece else None,
                                             inCurrent=True,
                                             inChilds=True if opts.childs else False,
                                             useRecursion=True if opts.recursion else False,
                                             objClass=SysInfo)
        for item in info_list:
            print item.server
            if opts.check_all:
                item.check_all(do_update=True if opts.update else False)

    @options([make_option('-p', '--piece', type='string', help='piece name'),
              make_option('--recursion', action='store_true', help='get childs  with recursion'),
              make_option('-c', '--childs', action='store_true', help='get childs '),

              make_option('-t', '--target', type='string', help='trans target'),
              make_option('-d', '--deploy_dir', type='string', help='trans target'),
              make_option('-w', '--who', type='string', help='trans target'),
              make_option('--get_version', type='string', help='trans target')])
    def do_trans(self, arg, opts=None):

        server_list = self._get_operation_list(self.server.current_node,
                                               inPiece=opts.piece if opts.piece else None,
                                               inCurrent=False,
                                               inChilds=True if opts.childs else False,
                                               useRecursion=True if opts.recursion else False,
                                               objClass=None)

        trans_task = Transfer()
        if opts.get_version:


            src_path = Transfer.get_from_lftp(self.server.current_node.root,
                                              'get-version',
                                              'db_version/ALL/',
                                              opts.get_version)
            if src_path:
                trans_task.set_source_server(self.server.current_node.root)
                trans_task.set_source_path(src_path)
            else:
                return
        else:
            trans_task.set_source_server(self.server.current_node)
            trans_task.set_source_path(opts.target)
            #self.server.current_node,opts.target)
        if opts.who:
            line = string.strip(opts.who)
            dbid = line
            if string.find(line, '[') != -1:
                (dbid, info) = string.split(line, '[')
                (dbid, info) = string.split(info, ':')
                server_list.append(self.server.current_node.get_node(int(dbid)))
        if len(server_list) > 0:
            trans_task.add_dest_server(*server_list)
            print "Servers Count:%s" % len(trans_task.dest_servers)
            trans_task.send(opts.deploy_dir if opts.deploy_dir else '/tmp')
            trans_task.clear()

    @options([make_option('-p', '--piece', type='string', help='piece name'),
              make_option('--recursion', action='store_true', help='get childs  with recursion'),
              make_option('-c', '--childs', action='store_true', help='get childs '),

              make_option('-a', '--make_authorized', action='store_true', help='piece name'),
              make_option('--disable_selinux', action='store_true', help='piece name'),
              make_option('--amazon_change_access_key', action='store_true', help='piece name'),
              make_option('--access_key', type='string', help='piece name'),
              make_option('--secret_key', type='string', help='piece name'),
              make_option('--invalid_users', action='store_true', help='piece name'),
    ])
    def do_sysinit(self, arg, opts=None):
        from node import SysInit
        import getpass

        init_list = self._get_operation_list(self.server.current_node,
                                             inPiece=opts.piece if opts.piece else None,
                                             inCurrent=True,
                                             inChilds=True if opts.childs else False,
                                             useRecursion=True if opts.recursion else False,
                                             objClass=SysInit)
        password = None
        for item in init_list:
            if opts.make_authorized:
                if password is None:
                    password = getpass.getpass('Enter Login password: ')
                item.make_authorized(password=password if len(password) > 0 else None)
            if opts.disable_selinux:
                item.disable_selinux()
            if opts.amazon_change_access_key and opts.access_key and opts.secret_key:
                item.amazon_change_access_key(opts.access_key, opts.secret_key)
            if opts.invalid_users:
                item.invalid_users()

    @options([make_option('-p', '--piece', type='string', help='piece name'),
              make_option('--recursion', action='store_true', help='get childs  with recursion'),
              make_option('-c', '--childs', action='store_true', help='get childs '),

              make_option('-i', '--install', action='store_true', help='piece name'),
              make_option('-k', '--check', action='store_true', help='piece name'),
              make_option('-s', '--start', action='store_true', help='piece name'),
              make_option('-t', '--stop', action='store_true', help='piece name'),
              make_option('-u', '--uninstall', action='store_true', help='piece name'),
              make_option('-a', '--address', type='string', help='piece name'), ])
    def do_axis(self, arg, opts=None):
        from node import Axis

        axis_list = self._get_operation_list(self.server.current_node,
                                             inPiece=opts.piece if opts.piece else None,
                                             inCurrent=True,
                                             inChilds=True if opts.childs else False,
                                             useRecursion=True if opts.recursion else False,
                                             objClass=Axis)
        for item in axis_list:
            if opts.install:
                if opts.address:
                    item.install(opts.address)
                else:
                    print 'please give satellite ip'
            if opts.start:
                item.start()
            if opts.stop:
                item.stop()
            if opts.uninstall:
                item.uninstall()
            if opts.check:
                item.check()

    @options([make_option('-p', '--piece', type='string', help='piece name'),
              make_option('--recursion', action='store_true', help='get childs  with recursion'),
              make_option('-c', '--childs', action='store_true', help='get childs '),

              make_option('--show', action='store_true', help='get crontab '),
              make_option('--collect', action='store_true', help='get crontab '),
              make_option('--list', action='store_true', help='get crontab '),
              make_option('--cronid', type='string', help='get crontab '),
              make_option('--delete', action='store_true', help='get crontab '),
              make_option('--disable', action='store_true', help='get crontab '),
              make_option('--enable', action='store_true', help='get crontab '),
              make_option('--change_group', action='store_true', help='get crontab '),
    ])
    def do_crontab(self, arg, opts=None):
        from node import Crontab

        crontab_list = self._get_operation_list(self.server.current_node,
                                                inPiece=opts.piece if opts.piece else None,
                                                inCurrent=True,
                                                inChilds=True if opts.childs else False,
                                                useRecursion=True if opts.recursion else False,
                                                objClass=Crontab)
        for item in crontab_list:
            if item.judge_available():
                if opts.show:
                    item.show()
                if opts.collect:
                    item.collect()
                if opts.list:
                    item.list()
                if opts.delete:
                    item.delete(opts.cronid)
                if opts.disable:
                    item.disable(opts.cronid)
                if opts.enable:
                    item.enable(opts.cronid)
                if opts.change_group:
                    item.list()
                    group_name = self.select(Crontab.groups, prompt='Your choice group?')
                    cronid_list = raw_input('Please give crondbid list spliting with comma:')
                    if cronid_list:
                        item.change_group(group_name, *string.split(cronid_list, ','))

    @options([make_option('-p', '--piece', type='string', help='piece name'),
              make_option('--recursion', action='store_true', help='get childs  with recursion'),
              make_option('-c', '--childs', action='store_true', help='get childs '),

              make_option('--sport', type='string', help='get childs '),
              make_option('--databases', type='string', help='get childs '),
              make_option('--no_data', action='store_true', help='get childs '),
              
              make_option('--backup', action='store_true', help='get childs '),
              make_option('--merage', action='store_true', help='get childs '),
              
              make_option('--dserver', type='string', help='get childs '),
              make_option('--dport', type='string', help='get childs ')
    ])
    def do_mysql(self, arg, opts=None):
        from node import MySQL
        mysql = MySQL(self.server.current_node)
        if opts.dserver:
            dest_server = None
            line = string.strip(opts.dserver)
            dbid = line
            if string.find(line, '[') != -1:
                (dbid, info) = string.split(line, '[')
                (dbid, info) = string.split(info, ':')
                dest_server = self.server.current_node.get_node(int(dbid))
            if dest_server is None:
                print 'Not find the destination :%s' % line
                return            
        if opts.backup  and opts.sport:
            backup_path=mysql.backup(db_name=opts.databases if opts.databases else None, port=opts.sport,
                                     no_data=True if opts.no_data else False)
            if len(backup_path)>0 :
                print "Backup databases [%s] finished -> %s:%s " % (opts.databases,mysql.server,backup_path)
                if opts.dserver:
                    trans=Transfer(mysql.server,backup_path)
                    trans.add_dest_server(dest_server)
                    trans.send('/home/databackup/')
                    print "Trans backup file finished -> %s:%s " % (dest_server,'/home/databackup/')                    
        if opts.merage and opts.sport and opts.dserver and opts.dport:
            
            #db_lists=None
            #if opts.databases:
            #db_lists=string.split(opts.databases,',')
            #else:
            #db_lists=[None]
            mysql.merage(opts.databases, sport=opts.sport, dest_server=dest_server, dport=opts.dport,
                         bk_nodata=True if opts.no_data else False)
            return

        #operation_list = self._get_operation_list(self.server.current_node,
                                                  #inPiece=opts.piece if opts.piece else None,
                                                  #inCurrent=True,
                                                  #inChilds=True if opts.childs else False,
                                                  #useRecursion=True if opts.recursion else False,
                                                  #objClass=MySQL)

        #for item in operation_list:
            #pass

    def do_go(self, line):
        line = string.strip(line)
        cnode = self.mode.cd(line)
        self.__set_prompt(cnode)
        

class Logger(object):
    def __init__(self, filename="Default.log"):
        self.terminal = sys.stdout
        self.log = open(filename, "a")
        self.mode = 'ip or product'
        self.current = 'target'

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        self.terminal.flush()
        self.log.flush()

    def close(self):
        self.terminal.close()
        self.log.close()

    def isatty(self):
        return False

        #def import_file(modulename):
        #dirname = os.path.dirname(os.path.abspath(modulename))
        #filename, ext = os.path.splitext(os.path.basename(modulename))
        #if ext.lower() != '.py':
        #return {}, {}
        #if sys.modules.has_key(filename):
        #del sys.modules[filename]
        #if dirname:
        #sys.path.insert(0, dirname)
        #mod = __import__(filename)
        #if dirname:
        #del sys.path[0]
        #return mod


def main():
    #log_file=r"dbpizza.log"
    #sys.stdout = Logger(log_file)
    #sys.stderr = sys.stdout
    if len(sys.argv) > 1:
        PizzaShell().onecmd(' '.join(sys.argv[1:]))
    else:
        PizzaShell().cmdloop()


if __name__ == '__main__':
    main()
