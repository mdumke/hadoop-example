# Exploring Hadoop
[Apache Hadoop](hadoop.apache.org) is currently the most widely used open source framework for storing massive amounts of data and performing analytics operations on them. It has quite a number of moving pieces, however, and can be a bit daunting to approach, especially with dozens of additional services that can all be part of the wider *ecosystem*.

The purpose of the text and code presented here is to get familiar with a few central aspects of the core Hadoop framework and start playing around with it.


## A First Installation
Hadoop is a distributed file system, designed for holding very large files. It is optimized for read and append operations on these files. Furthermore, it supports the distributed execution of code across many machines in parallel.

Storage and execution are the two core concerns of *HDFS*, the *Hadoop Distributed File System*, and *YARN*, *Yet Another Resource Negotiator*, respectively. A simple workflow would be to take some data, store it on HDFS, then use YARN to run a piece of code to extract some information from the data.

When learning about a piece of technology, it's often a good idea to prepare a clean setup and start playing around with it. While we can discuss Hadoop in greater detail later on, let's see if we can get through the installation and configuration process for running Hadoop inside a single virtual machine:

[Single Node Setup](./1-single-node-setup/)

If you've made it through this section, you now have a running, albeit basic, Hadoop installation, and you have seen HDFS's *NameNode* and *DataNode* in action, as well als YARN's *ResourceManager* and *NodeManager* processes.


## An Example Application
Hadoop allows us to operate on data that is distributed across potentially thousands of computers, and it abstracts away the challenges of resource management and parallel execution of code. For this to work, however, we need our code to respect the basic *MapReduce* execution pattern, so let's take a look at that.

As a side note, know that there are new tools in the Hadoop environment such as [Apache Spark](http://spark.apache.org/), [Apache HBase](http://hbase.apache.org/) and many others that allow for diffent forms of interaction with Hadoop based Big Data systems. These developments make it unlikely that you'll ever be writing *MapReduce* jobs to run in production. Still, understanding the basic *MapReduce* execution pattern will enhance the ability to work with these other tools as well. And it's fun.

In order to understand how *MapReduce* works, we don't actually need Hadoop. The pattern is more general. So before running any jobs on the machine we have prepared before, let's go through a basic example that can run on a standard Unix system. In doing this, we'll also start building a tiny application, including fake data and analytics scripts, that we can reuse later on:

[Bird Tracking Example Application](./2-example-app)

Prepared with a better understanding of *MapReduce*, and with some mapper and reducer scripts at hand, let's bring our code to Hadoop and see how it executes there.
