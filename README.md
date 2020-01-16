# Exploring Hadoop
[Apache Hadoop](hadoop.apache.org) is currently the most widely used open source framework for storing massive amounts of data and performing analytics operations on them. It has quite a number of moving pieces, however, and can be a bit daunting to approach, especially with dozens of additional services that can all be part of the wider *ecosystem*.

The purpose of the text and code presented here is to get familiar with a few central aspects of the core Hadoop framework and start playing around with it.


## A First Installation
Hadoop is a distributed file system, designed for holding very large files. It is optimized for read and append operations on these files. Furthermore, it supports the distributed execution of code across many machines in parallel.

Storage and execution are the two core concerns of *HDFS*, the *Hadoop Distributed File System*, and *YARN*, *Yet Another Resource Negotiator*, respectively. A simple workflow would be to take some data, store it on HDFS, then use YARN to run a piece of code to extract some information from the data.

When learning about a piece of technology, it's often a good idea to prepare a clean setup and start playing around with it. While we can discuss Hadoop in greater detail later on, let's see if we can get through the installation and configuration process for running Hadoop inside a single virtual machine.

[Single Node Setup](./1-single-node-setup/)

If you've made it through this section, you now have a running, albeit basic, Hadoop installation, and you have seen HDFS's *NameNode* and *DataNode* in action, as well als YARN's *ResourceManager* and *NodeManager* processes.
