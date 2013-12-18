/*
Navicat MySQL Data Transfer

Source Server         : 10.127.64.248
Source Server Version : 50515
Source Host           : 10.127.64.248:3306
Source Database       : dbpizza

Target Server Type    : MYSQL
Target Server Version : 50599
File Encoding         : 65001

Date: 2013-12-18 21:15:56
*/

SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for `t_crontab`
-- ----------------------------
DROP TABLE IF EXISTS `t_crontab`;
CREATE TABLE `t_crontab` (
`id`  int(11) UNSIGNED NOT NULL AUTO_INCREMENT ,
`server_id`  int(11) UNSIGNED NULL DEFAULT NULL ,
`pminute`  varchar(20) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL ,
`phour`  varchar(20) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL ,
`pday`  varchar(20) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL ,
`pmonth`  varchar(20) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL ,
`pweek`  varchar(20) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL ,
`process`  varchar(400) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL ,
`status`  int(5) NULL DEFAULT NULL COMMENT '1 run 0 not use' ,
`user`  varchar(20) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL ,
`group`  varchar(20) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL ,
`operator`  varchar(30) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL ,
`description`  varchar(100) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL ,
`create_time`  timestamp NULL DEFAULT NULL ,
`update_time`  timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP ,
PRIMARY KEY (`id`)
)
ENGINE=InnoDB
DEFAULT CHARACTER SET=latin1 COLLATE=latin1_swedish_ci
AUTO_INCREMENT=1618

;

-- ----------------------------
-- Table structure for `t_feature`
-- ----------------------------
DROP TABLE IF EXISTS `t_feature`;
CREATE TABLE `t_feature` (
`id`  int(11) UNSIGNED NOT NULL AUTO_INCREMENT ,
`pid`  int(11) NULL DEFAULT NULL ,
`feature`  varchar(50) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL ,
`detail`  varchar(100) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL ,
`server_id`  int(11) UNSIGNED NULL DEFAULT NULL ,
`fabric`  varchar(50) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL ,
`exec_info`  varchar(200) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL ,
PRIMARY KEY (`id`)
)
ENGINE=InnoDB
DEFAULT CHARACTER SET=latin1 COLLATE=latin1_swedish_ci
AUTO_INCREMENT=11

;

-- ----------------------------
-- Table structure for `t_ipsec`
-- ----------------------------
DROP TABLE IF EXISTS `t_ipsec`;
CREATE TABLE `t_ipsec` (
`id`  int(11) UNSIGNED NOT NULL AUTO_INCREMENT ,
`server_id`  int(11) NULL DEFAULT NULL ,
`chain`  enum('FORWARD','OUTPUT','INPUT') CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL ,
`source_addr`  varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL ,
`dest_addr`  varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL ,
`protocal`  enum('all','icmp','udp','tcp') CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL ,
`dport`  varchar(100) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL ,
`status`  tinyint(4) NULL DEFAULT NULL ,
`description`  varchar(100) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL ,
`createdate`  datetime NULL DEFAULT NULL ,
`modifydate`  timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP ,
PRIMARY KEY (`id`),
INDEX `t_ipsec_server_id` (`server_id`) USING BTREE 
)
ENGINE=InnoDB
DEFAULT CHARACTER SET=utf8 COLLATE=utf8_general_ci
AUTO_INCREMENT=116

;

-- ----------------------------
-- Table structure for `t_server`
-- ----------------------------
DROP TABLE IF EXISTS `t_server`;
CREATE TABLE `t_server` (
`id`  int(10) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'è‡ªå¢žID' ,
`pid`  int(10) UNSIGNED NULL DEFAULT NULL COMMENT 'çˆ¶ID' ,
`region`  varchar(4) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'åœ°åŒº' ,
`product`  varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'äº§å“' ,
`role`  varchar(15) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'æœåŠ¡å™¨è§’è‰²' ,
`loginuser`  varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT 'root' ,
`description`  varchar(250) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL ,
`ip_oper`  varchar(100) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'è¿ç»´æ“ä½œIP' ,
`ip_private`  varchar(16) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'ç§ç½‘IP' ,
`ip_public`  varchar(16) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'å…¬ç½‘IP' ,
`ip_ilo`  varchar(16) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'ILO IP' ,
`ip_monitor`  varchar(16) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL ,
`ip_ntp_server`  varchar(16) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL ,
`is_reserve`  tinyint(1) NULL DEFAULT 0 COMMENT 'æ˜¯å¦ä¸ºå¤‡æœº' ,
`is_online`  tinyint(1) NULL DEFAULT 0 ,
`dbms`  varchar(20) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'å…³ç³»æ•°æ®åº“' ,
`vender`  varchar(20) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'æœåŠ¡å™¨åŽ‚å•†' ,
`model`  varchar(100) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'æœåŠ¡å™¨äº§å“å' ,
`serial`  varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL ,
`os_type`  varchar(20) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'æ“ä½œç³»ç»Ÿç±»åž‹' ,
`os_release`  varchar(20) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'æ“ä½œç³»ç»Ÿç‰ˆæœ¬' ,
`os_arch`  varchar(20) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '32/64ä½' ,
`update_time`  timestamp NOT NULL DEFAULT '0000-00-00 00:00:00' ON UPDATE CURRENT_TIMESTAMP COMMENT 'ä¿®æ”¹æ—¶é—´' ,
`create_time`  timestamp NOT NULL DEFAULT '0000-00-00 00:00:00' COMMENT 'åˆ›å»ºæ—¶é—´' ,
`is_deleted`  tinyint(1) NULL DEFAULT 0 COMMENT 'åˆ é™¤æ ‡è®°' ,
PRIMARY KEY (`id`)
)
ENGINE=InnoDB
DEFAULT CHARACTER SET=utf8 COLLATE=utf8_general_ci
AUTO_INCREMENT=337

;

-- ----------------------------
-- Table structure for `t_sysinfo`
-- ----------------------------
DROP TABLE IF EXISTS `t_sysinfo`;
CREATE TABLE `t_sysinfo` (
`id`  int(11) UNSIGNED NOT NULL AUTO_INCREMENT ,
`need_id`  int(11) UNSIGNED NULL DEFAULT NULL ,
`need_value`  varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL ,
`check_name`  varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL ,
`check_cmd`  varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL ,
`sys_type`  enum('Windows','Linux') CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL ,
`result_reg`  varchar(100) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL ,
`record_table`  varchar(30) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL ,
`record_field`  varchar(30) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL ,
PRIMARY KEY (`id`),
INDEX `idx_t_sysinfo_systype` (`sys_type`) USING BTREE 
)
ENGINE=InnoDB
DEFAULT CHARACTER SET=utf8 COLLATE=utf8_general_ci
AUTO_INCREMENT=39

;

-- ----------------------------
-- Auto increment value for `t_crontab`
-- ----------------------------
ALTER TABLE `t_crontab` AUTO_INCREMENT=1618;

-- ----------------------------
-- Auto increment value for `t_feature`
-- ----------------------------
ALTER TABLE `t_feature` AUTO_INCREMENT=11;

-- ----------------------------
-- Auto increment value for `t_ipsec`
-- ----------------------------
ALTER TABLE `t_ipsec` AUTO_INCREMENT=116;

-- ----------------------------
-- Auto increment value for `t_server`
-- ----------------------------
ALTER TABLE `t_server` AUTO_INCREMENT=337;

-- ----------------------------
-- Auto increment value for `t_sysinfo`
-- ----------------------------
ALTER TABLE `t_sysinfo` AUTO_INCREMENT=39;
