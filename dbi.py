#!/usr/bin/env python
#coding:utf-8
# Author:  Haiyang Peng
# Purpose:
# Created: 2013/6/28
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, BigInteger, VARCHAR, Text, DateTime, DATETIME, SMALLINT, TIMESTAMP, Boolean
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.types import SchemaType, TypeDecorator, Enum
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.expression import text
import ConfigParser
import time, datetime
import sys, os.path


def _get_db_string():
    config = ConfigParser.SafeConfigParser()
    base_path = os.path.split(os.path.realpath(sys.argv[0]))[0]
    config.read(os.path.join(base_path, "config/dbi.ini"))
    dblink = """%s://%s%s@%s/%s?charset=%s""" % (config.get('database', 'engine'),
                                                 config.get('database', 'user'),
                                                 config.get('database', 'password') if config.get('database',
                                                                                                  'password') else '',
                                                 config.get('database', 'host'),
                                                 config.get('database', 'database'),
                                                 config.get('database', 'charset'))
    return dblink


engine = create_engine(_get_db_string(), pool_size=4, pool_recycle=10, max_overflow=10)
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()


class t_region(Base):
    __tablename__ = 't_region'
    __table_args__ = {'mysql_engine': 'InnoDB'}
    id = Column(Integer, primary_key=True)
    code = Column(VARCHAR(3))
    name = Column(VARCHAR(50))


class t_product(Base):
    __tablename__ = 't_product'
    __table_args__ = {'mysql_engine': 'InnoDB'}
    id = Column(Integer, primary_key=True)
    code = Column(VARCHAR(20))
    name = Column(VARCHAR(50))


class t_server(Base):
    __tablename__ = 't_server'
    __table_args__ = {'mysql_engine': 'InnoDB'}
    __searchword__ = None
    id = Column(Integer, primary_key=True)
    pid = Column(Integer, nullable=True)
    # 记录上层硬件所属ID，用途：虚拟机-》物理机
    mid = Column(Integer, nullable=True)
    region = Column(Enum('hk', 'vn', 'id', 'in', 'tw', 'th', 'us', 'my', 'cn'))
    product = Column(
        Enum('tlbb', 'ldj', 'taoyuan', 'guyu', 'totem', 'specialforce', 'gamefuse', 'oppaplay', 'gamiction', 'cuaban',
             'davinci', 'swordgirls', 'zszw', 'common', 'pengyou'))
    role = Column(Enum('cc', 'backup', 'db'))
    loginuser = Column(VARCHAR(40), server_default='root')
    description = Column(VARCHAR(250))
    ip_oper = Column(VARCHAR(16))
    ip_private = Column(VARCHAR(16))
    ip_public = Column(VARCHAR(16))
    ip_ilo = Column(VARCHAR(16))
    is_reserve = Column(Boolean, server_default='0')
    dbms = Column(Enum('MySQL', 'Oracle', 'MSSQL'))
    vender = Column(Enum('Dell', 'HP', 'VMware', 'Intel', 'Xen'))
    model = Column(VARCHAR(100))
    os_type = Column(Enum('Linux', 'Windows'))
    os_release = Column(Enum('RHEL_5_3', 'RHEL_4_8', 'RHEL_4_6', 'CENT_6_3', 'WIN2003', 'WIN2008'))
    os_arch = Column(Enum('x86_64', 'i386'))
    ip_monitor = Column(VARCHAR(16))
    ip_ntp_server = Column(VARCHAR(16))
    serial = Column(VARCHAR(50))
    is_online = Column(Boolean, server_default='0')
    update_time = Column(TIMESTAMP, server_default=text('0 ON UPDATE CURRENT_TIMESTAMP'))
    create_time = Column(TIMESTAMP, server_default=text('0'))
    is_deleted = Column(Boolean)

    def __repr__(self):
        return "<Server('%s','%s','%s')>" % (self.region, self.product, self.ip_oper)

    @classmethod
    def _all_words(cls):
        if cls.__searchword__:
            return cls.__searchword__
        words = []
        words += cls._get_word(t_server.region)
        words += cls._get_word(t_server.product)
        words += cls._get_word(t_server.role)
        words += cls._get_word(t_server.dbms)
        words += cls._get_word(t_server.vender)
        words += cls._get_word(t_server.os_type)
        words += cls._get_word(t_server.os_release)
        words += cls._get_word(t_server.os_arch)
        words += [('reserve', t_server.is_reserve)]
        words = dict(words)
        cls.__searchword__ = words
        return cls.__searchword__

    @classmethod
    def _get_word(cls, col):
        ret = session.query(col).filter(col != None).distinct().all()
        return [(str(x[0]), col) for x in ret]

    @classmethod
    def piece(cls, keywords):
        import string

        keywords = string.split(keywords, ',')
        words = cls._all_words()
        knife = {}
        for i in keywords:
            if i in words.keys():
                knife[i] = words[i]
        if len(knife.keys()) <= 0:
            return []
        result = session.query(t_server)
        for value, col in knife.iteritems():
            result = result.filter(col == value)
        result = result.all()
        return [i.id for i in result]

    def update_value(self, col, value):
        if hasattr(self, col):
            setattr(self, col, value)
            session.commit()
            return 1
        else:
            print 'this tables has no field of \'%s\'' % col
            return 0


class t_feature(Base):
    __tablename__ = 't_feature'
    __table_args__ = {'mysql_engine': 'InnoDB'}
    id = Column(Integer, primary_key=True)
    pid = Column(Integer)
    feature = Column(VARCHAR(50))
    detail = Column(VARCHAR(50))
    server_id = Column(Integer)


class t_ipsec(Base):
    __tablename__ = 't_ipsec'
    __table_args__ = {'mysql_engine': 'InnoDB'}
    id = Column(Integer, primary_key=True)
    server_id = Column(Integer)
    chain = Column(Enum('INPUT', 'OUTPUT', 'FORWARD'))
    source_addr = Column(VARCHAR(50))
    dest_addr = Column(VARCHAR(50))
    protocal = Column(Enum('tcp', 'udp', 'icmp', 'all'))
    dport = Column(VARCHAR(50))
    #
    status = Column(Integer)
    description = Column(VARCHAR(100))
    # 老马看到这里的时候看看这两个字段的字段名能不能和其他表的写法统一下
    createdate = Column(DATETIME)
    modifydate = Column(DATETIME)

    def __init__(self, server_id, protocal, source_addr, dport, description, status=0, chain='INPUT'):
        self.chain = chain
        self.server_id = server_id
        self.chain = chain
        self.source_addr = source_addr
        self.protocal = protocal
        self.dport = dport
        self.status = status
        self.description = description
        self.createdate = datetime.datetime.now()
        self.modifydate = datetime.datetime.now()


class t_sysinfo(Base):
    __tablename__ = 't_sysinfo'
    __table_args__ = {'mysql_engine': 'InnoDB'}
    id = Column(Integer, primary_key=True)
    need_id = Column(Integer)
    need_value = Column(VARCHAR(50))
    check_name = Column(VARCHAR(40))
    check_cmd = Column(VARCHAR(255))
    sys_type = Column(Enum('Windows', 'Linux'))
    result_reg = Column(VARCHAR(50))
    record_table = Column(VARCHAR(50))
    record_field = Column(VARCHAR(50))


class t_crontab(Base):
    __tablename__ = 't_crontab'
    __table_args__ = {'mysql_engine': 'InnoDB'}
    id = Column(Integer, primary_key=True)
    server_id = Column(Integer)
    pminute = Column(VARCHAR(20))
    phour = Column(VARCHAR(20))
    pday = Column(VARCHAR(20))
    pmonth = Column(VARCHAR(20))
    pweek = Column(VARCHAR(20))
    process = Column(VARCHAR(400))
    status = Column(SMALLINT)
    user = Column(VARCHAR(30))
    group = Column(VARCHAR(20))
    description = Column(VARCHAR(100))
    operator = Column(VARCHAR(30))
    create_time = Column(TIMESTAMP)
    update_time = Column(TIMESTAMP)


class t_iptables(Base):
    __tablename__ = 't_iptables'
    __table_args__ = {'mysql_engine': 'InnoDB'}
    id = Column(Integer, primary_key=True)
    server_id = Column(Integer)
    trx_id = Column(VARCHAR(16))
    trx_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP')) 


class t_iptables_rules(Base):
    __tablename__ = 't_iptables_rules'
    __table_args__ = {'mysql_engine': 'InnoDB'}
    id = Column(Integer, primary_key=True)
    trx_id = Column(VARCHAR(16))
    index = Column(TINYINT)
    table = Column(VARCHAR(16))
    chain = Column(VARCHAR(50))
    opt = Column(VARCHAR(150))
    arg = Column(VARCHAR(150))

Base.metadata.create_all(engine)
