# Hadoop Experiments

## HDFS, YARN, and MapReduce

We begin with a single-node installation of Hadoop 3 on a virtual machine, to get a feeling for what may be involved when undertaking such a project. In broad steps, this is following the [official guide](https://hadoop.apache.org/docs/stable/hadoop-project-dist/hadoop-common/SingleCluster.html).


### Setting up a VM

For this part, use an Ubuntu 18.04 image. Before starting the VM, make sure to update `Vagrantfile` to forward ports `9870` (for the HDFS health check), `9864` (for the data node inspector) and `8088` (for the resource manager interface).

```sh
# use an ubuntu 18.04 image
vagrant init ubuntu/bionic64
```

```ruby
# update Vagrantfile

Vagrant.configure("2") do |config|
  # ...
  config.vm.network "forwarded_port", guest: 9864, host: 9864
  config.vm.network "forwarded_port", guest: 9870, host: 9870
  config.vm.network "forwarded_port", guest: 8088, host: 8088
  # ...
end
```

```sh
# start the machine
vagrant up
vagrant ssh
```


### Get Hadoop

Hadoop 3 requires Java 8. At the time of this writing (November 2019), the documentation states that Java 11 support is being prepared. But let's install Java 8 for now, and in its open source version (be sure to do this as the system's default sudo user):


```sh
# Update apt sources
sudo apt update

# Hadoop 3.x supports Java 8
sudo apt-get install openjdk-8-jdk

# symlink for less typing
cd /usr/lib/jvm
sudo ln -s java-8-openjdk-amd64 jdk

# check installation
java -version
```

[Do we actually need the full jdk on the executing machine?]


With Java in place, we can dowload Hadoop. The official [download options](http://www.apache.org/dyn/closer.cgi/hadoop/common/) have a path to `hadoop-3.2.1.tar.gz`, which we download into the `/usr/local` directory.


```sh
# download hadoop
cd /usr/local
sudo wget http://apache.lauf-forum.at/hadoop/common/hadoop-3.2.1/hadoop-3.2.1.tar.gz

# extract the compiled program
sudo tar xzf hadoop-3.2.1.tar.gz
sudo mv hadoop-3.2.1 hadoop
```

### Create a Dedicated User and Group

For more fine-grained security control, only users with access restrictions will be allowed to operate Hadoop. The first of these users will be `hduser` in the group `hadoop`, both of which need to be created (for simplicity, we use `hduser` as password as well):

```
# inside the VM, create a hadoop group with a user
sudo addgroup hadoop
sudo adduser --ingroup hadoop hduser
```

Now we can make the Hadoop executables available to the hadoop group and the first user.

```
# hand it over to the hduser and hadoop group
sudo chown -R hduser:hadoop hadoop
```

### Preparing the Environment

Hadoop is in place, but it needs a bit of configuration to run. First of all, it will be convenient to have a shortcut to execute hadoop binaries and scripts, which we can do by updating the path variable in hduser's `~/.bashrc`.

```sh
# in /home/hduser/.bashrc

# Hadoop
export HADOOP_HOME=/usr/local/hadoop
export PATH=$PATH:$HADOOP_HOME/bin
export PATH=$PATH:$HADOOP_HOME/sbin
```

We also need to let Hadoop know where Java is. We do this in `/usr/local/hadoop/etc/hadoop/hadoop-env.sh:54`, by setting the path where Java was installed:

```sh
export JAVA_HOME=/usr/lib/jvm/jdk/
```

These preparations are enough to execute as a very first command:

```sh
hadoop version
```

If this is not working, now is a good time to stop and see if everything has been downloaded correctly, environment variables are up to date, and the right user has been created.


### Configuring Hadoop

Hadoop needs at least a place to store data for the namenode and datanode operations, as well as temporary data. Since the first step is to set up a single node, this can be done directly in the `$HADOOP_HOME` directory, which also avoids permission issues (be sure to execute the following listing as sudo-user).

```sh
# create directories
cd $HADOOP_HOME
sudo mkdir namenode datanode tmp

# set permissions
sudo chown hduser:hadoop namenode datanode tmp
```

The next thing to do is to let Hadoop know about these directories, which is done using a number of XML-configuration files. First up is `etc/hadoop/core-site.xml`, where we specify the entry point to the filesystem and let Hadoop know about the temporary storage:

```xml
<!-- in etc/hadoop/core-site.xml -->

<configuration>
    <property>
        <name>fs.defaultFS</name>
        <value>hdfs://localhost:9000</value>
    </property>

    <property>
        <name>hadoop.tmp.dir</name>
        <value>/usr/local/hadoop/tmp</value>
    </property>
</configuration>
```

The namenode and datanode locations are specified in `hdfs-site.xml`, along with the default replication level, which is one in the first step, as there is only a single node.

```xml
<!-- in etc/hadoop/hdfs-site.xml -->

<configuration>
    <property>
        <name>dfs.replication</name>
        <value>1</value>
    </property>

    <property>
        <name>dfs.namenode.name.dir</name>
        <value>file:/usr/local/hadoop/namenode</value>
    </property>

    <property>
        <name>dfs.datanode.data.dir</name>
        <value>file:/usr/local/hadoop/datanode</value>
    </property>
</configuration>
```

### Running HDFS

This is the minimal configuration to get HDFS up and running. However, before we can actually start the services, we need to enable the hduser to interact with the machines that run the services. In particular, the Hadoop services will typically run on different machines and listen on various urls. To start or stop a service, the user will need access to these machines. In the context of the single-node setup, it's the same machine, but the user will still need to be able to log onto that machine. In other words, we need to be able to execute `ssh localhost` as hduser, so we need to create an ssh key for the `hduser` and add it to their `.ssh/authorized_keys`:

```sh
# creating a key for hduser
su - hduser
ssh-keygen -t rsa -P ''

# registering the key
cat $HOME/.ssh/id_rsa.pub >> $HOME/.ssh/authorized_keys
```

At this point, execute `ssh localhost` once, manually, to add the current machine to the `known_hosts` file. Now everything is prepared for the Hadoop installation.

To start the HDFS services, some environment variables need to be set, so we add the following to `.bashrc`:

```sh
# append to /home/hduser/.bashrc

export HADOOP_COMMON_HOME=$HADOOP_HOME
export HADOOP_HDFS_HOME=$HADOOP_HOME
```

As hduser, we should now be able to execute a run script, that comes with Hadoop, and which starts the HDFS services:

```sh
# start HDFS related services
start-dfs.sh
```

This script may fail because of permission problems. There might be a problem because the program to execute commands on multiple remote shells in parallel is either not installed, or it is configured by default to use `rsh`, which has some limitations compared to `ssh`. To fix these issues, update `.bashrc` to change the default remote shell:

```sh
# as sudo user, make sure pdsh is present
sudo apt install pdsh

# update hduser's ~/.bashrc
export PDSH_RCMD_TYPE=ssh
```

Now the `start-dfs.sh` command should work. Because the namenode is not prepared, however, the namenode process will not be properly executed. Listing Java processes via `jps` will not list the namenode. To fix this, run:

```
# prepare the filesystem
hdfs namenode -format
```

Finally, when we run `start-dfs.sh` again, all processes start up. When the services run, we will be able to execute operations on HDFS such as:

```sh
# create a data directory and add some content
hdfs dfs -mkdir -p /raw/xml
hdfs dfs -put $HADOOP_HOME/etc/hadoop/*.xml /raw/xml

# inspect successful ingestion
hdfs dfs -ls -R /
hdfs dfs -cat /raw/xml/core-site.xml

# create a home directory
hdfs dfs -mkdir -p /user/hduser
hdfs dfs -ls
```

Hadoop exposes a health dashbord for HDFS at `http://localhost:9870`. To take a first look under the hood of HDFS, inspect the output of `tree $HADOOP_HOME/datanode` to see how different blocks are stored by Hadoop.


### Starting YARN Processes

YARN and MapReduce rely on two additional environment variables, which can be set in hduser's `.bashrc`:

```sh
# append to /home/hduser/.bashrc

export HADOOP_YARN_HOME=$HADOOP_HOME
export HADOOP_MAPRED_HOME=$HADOOP_HOME
```

Additionaly, we tell Hadoop that YARN will be responsible for managing MapReduce jobs and tell it where to find supporting software executing the jobs.

```xml
<!-- in etc/hadoop/mapred-site.xml -->

<configuration>
  <property>
    <name>mapreduce.framework.name</name>
    <value>yarn</value>
  </property>
  <property>
    <name>mapreduce.application.classpath</name>
    <value>
      $HADOOP_MAPRED_HOME/share/hadoop/mapreduce/*:$HADOOP_MAPRED_HOME/share/hadoop/mapreduce/lib/*
    </value>
  </property>
</configuration>
```

Finally, YARN itself takes a few configuration options. In particular, specifying the traditional shuffle handler will ensure data is distributed as it was in Hadoop version 1. At the same time, we need to whitelist some environment variables to be accessible by Hadoop:

```xml
<!-- in etc/hadoop/yarn-site.xml -->

<configuration>
  <property>
    <name>yarn.nodemanager.aux-services</name>
    <value>mapreduce_shuffle</value>
  </property>

  <property>
    <name>yarn.nodemanager.aux-services.mapreduce.shuffle.class</name>
    <value>org.apache.hadoop.mapred.ShuffleHandler</value>
  </property>

  <property>
    <name>yarn.nodemanager.env-whitelist</name>
    <value>
      JAVA_HOME,HADOOP_COMMON_HOME,HADOOP_HDFS_HOME,HADOOP_CONF_DIR,CLASSPATH_PREPEND_DISTCACHE,HADOOP_YARN_HOME,HADOOP_MAPRED_HOME
    </value>
  </property>
</configuration>
```

With these configurations in place, start YARN services via a script:

```sh
# starting YARN
start-yarn.sh
```

The resource manager will also expose a health dashboard via a webinterface, which by default is `http://localhost:8088`.


### Running a MapReduce Job

To process data on HDFS using MapReduce, we first need to make sure the datanode is not in safemode, which is the default state during startup.

```sh
# check safemode state
hdfs dfsadmin -safemode get

# switch off safemode
hdfs dfsadmin -safemode leave
```

This should enough to run a first job. Inside $HADOOP_HOME, we find the streaming jar to use for a streaming job and then execute a word-count job on the xml data we copied earlier:

```sh
# prepare the streaming job
HADOOP_STREAMING_JAR="$(find $HADOOP_HOME -name *streaming-3.2.1.jar)"

# run an example job
yarn jar $HADOOP_STREAMING_JAR \
  -mapper 'wc -l' \
  -numReduceTasks 0 \
  -input /raw/xml \
  -output word_count_01

# expect the output
hdfs dfs -text word_count_01/*
```

Make sure python is installed (in my Ubuntu image, I needed to symlink python3 to python). We can now use Python to write a mapper in, say, `mapper.py`:

```python
#!/usr/bin/env python

# read lines from stdin
import sys
lines = sys.stdin.read().strip().split('\n')

# parse lines and print key-value pairs
for line in lines:
    print(f'{line[10:14]}\t{line[14:]}')
```

Provide a reducer in `reducer.py`:

```python
#!/usr/bin/env python

import sys
data = sys.stdin.read().strip('\n').split('\n')

def mean(values):
    return sum(values) / len(values)

grades = {}

# collect all grades for a year
for line in data:
    year, grade = [int(n) for n in line.split('\t')]

    if not grades.get(year):
        grades[year] = []

    grades[year].append(grade)

# print the mean for each year
for year, values in grades.items():
    print(year, sum(values) / len(values))
```

When running the script, make sure the files are broadcast to all nodes by passing them in the `files` argument (-> data locality). This makes sure the code can run on all nodes:

```sh
yarn jar $HADOOP_STREAMING_JAR \
  -files mapper.py,reducer.py \
  -mapper mapper.py \
  -reducer reducer.py \
  -numReduceTasks 3 \
  -input /raw/xml \
  -output word_count_02
```

We can also operate on the local filesystem, independent of HDFS (notice, however, that HDFS services need to be running):

```sh
yarn jar $HADOOP_STREAMING_JAR \
  -files mapper.py,reducer.py \
  -mapper mapper.py \
  -reducer reducer.py \
  -numReduceTasks 2 \
  -input file:/home/hduser/data/input.txt \
  -output file:/home/hduesr/mr_jobs/output_01
```





### Preparing Scala

```sh
# prerequisite: Java 8
sudo apt-get install scala

# see if it runs
scala -version
```

Try out scala by creating a simple script:

```scala
// Mapper.scala

object Mapper extends App {
  println("mapping...")
}
```

Now we can compile the script, which will produce additional files, then execute the program:

```sh
# compile
scalac Mapper.scala

# run
scala Mapper
```


