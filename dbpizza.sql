-- MySQL dump 10.13  Distrib 5.6.15, for Linux (x86_64)
--
-- Host: localhost    Database: dbpizza
-- ------------------------------------------------------
-- Server version	5.6.15

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `check_server_list`
--

DROP TABLE IF EXISTS `check_server_list`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `check_server_list` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `pid` int(11) DEFAULT NULL COMMENT '依赖ID',
  `need_pvalue` varchar(100) DEFAULT NULL,
  `check_name` varchar(100) DEFAULT NULL,
  `check_command` varchar(100) DEFAULT NULL,
  `filter_command` varchar(100) DEFAULT NULL,
  `fix_command` varchar(100) DEFAULT NULL,
  `result_table` varchar(50) DEFAULT NULL COMMENT '指定信息存储表名',
  `result_field` varchar(50) DEFAULT NULL COMMENT '指定信息存储表的字段名',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `checklist_entry`
--

DROP TABLE IF EXISTS `checklist_entry`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `checklist_entry` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `target` varchar(50) DEFAULT NULL COMMENT '¼ì²é¶ÔÏó',
  `item` varchar(200) DEFAULT NULL COMMENT '¼ì²éÏî',
  `mothed` varchar(200) DEFAULT NULL COMMENT '¼ì²é·½·¨',
  `require` varchar(200) DEFAULT NULL COMMENT 'Í¨¹ýÌõ¼þ',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `checklist_event`
--

DROP TABLE IF EXISTS `checklist_event`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `checklist_event` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `job_id` varchar(50) NOT NULL COMMENT 'ÒµÎñ²Ù×÷',
  `checkorder` int(11) NOT NULL COMMENT '¼ì²éÐòÁÐ',
  `entry_id` int(11) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `checklist_event_history`
--

DROP TABLE IF EXISTS `checklist_event_history`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `checklist_event_history` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `checklist_job`
--

DROP TABLE IF EXISTS `checklist_job`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `checklist_job` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(50) DEFAULT NULL COMMENT 'ÒµÎñ²Ù×÷',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `checklist_job_history`
--

DROP TABLE IF EXISTS `checklist_job_history`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `checklist_job_history` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `db_schemas`
--

DROP TABLE IF EXISTS `db_schemas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `db_schemas` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT COMMENT '×ÔÔöID',
  `update_time` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00' ON UPDATE CURRENT_TIMESTAMP COMMENT 'ÐÞ¸ÄÊ±¼ä',
  `create_time` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00' COMMENT '´´½¨Ê±¼ä',
  `is_deleted` tinyint(1) DEFAULT '0' COMMENT 'É¾³ý±ê¼Ç',
  `server_id` int(10) unsigned NOT NULL COMMENT 'ËùÊô·þÎñÆ÷ID',
  `instance_port` smallint(5) unsigned DEFAULT NULL COMMENT 'ËùÊôÊµÀý¶Ë¿ÚºÅ',
  `schema_name` varchar(50) DEFAULT NULL COMMENT 'schemaÃû',
  `schema_role` enum('usercenter','gamecenter','recharge','stat','log','sns','gmdb','gamedb') DEFAULT NULL COMMENT 'schema½ÇÉ«',
  `schema_desc` varchar(250) DEFAULT NULL COMMENT '¹¦ÄÜÃèÊö',
  `gamedb_group` varchar(50) DEFAULT NULL COMMENT 'ÓÎÏ·DB×éºÅ',
  `all_db_users` varchar(250) DEFAULT NULL COMMENT '·ÃÎÊÁÐ±í',
  `is_gamedb` tinyint(1) DEFAULT '1' COMMENT 'ÊÇ·ñÓÎÏ·DB',
  `is_slave` tinyint(1) DEFAULT '0' COMMENT 'ÊÇ·ñÎªslave',
  `is_online` tinyint(1) DEFAULT '1' COMMENT 'ÊÇ·ñÏßÉÏ',
  `nation` enum('hk','vn','id','in','tw','th','us','my') DEFAULT NULL COMMENT 'µØÇø',
  `product` enum('tlbb','ldj','taoyuan','guyu','totem','specialforce','gamefuse','oppaplay','gamiction','cuaban','davinci','swordgirls','common') DEFAULT NULL COMMENT '²úÆ·',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `t_backup_info`
--

DROP TABLE IF EXISTS `t_backup_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `t_backup_info` (
  `ID` bigint(10) NOT NULL AUTO_INCREMENT,
  `locale` varchar(5) DEFAULT NULL,
  `product` varchar(15) DEFAULT NULL,
  `db_type` varchar(5) DEFAULT NULL,
  `backup_type1` varchar(5) DEFAULT NULL,
  `backup_type2` varchar(5) DEFAULT NULL,
  `save_time` int(4) DEFAULT NULL,
  `ip` varchar(20) DEFAULT NULL,
  `status` char(8) DEFAULT NULL,
  `people` varchar(20) DEFAULT NULL,
  `zone` varchar(20) DEFAULT NULL,
  `port` int(6) DEFAULT NULL,
  `db_name` varchar(20) DEFAULT NULL,
  `bak_type` char(5) DEFAULT NULL,
  `character_set` char(6) DEFAULT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `t_backup_server`
--

DROP TABLE IF EXISTS `t_backup_server`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `t_backup_server` (
  `ID` bigint(10) NOT NULL AUTO_INCREMENT,
  `locale` varchar(5) DEFAULT NULL,
  `product` varchar(5) DEFAULT NULL,
  `IP` varchar(20) DEFAULT NULL,
  `db_type` varchar(5) DEFAULT NULL,
  `backup_type1` varchar(5) DEFAULT NULL,
  `backup_type2` varchar(5) DEFAULT NULL,
  `save_time` int(4) DEFAULT NULL,
  `people` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `t_crontab`
--

DROP TABLE IF EXISTS `t_crontab`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `t_crontab` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `server_id` int(11) unsigned DEFAULT NULL,
  `pminute` varchar(20) DEFAULT NULL,
  `phour` varchar(20) DEFAULT NULL,
  `pday` varchar(20) DEFAULT NULL,
  `pmonth` varchar(20) DEFAULT NULL,
  `pweek` varchar(20) DEFAULT NULL,
  `process` varchar(400) DEFAULT NULL,
  `status` int(5) DEFAULT NULL COMMENT '1 run 0 not use',
  `user` varchar(20) DEFAULT NULL,
  `group` varchar(20) DEFAULT NULL,
  `operator` varchar(30) DEFAULT NULL,
  `description` varchar(100) DEFAULT NULL,
  `create_time` timestamp NULL DEFAULT NULL,
  `update_time` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `t_feature`
--

DROP TABLE IF EXISTS `t_feature`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `t_feature` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `pid` int(11) DEFAULT NULL,
  `feature` varchar(50) DEFAULT NULL,
  `detail` varchar(100) DEFAULT NULL,
  `server_id` int(11) unsigned DEFAULT NULL,
  `fabric` varchar(50) DEFAULT NULL,
  `exec_info` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `t_ipsec`
--

DROP TABLE IF EXISTS `t_ipsec`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `t_ipsec` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `server_id` int(11) DEFAULT NULL,
  `chain` enum('FORWARD','OUTPUT','INPUT') DEFAULT NULL,
  `source_addr` varchar(50) DEFAULT NULL,
  `dest_addr` varchar(50) DEFAULT NULL,
  `protocal` enum('all','icmp','udp','tcp') DEFAULT NULL,
  `dport` varchar(100) DEFAULT NULL,
  `status` tinyint(4) DEFAULT NULL,
  `description` varchar(100) DEFAULT NULL,
  `createdate` datetime DEFAULT NULL,
  `modifydate` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `t_ipsec_server_id` (`server_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `t_iptables`
--

DROP TABLE IF EXISTS `t_iptables`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `t_iptables` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `server_id` int(10) unsigned NOT NULL,
  `trx_id` varchar(16) NOT NULL,
  `trx_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `t_iptables_rules`
--

DROP TABLE IF EXISTS `t_iptables_rules`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `t_iptables_rules` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `trx_id` varchar(16) NOT NULL,
  `index` tinyint(11) NOT NULL,
  `table` varchar(16) NOT NULL,
  `chain` varchar(50) NOT NULL,
  `opt` varchar(150) NOT NULL,
  `arg` varchar(150) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `t_server`
--

DROP TABLE IF EXISTS `t_server`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `t_server` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT COMMENT 'è‡ªå¢žID',
  `pid` int(10) unsigned DEFAULT NULL COMMENT 'çˆ¶ID',
  `region` varchar(4) DEFAULT NULL COMMENT 'åœ°åŒº',
  `product` varchar(40) DEFAULT NULL COMMENT 'äº§å“',
  `role` varchar(15) DEFAULT NULL COMMENT 'æœåŠ¡å™¨è§’è‰²',
  `loginuser` varchar(40) DEFAULT 'root',
  `description` varchar(250) DEFAULT NULL,
  `ip_oper` varchar(100) DEFAULT NULL COMMENT 'è¿ç»´æ“ä½œIP',
  `ip_private` varchar(16) DEFAULT NULL COMMENT 'ç§ç½‘IP',
  `ip_public` varchar(16) DEFAULT NULL COMMENT 'å…¬ç½‘IP',
  `ip_ilo` varchar(16) DEFAULT NULL COMMENT 'ILO IP',
  `ip_monitor` varchar(16) DEFAULT NULL,
  `ip_ntp_server` varchar(16) DEFAULT NULL,
  `is_reserve` tinyint(1) DEFAULT '0' COMMENT 'æ˜¯å¦ä¸ºå¤‡æœº',
  `is_online` tinyint(1) DEFAULT '0',
  `dbms` varchar(20) DEFAULT NULL COMMENT 'å…³ç³»æ•°æ®åº“',
  `vender` varchar(20) DEFAULT NULL COMMENT 'æœåŠ¡å™¨åŽ‚å•†',
  `model` varchar(100) DEFAULT NULL COMMENT 'æœåŠ¡å™¨äº§å“å',
  `serial` varchar(50) DEFAULT NULL,
  `os_type` varchar(20) DEFAULT NULL COMMENT 'æ“ä½œç³»ç»Ÿç±»åž‹',
  `os_release` varchar(20) DEFAULT NULL COMMENT 'æ“ä½œç³»ç»Ÿç‰ˆæœ¬',
  `os_arch` varchar(20) DEFAULT NULL COMMENT '32/64ä½',
  `update_time` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00' ON UPDATE CURRENT_TIMESTAMP COMMENT 'ä¿®æ”¹æ—¶é—´',
  `create_time` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00' COMMENT 'åˆ›å»ºæ—¶é—´',
  `is_deleted` tinyint(1) DEFAULT '0' COMMENT 'åˆ é™¤æ ‡è®°',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `t_sysinfo`
--

DROP TABLE IF EXISTS `t_sysinfo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `t_sysinfo` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `need_id` int(11) unsigned DEFAULT NULL,
  `need_value` varchar(50) DEFAULT NULL,
  `check_name` varchar(40) DEFAULT NULL,
  `check_cmd` varchar(255) DEFAULT NULL,
  `sys_type` enum('Windows','Linux') DEFAULT NULL,
  `result_reg` varchar(100) DEFAULT NULL,
  `record_table` varchar(30) DEFAULT NULL,
  `record_field` varchar(30) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_t_sysinfo_systype` (`sys_type`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2013-12-18 12:34:01
