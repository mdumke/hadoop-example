# Hadoop Single Node Setup
Without worrying too much about conceptual details upfront, let's install Hadoop 3.2.1 through its binaries and see how far we get with playing around a little bit. We will, in broad steps, follow the [official guide](https://hadoop.apache.org/docs/r3.2.1/hadoop-project-dist/hadoop-common/SingleCluster.html) for setting up Hadoop on a single computer.

```md
# prerequisites

Vagrant >= 2.2.6
VirtualBox >= 5.1.38
```

At the time of this writing in early 2020, Hadoop 3.2.1 is the latest version of the framework. Please be aware that some details of the installation process may change if you decide to select a different version.


## Preparing a Virtual Machine
We start from scratch using a fresh installation of Ubuntu 18.04 on a virtual machine. The examples will use Vagrant with VirtualBox to create a local setup, which is fast and free of charge. Of course, you can also use a different provider (e.g. AWS or DigitalOcean), or even follow along on your local computer.

A few details about our VM are specified in the [Vagrantfile](./Vagrantfile). In particular, we'll use a single machine with 4GB of memory, which is enough to run a few of the Hadoop processes, and we configure it with a local network for host-only communication, so we can access the VM from our local machine easily. Start the machine:

```sh
# initialize the virtual machine
vagrant up

# check the current machine state
vagrant status

# enter the vm
vagrant ssh
```

By default, Vagrant uses the sudo user `vagrant` for login. We'll use this account as well for our first exploration, though later on we will create dedicated accounts with restricted permissions to perform the different tasks as is best practice.


## Hadoop Download
Hadoop is open source software that can be built from source, but there are builds readily available as binaries for us to run. You can choose a download from the [recommended mirrors](https://www.apache.org/dyn/closer.cgi/hadoop/common/hadoop-3.2.1/hadoop-3.2.1.tar.gz).

```sh
# download Hadoop
cd /tmp
wget https://www-eu.apache.org/dist/hadoop/common/hadoop-3.2.1/hadoop-3.2.1.tar.gz

# compare checksum with the official one (d627...34ee)
sha512sum hadoop-3.2.1.tar.gz

# unpack
tar xzf hadoop-3.2.1.tar.gz

# move to target location
sudo mv hadoop-3.2.1 /usr/local/hadoop
```


## Installing Java 8
If we take a look at what we have just downloaded and unpacked, we see that there are some binaries files in `bin/` and `sbin/` (in the following, relative paths will refer to `/usr/local/hadoop`. However, if we try to run the hadoop command, it will complain about a missing Java installation:

```sh
# hadoop needs to know Java
/usr/local/hadoop/bin/hadoop
```

Since Hadoop 3 requires Java 8 to work properly, let's begin by installing this first.

```sh
# update cache
sudo apt update

# get Java 8
sudo apt install openjdk-8-jdk
```

At the very least, Hadoop needs to know where to find the Java installation. We can tell it in `etc/hadoop/hadoop-env.sh`:

```sh
# configure hadoop-env.sh
export JAVA_HOME=/usr/lib/jvm/java-1.8.0-openjdk-amd64
```

This should be enough to get the first sign of life from Hadoop:

```sh
# see if hadoop is there
/usr/local/hadoop/bin/hadoop version
```


## Configuring the Environment
The above command would require a lot of typing, and what's more, some of Hadoop's processes will expect certain environment variables to be set. At the very least, we should specify `HADOOP_HOME`, but while we're at it, let's update the PATH variable as well. To keep everything in one place, consider adding a new script `/etc/profile.d/hadoop.sh` that specifies the installation path:

```sh
# /etc/profile.d/hadoop.sh

export HADOOP_HOME=/usr/local/hadoop
export PATH=$HADOOP_HOME/bin:$PATH
export PATH=$HADOOP_HOME/sbin:$PATH
```

Now, log out and back into the terminal to make the variables available, or run `source /etc/profile.d/hadoop.sh`. After that, `echo $HADOOP_HOME` should display the correct value, and the following command succeeds:

```sh
# see if commands are available

hadoop version
hdfs version
yarn version
```

If we inspect the output of these commands more carefully, we find information about who compiled the build we are using and when, where the exact version of the source code can be found, and also which Java Archive (.jar-file) was used for this particular command.


## Configuring Hadoop
Hadoop is actually a suite of services. Let's start a few of those and see what happens. Along the way, we need to provide a bit of configuration through the files in `$HADOOP_HOME/etc/hadoop`.

But first of all, Hadoop needs a place to store logs, temporary files and manage processes. While there are common places for these tasks on Unix file systems, we want to keep everything in one place for now so we can quickly see how Hadoop is working and what kind of management data it produces. To this end, we create subdirectories inside the hadoop home directory for everything we need:

```sh
# create auxilliary directories

mkdir $HADOOP_HOME/tmp
mkdir $HADOOP_HOME/logs
mkdir $HADOOP_HOME/proc
```

Now let's tell Hadoop about these in `hadoop-env.sh`:

```sh
# inform hadoop about auxilliary directories

export HADOOP_LOG_DIR=${HADOOP_HOME}/logs
export HADOOP_PID_DIR=${HADOOP_HOME}/proc
```

The temporary directory is not specified in this file, but along with other machine-specific configuration in `core-site.xml`.

```xml
<!-- etc/hadoop/core-site.xml -->

<configuration>
    <property>
        <name>fs.defaultFS</name>
        <value>hdfs://localhost:9000</value>
    </property>

    <property>
        <name>hadoop.tmp.dir</name>
        <value>$HADOOP_HOME/tmp</value>
    </property>
</configuration>
```

Here, next to letting Hadoop know about the `tmp/` directory, we also - and more importantly - specify the main access the file system. HDFS clients and YARN processes will need this address to talk to the *NameNode*.

By the way, all the many configuration options, together with their default values, can be explored under the `Configuration` section of Hadoop's [documentation](https://hadoop.apache.org/docs/r3.2.1/).


### HDFS
Next, we turn to HDFS and the services that run the distributed filesystem. On HDFS, as on most other filesystems, the file metadata and the actual file contents are stored separately. What's special about HDFS is that the metadata typically is stored on a dedicated machine and managed by a dedicated process, the *NameNode*. The data itself is stored on *DataNodes*. Let's create a place for the Hadoop processes to store their information:

```sh
# create places for hadoop to store information

mkdir $HADOOP_HOME/namenode
mkdir $HADOOP_HOME/datanode
```

Because these paths might change from machine to machine (not actually recommended), we specify them as site-specific configuration in `hdfs-site.xml`:

```xml
<!-- etc/hadoop/hdfs-site.xml -->

<configuration>
    <property>
        <name>dfs.namenode.name.dir</name>
        <value>$HADOOP_HOME/namenode</value>
    </property>

    <property>
        <name>dfs.datanode.data.dir</name>
        <value>$HADOOP_HOME/datanode</value>
    </property>

    <property>
        <name>dfs.replication</name>
        <value>1</value>
    </property>
</configuration>
```

There is another important point to notice here. Since we are setting up Hadoop on a single machine and we'll only have a single *DataNode*, we cannot actually make use of it's replication capabilities (let alone the powerful [erasure coding](https://hadoop.apache.org/docs/r3.2.1/hadoop-project-dist/hadoop-hdfs/HDFSErasureCoding.html), which was added in Hadoop 3). This is why we set the default replication factor to one.

With this configuration, we are ready to start up the HDFS processes. As with other filesystems, HDFS needs to be formatted before we can use it.

```sh
# prepare hdfs filesystem
hdfs namenode -format

# start hdfs processes
hdfs --daemon start namenode
hdfs --daemon start datanode

# check processes are running
jps
```

The `jps` command line tool comes as part of the Java SDK. It lists running Java processes. If everything goes well, you should be able to see `NameNode` and `DataNode` listed as running processes.

Before we move on to YARN, let's run a few commands on HDFS and store some data on it to get a first impression of how the service works. The following listing displays a brief session with HDFS.

```sh
# create a working directory
mkdir ~/hadoop && cd ~/hadoop

# create some fake data
echo -e '1\n1\n2\n3\n5\n8\n13\n21' > sample.txt

# create a directory on hdfs
hdfs dfs -mkdir /data

# transfer our data to hdfs
hdfs dfs -put sample.txt /data/sample.txt

# list the data we have on hdfs
hdfs dfs -ls /
hdfs dfs -ls -R /

# read the file from hdfs
hdfs dfs -cat /data/sample.txt

# get help on different commands
hdfs --help
hdfs dfs --help
```

The example shows how we can treat HDFS has a type of filesystem and how we can interact with it through a command line client. Other clients have been implemented as well, including a HTTP-based REST API via [WebHDFS](https://hadoop.apache.org/docs/r3.2.1/hadoop-project-dist/hadoop-hdfs/WebHDFS.html).

Notice that the *NameNode* exposes a low-level health monitor through a web interface, by default at port 9870. If you haven't changed the infrastructure setup, the interface will be available at:

```sh
# namenode health monitor
http://192.168.60.2:9870
```

We shall come back to HDFS at a later point and explore it's workings in a bit more depth. For now, let's turn our attention to YARN and see how it can run jobs on the distributed filesystem.


### YARN
In version 1 of Hadoop, the MapReduce execution pattern and resource scheduling for the distributed *DataNodes* were at the heart of the framework. With Hadoop 2, they became modules that could be replaced by alternative approaches or implementations. For instance, Hadoop users could now use [Apache Mesos](http://mesos.apache.org/) for resource management. We are not going to explore these options here.

YARN is responsible for keeping track of which compute resources are available throughout the cluster and for scheduling job execution accordingly.

We'll begin its configuration by specifying two important environment variables:

```sh
# append to /etc/profile.d/hadoop.sh

export HADOOP_YARN_HOME=$HADOOP_HOME
export HADOOP_MAPRED_HOME=$HADOOP_HOME
```

Don't forget to `source` or re-enter the terminal after this change.

According to the documentation, we need to whitelist a few environment variables and tell Hadoop to actually use YARN for its MapReduce jobs. The configuration can be copied straight from the docs and added into the respective files in `$HADOOP_HOME/etc/hadoop`:

```xml
<!-- mapred-site.xml -->

<configuration>
    <property>
        <name>mapreduce.framework.name</name>
        <value>yarn</value>
    </property>

    <property>
        <name>mapreduce.application.classpath</name>
        <value>$HADOOP_MAPRED_HOME/share/hadoop/mapreduce/*:$HADOOP_MAPRED_HOME/share/hadoop/mapreduce/lib/*</value>
    </property>
</configuration>
```

For YARN itself, we need to set a shuffle handler explicitely. The shuffle phase is typically the most resource-intensive part of a MapReduce job, and there are different handler implementations. Let's go with the default option.

```xml
<!-- yarn-site.xml -->

<configuration>
    <property>
        <name>yarn.nodemanager.aux-services</name>
        <value>mapreduce_shuffle</value>
    </property>

    <property>
        <name>yarn.nodemanager.env-whitelist</name>
        <value>JAVA_HOME,HADOOP_COMMON_HOME,HADOOP_HDFS_HOME,HADOOP_CONF_DIR,CLASSPATH_PREPEND_DISTCACHE,HADOOP_YARN_HOME,HADOOP_MAPRED_HOME</value>
    </property>
</configuration>
```

And that's it for basic configuration. All that is left is to start up the respective YARN services. In a full cluster setup, we would configure the *ResourceManager* to run on its own machine and start it there with a special account called `yarn`. And we would start a *NodeManager* on each worker node in the cluster. But since we are not concerned with multiple nodes, let alone security here, we can start both processes on the same machine with our sudo account (don't try this in production, kids):

```sh
# start yarn processes
yarn --daemon start resourcemanager
yarn --daemon start nodemanager

# see if they're running
jps
```

As before, `jps` will list all running Java processes. If nothing went wrong, both YARN processes show up. For further inspection, we can also run `yarn node -list -all` to confirm a single healthy node is up and running. And similar to the HDFS *NameNode*, YARN's resource manager exposes a health dashboard through a web interface:

```sh
# resource manager dashboard url
http://192.168.60.2:8088
```

The dashboard does not tell us too many interesting things at this point because we haven't done anything yet. Let's run a little job with YARN to try out if the setup works.

A very straight forward way to work with Hadoop is to have it stream the output of files to STDOUT, from where it can be read and processed with command line tools. The listing below shows another session with Hadoop, assuming the previous state is still present, including a test file on HDFS:

```sh
# go to the project directory
cd ~/hadoop

# check sample.txt is still there
hdfs dfs -ls /data

# prepare for streaming
export HADOOP_STREAMING_JAR=$HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-3.2.1.jar

# run an example job
yarn jar $HADOOP_STREAMING_JAR \
  -mapper 'wc -l' \
  -numReduceTasks 0 \
  -input /data
  -output /job_output

# inspect job output
hdfs dfs -ls /job_output
hdfs dfs -cat /job_output/part-00000
hdfs dfs -text /job_output/*
```

If the job runs as expected, it produces two files in a newly created `job_output` directory. These contain linecounts for different parts of the input file. Adding up these numbers should tell us the total number of lines in the `sample.txt` file. You can also inspect the job now on `http://192.168.60.2:8088`.

Just showing this example will naturally raise more questions than it answers about YARN and MapReduce, but further explanation will have to wait until later. All we wanted to do here was run a very simple job as a kind of smoke test for our setup.

For now, let's clean up after ourselves:

```sh
# remove example data from hdfs
hdfs dfs -rm -r /data
hdfs dfs -rm -r /tmp
hdfs dfs -rm -r /job_output
```


## Summary and Outlook

This concludes setting up the core Hadoop system on a single node. We have seen how we can download the Hadoop binaries, create a few working directories and with a little bit of configuration can execute some example tasks, both on HDFS directly and using YARN.

There are a few different directions we could take it from here. Perhaps it makes most sense to talk about the *MapReduce* execution pattern and see how we can ran some more interesting jobs using our current setup. After that, it may be helpful to dig further into creating a more advanced setup that spans multiple machines.
