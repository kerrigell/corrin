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
from sqlalchemy.orm import relationship,backref
import ConfigParser
import time, datetime
import sys, os.path
from alembic.config import Config
from alembic import command


def _get_db_string():
    config = ConfigParser.SafeConfigParser()
    base_path = os.path.dirname(os.path.abspath(__file__))
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
#session = Session()



#这样写会不会每次调用模块都会被调用，相同的功能添加到init_db()中了
#Base.metadata.create_all(engine)

def init_db():
    BaseModel.metadata.create_all(engine)
    base_path = os.path.dirname(os.path.abspath(__file__))
    alembic_cfg_file = os.path.join(base_path, "alembic.ini")
    alembic_cfg = Config(alembic_cfg_file)
    ## Initialize the alembic version after fully create a new database by "create_all"
    # command.stamp(alembic_cfg, "head")
def drop_db():
    BaseModel.metadata.drop_all(engine)

class BaseModel(Base):
    __abstract__ = True
    __table_args__ = {
        'mysql_engine':'InnoDB',
        'mysql_charset':'utf8'
        }

    # use a session every record
    # session=Session()

    @classmethod
    def get(cls,  value ,filter='id', columns=None, lock_mode=None,first=False):
        result=None
        try:
            session=Session()
            if hasattr(cls,filter):
                scalar = False
                if columns:
                    if isinstance(columns, (tuple, list)):
                        query = session.query(*columns)
                    else:
                        scalar = True
                        query = session.query(columns)
                else:
                    query = session.query(cls)
                if lock_mode:
                    query = query.with_lockmode(lock_mode)
                if isinstance(value,(list,tuple)):
                    query=query.filter(getattr(cls,filter).in_(value))
                else:
                    query=query.filter(getattr(cls,filter) == value)
                if scalar:
                    result = query.scalar()
                if first:
                    result = query.first()
                else:
                    result = query.all()
            else:
                result = None
        except Exception,e:
            print e
            if session:
                session.rollback()
            result = None
        finally:
            if session:
                session.close()
            return result


    #@classmethod
    #def count_all(cls, lock_mode=None):
        #query = cls.session.query(func.count('*')).select_from(cls)
        #if lock_mode:
            #query = query.with_lockmode(lock_mode)
        #return query.scalar()


    #@classmethod
    #def exist(cls,  id, lock_mode=None):
        #if hasattr(cls, 'id'):
            #query = cls.session.query(func.count('*')).select_from(cls).filter(cls.id == id)
            #if lock_mode:
                #query = query.with_lockmode(lock_mode)
            #return query.scalar() > 0
        #return False




    @classmethod
    def set_attrs(cls,  id, **attrs):
        try:
            session=Session()
            if hasattr(cls, 'id'):
                session.query(cls).filter(cls.id == id).update(attrs)
                session.commit()
        except Exception,e:
            print e
            if session:
                session.rollback()
        finally:
            if session:
                session.close()


    @classmethod
    def add(cls, **attrs):
        try:
            session=Session()
            cls.session.add(cls(**attrs))
            cls.session.commit()
        except Exception,e:
            print e
            if session:
                session.rollback()
        finally:
            if session:
                session.close()

    @classmethod
    def delete(cls,value,filter='id'):
        try:
            session=Session()
            for ins in cls.get(value,filter):
                session.delete(ins)
            session.commit()
        except Exception,e:
            print e
            if session:
                session.rollback()
        finally:
            if session:
                session.close()





class t_region(BaseModel):
    __tablename__ = 't_region'
    #MySQL 5.5 开始支持存储 4 字节的 UTF-8 编码的字符了，iOS 里自带的 emoji（如 🍎 字符）就属于这种。
    #如果是对表来设置的话，可以把上面代码中的 utf8 改成 utf8mb4，DB_CONNECT_STRING 里的 charset 也这样更改。
    id = Column(Integer, primary_key=True)
    code = Column(VARCHAR(3))
    name = Column(VARCHAR(50))


class t_product(BaseModel):
    __tablename__ = 't_product'
    id = Column(Integer, primary_key=True)
    code = Column(VARCHAR(20))
    name = Column(VARCHAR(50))


class t_server(BaseModel):
    __tablename__ = 't_server'
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
        try:
            session=Session()
            ret = session.query(col).filter(col != None).distinct().all()
        finally:
            if session:
                session.close()
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
        try:
            session=Session()
            result = session.query(t_server)
        finally:
            if session:
                session.close()
        for value, col in knife.iteritems():
            result = result.filter(col == value)
        result = result.all()
        return [i.id for i in result]


class t_feature(BaseModel):
    __tablename__ = 't_feature'
    id = Column(Integer, primary_key=True)
    pid = Column(Integer)
    feature = Column(VARCHAR(50))
    detail = Column(VARCHAR(50))
    server_id = Column(Integer)


class t_ipsec(BaseModel):
    __tablename__ = 't_ipsec'
    id = Column(Integer, primary_key=True)
    server_id = Column(Integer, index=True)
    chain = Column(Enum('INPUT', 'OUTPUT', 'FORWARD'))
    source_addr = Column(VARCHAR(50))
    dest_addr = Column(VARCHAR(50))
    protocal = Column(Enum('tcp', 'udp', 'icmp', 'all'))
    dport = Column(VARCHAR(50))
    #
    status = Column(Integer)
    description = Column(VARCHAR(100))
    create_time = Column(DATETIME)
    modify_time = Column(DATETIME)

    def __init__(self, server_id, protocal, source_addr, dport, description, status=0, chain='INPUT'):
        self.chain = chain
        self.server_id = server_id
        self.chain = chain
        self.source_addr = source_addr
        self.protocal = protocal
        self.dport = dport
        self.status = status
        self.description = description
        self.create_time = datetime.datetime.now()
        self.modify_time = datetime.datetime.now()


class t_sysinfo(BaseModel):
    __tablename__ = 't_sysinfo'
    id = Column(Integer, primary_key=True)
    need_id = Column(Integer)
    need_value = Column(VARCHAR(50))
    check_name = Column(VARCHAR(40))
    check_cmd = Column(VARCHAR(255))
    sys_type = Column(Enum('Windows', 'Linux', 'All'), index=True)
    result_reg = Column(VARCHAR(50))
    record_table = Column(VARCHAR(50))
    record_field = Column(VARCHAR(50))


class t_crontab(BaseModel):
    __tablename__ = 't_crontab'
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


class t_iptables(BaseModel):
    __tablename__ = 't_iptables'
    id = Column(Integer, primary_key=True)
    server_id = Column(Integer)
    trx_id = Column(VARCHAR(16))
    trx_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))


class t_iptables_rules(BaseModel):
    __tablename__ = 't_iptables_rules'
    id = Column(Integer, primary_key=True)
    trx_id = Column(VARCHAR(16))
    index = Column(TINYINT)
    table = Column(VARCHAR(16))
    chain = Column(VARCHAR(50))
    opt = Column(VARCHAR(150))
    arg = Column(VARCHAR(150))


