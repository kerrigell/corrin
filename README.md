# corrin
Automatically exported from code.google.com/p/corrin

**Corrin**  是一个服务器运维管理工具，主要优点:

* 管理具有SSH信任管理的运维拓扑服务器
* 只需在中央节点上进行安装和操作
* 依据需求进行节点筛选，批量执行
* 模块化架构设计
* 具有一定代码级别功能扩展能力

## 命令来源
corrin 中文称为咕啉，取自维生素 B12 化学结构。
```
维生素B12是B族维生素中迄今为止发现最晚的一种。维生素B12是一种含有3价钴的多环系化合物，4个还原的吡咯环连在一起变成为1个咕啉大环，是维生素B12分子的核心。是红血球生成不可缺少的重要元素，如果严重缺乏，将导致恶性贫血。
```

服务器维护网络同咕啉环结构相似，希望成为运维工作的得力助手。

## 设计理念

* 节点树状组织结构：从中央节点延展出2层、3层或者更多层的树状结构，以同心圆的方式展示，便成为星形散射装分布。
* 每台被操作服务器，即这个结构上的一个节点。这些节点信息，保存在中央机器的数据库中，由父子关系计算出行动路径，再依据一些配置执行命令。
* 日常运维工作中操作点比较多，但抽象出来无非是三种操作：执行命令、传输文件、记录信息。所以，实现这三种操作，便可以通过拆分操作然后进行排列组合即可实现功能上的扩展。

## 主要功能
* 利用数据关系，构建服务器节点网络
* 通过中央节点发送命令，控制节点操作，同时不限于中央对操作服务器操作。
* 实现任意节点间操作，如mysql数据库迁移，控制A节点备份，计算节点路径，传输，B节点恢复

## 架构设计
此工具使用Python语言编写



|逻辑层	|主要功能|	Python模块	|代码类|
|---|---|---|---|
|操作层	|完成用户操作，主要命令行操作|	cmd2	|PizzaShell|
|筛选层	|实现网络节点条件筛选		|||
|逻辑层	|实现单台目标或单功能操作||		NodeNet?/Server/IPsec等等|
　|数据层|	对数据库进行读写|	sqlalchemy|	t_server等以调用类名称定义的数据对象类|
|分发层|	实现操作对象多线程分发	||	Parallel(待实现)|
|执行层|	给目标服务器发送操作指令|	Fabric|	Server.execute|


## 部署依赖
- Linux 5.+版本操作系统
- python 2.7.3+
- Fabric 1.8
- sqlalchemy 0.8.1
- cmd2 0.6.7
- paramiko 1.12.0
- pycrypto 2.6
- mysqld 5.5+
- prettytable 0.7.2


## 使用帮助
## 部署安装?
## 工具shell介绍
## 记录点滴
* 设计初期以披萨为原型，节点为肉食点缀，管理区域为切割块。 
* 为数据管理层面开发的web端命名为 office
* 曾经共同开发人 ：P海洋

