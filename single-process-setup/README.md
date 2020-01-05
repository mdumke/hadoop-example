# Hadoop Single Process Setup

From the [official guide](https://hadoop.apache.org/docs/stable/hadoop-project-dist/hadoop-common/SingleCluster.html) we learn that Hadoop can run in a single Java process. We'll recreate this simple setup to get a first impression of how Hadoop operates.

## Preparing a Virtual Machine
For good measure, let's start from scratch using a fresh installation of Ubuntu 18.04 on a virtual machine. I'll use Vagrant 2.2.6 with VirtualBox 5.1.38 to create a local setup. The [Vagrantfile](./Vagrantfile) specifies an environment with 2GB of RAM, and it can be started with

```sh
# start the vm
vagrant up

# and access it
vagrant ssh
```

## Installing Hadoop via Ansible
If you'd like to get started quickly, run the ansible playbook to provision the VM. You may need to adapt the `inventory.cfg` and the `sudo_account` and `vars.yml` if you're not using Vagrant, but this should suffice to run:

```sh
# provision the vm
ansible-playbook playbook.yml -i inventory.cfg
```

## Installing Hadoop Manually
In the following, I'll go over the relevant steps to download and install Hadoop manually, before capturing everything in a few Ansible tasks.

First and foremost, we need Java installed. Hadoop 3 depends on Java 8 (a Java 11 version is in the making), so let's get that:

```sh
# update apt cache
sudo apt update

# install the openjdk implementation of Java 8
sudo apt install opendjdk-8-jdk
```

Next, we download the Hadoop binaries from the [recommended mirror](https://www.apache.org/dyn/closer.cgi/hadoop/common/hadoop-3.2.1/hadoop-3.2.1.tar.gz) and unpack it into `/usr/local/hadoop`:

```sh
# download hadoop binaries
cd /tmp
sudo wget http://ftp.halifax.rwth-aachen.de/apache/hadoop/common/hadoop-3.2.1/hadoop-3.2.1.tar.gz

# ensure checksum matches official sum (d627..34ee)
sha512sum hadoop-3.2.1.tar.gz

# unpack
tar xzf hadoop-3.2.1.tar.gz

# move to destination directory
sudo mv hadoop.3.2.1 /usr/local/hadoop
```

Before we can run any job, Hadoop needs to know where to find Java, so we need to set the `JAVA_HOME` environment variable. To ensure reusability, add the following line to `.bashrc`:

```sh
# in $HOME/.bashrc

export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
```

And while we're at it, let's also update the `PATH` variable so we can access the Hadoop executables more conveniently:

```sh
# in $HOME/.bashrc

export HADOOP_HOME=/usr/local/hadoop
export PATH=$PATH:$HADOOP_HOME/bin
```

Be sure to `source ~/.bashrc` to set the variables.

At this point, we should be able to talk to Hadoop through the first simple command:

```sh
# See if Hadoop is present
hadoop version
```

Because we want to use Hadoop's streaming functionality in a moment, it is conventient to make the streaming jar accessible through an environment variable as well.

```sh
# locate the streaming jar
find $HADOOP_HOME - name *streaming-3.2.1.jar

# consider adding this to your .bashrc
export HADOOP_STREAMING_JAR=\
  $HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-3.2.1.jar
```

## Running an Example Job
Perhaps the simplest way to run a task on Hadoop is through it's streaming jar. Normally, we would have to write mappers and reducers that compile to run on the JVM (typically using Java, Scala or Kotlin). These jobs would accept input data from Hadoop and produce output data in a standardized format. With streaming, this process can be simplified: our mappers and reducers simply read from *STDIN* and write to *STDOUT*. Without going too much into the details of MapReduce at this point, let's see how this works on an example.

We start with a little bit of data preparation:

```sh
# create two files with example data
cd ~
mkdir data
echo -e 'line 1\nline 2' > data/file1.txt
echo -e 'line 1\nline 2\nline 3' > data/file2.txt
```

Now we are ready to run a line count job using the streaming jar directly:

```sh
# map-reduce job using streaming
hadoop jar $HADOOP_STREAMING_JAR \
  -mapper 'wc -l' \
  -numReduceTasks 0 \
  -input data \
  -output example1
```

By default, Hadoop's loglevel is `INFO`, so we get a lot of statistics and metainformation on the job via STDERR, which Hadoop uses for external communication.

What is happening is this: Hadoop is reading the contents of all files in `data/`, concatenates them and streams them to STDOUT. From here, the mapper can read and process it. The `wc -l` utility tool outputs the number of lines in each file to STDOUT. The results get stored in the output directory, `example1`. In here, we find an empty file named `_SUCCESS`, indicating the job has finished successfully, and two files with partial results. If we inspect them, we find that they contain the line-counts for both input files:

```sh
# inspect job output results: our line-counts

cat example1/part-00000
cat example1/part-00001
```

Of course, we could have counted all lines with a simple unix pipeline such as:

```sh
# linecount as unix pipeline
cat data/file* | wc -l
```

This is way faster and more convenient than what Hadoop was doing, but with this approach we are limited to a single machine and a standard file system. This basic setup does not use HDFS, Hadoop's distributed file system, and it does not execute on multiple machines. A more advanced usage would also not call `hadoop` directly, but would use `yarn`, which can distribute jobs across multiple processes and machines in a cluster.

The single-process installation is helpful for exploring some of Hadoop's capabilities, getting familiar with the project's different parts, and can even help with debugging, since we don't have to worry about distributed execution, data replication, and many other aspects that make the process more complicated.

In the next steps we will explore HDFS and YARN. For this, we'll start by setting up Hadoop in *Pseudo-Distributed Mode*.
