# Hadoop Cluster Setup

After exploring a [pseudo distributed setup](../pseudo-distributed-setup/) with multiple services running on a single machine, it's time to consider how to install a proper Hadoop cluster spanning multiple actual nodes. We'll continue to do the installation from scratch using Hadoop binaries to get a better understanding of the framework's moving pieces, even though for a production setup it is advisable to use a management service like [Ambari](...) or even a third party provided distribution.

```md
# prerequisites

Virtualbox >= 5.1.28
Vagrant >= 2.2.6
Python >= 3.6
Ansible >= 2.0.2
```

One thing to take note of: while the previous setup was discussed in terms of raw command line execution on a Debian machine, we will use [Ansible](...) for this one. This is because first of all executing the same commands on multiple machines becomes tedious very quickly, and secondly, the Ansible script itself can serve as documentation.

For this discussion, we will use multiple virtual machines that run on our computer. These which will be managed by [Vagrant](...) and use [Virtualbox](...) as backend. If you want to install Hadoop using a different provider, e.g. AWS, you will need to prepare an inventory file like our [local inventory file](./inentories/local) with IP addresses, user information and SSH keys accordingly. Be aware that to run the setup on your computer, you will need *at least* 8Gb ob RAM.


## Quick Start

Since all steps to prepare a simple setup are specified in our Ansible playbooks already, it should be a matter of booting up the VMs and provisioning them using Ansible:

```sh
# start virtual machines
vagrant up

# run the ansible playbook
ansible-playbook provision.yml -i inventories/local
```

This will start five virtual machines, install Hadoop on them, and prepare relevant user accounts. With this in place, you can skip ahead to the [Running Hadoop](...) section below.

In the following, we'll discuss the setup in some detail.


## Preparing Virtual Machines

According to the Hadoops official [cluster installation guide](...), we will want to

- run the HDFS *namenode* process on a dedicated machine
- run the HDFS *secondary namenode* process on a dedicated machine
- run the YARN *resource manager* process on a dedicated machine
- run HDFS *data nodes* and YARN *node managers* side-by-side on each worker node
- provide a machine for services like a WebApp proxy server

We will not worry about the services here, as they can be provided through the YARN resource manager itself. What we will do, however, is set up another machine to act as an edge node. From here, users can access the cluster and execute their jobs.

In total, we will need five machines supporting the following roles:

[img](...)

You can find the machine specifications in the [Vagrantfile](Vagrantfile). Each VM will have 512MB of memory, and will be accessible through a management user called `vagrant`.

Let's take a look at Ansible's [local inventory file](./inventories/local). In here, we create four base groups to which we assign our five virtual machines:

```ini
[namenode]
192.168.50.2

[resource_manager]
192.168.50.5

[workers]
192.168.50.3
192.168.50.4

[edge]
192.168.50.6
```

These IP addresses are for host-only communication in a private network set up by Vagrant. If you'd like to switch to a different VM provider, this is where you'd need to add your custom IP addresses and specify access information. As we are not too concerned about security issues when running a local test environment, we can use the same user and `insecure_private_key` for all our machines as specified in the `[hadoop:vars]` section. But in a different context you may need to specify access information relevant for your context.

At this point, you should have five virtual machines running and Ansible should know how to access them. If you'd like, check this via a ping and by logging into the machine and performing an action only root is allowed to.

```sh
# see if machines are available
ansible hadoop -m ping -i inventories/local

# check if you have access
ansible hadoop -b -m shell -a 'cat /etc/passwd' -i inentories/local
```

With this, our infrastructure is ready for provisioning.


## Installing Hadoop

Ansible's main entry point is [provision.yml](./provision.yml). In here, we see an overview over the tasks to be performed. There is some setup that needs to be done on every machine in our cluster first, and then some role-specific setup.

Looking at [hadoop-base.yml](./playbooks/hadoop-base.yml), the first interesting reference is to [vars.yml](./playbooks/vars.yml). This is the central place for basic installation options. Here, we can specify which Hadoop version we want to use, the download path, where Hadoop is going to live on our machines, and so on.

The `roles` section specifies the different parts required for the actual installation:

```yml
roles:
  - java8
  - cluster-communication
  - account-creation
  - hadoop-download
  - hadoop-config
```

- `java8`: Hadoop 3 requires Java 8 at the time of this writing, in early 2020. But a move to Java 11 is already anounced.
- `cluster-communication`: For convenient communication between machines and because we don't want to have the overhead of talking to a DNS server, we make the IP addresses of each machine known in each nodes `/etc/hosts` file.
- `account-creation`: It is best practice to run HDFS services as user `hdfs`, YARN services as user `yarn`, and everything else from permission-restricted user accounts. For this, we need to set up the accounts we want and distribute their keys across the cluster, so all machines can properly communicate.
- `hadoop-download`: Hadoop binaries are downloaded, the download's Hash is verified, and everything is unpacked as specified in [vars.yml](./playbooks/vars.yml).
- `hadoop-config`: Some environment variables are set and the configuration files are copied over from the [config](./config/) directory. We'll go over parts of this configuration in the next section. Finally, some working directories are created.

This concludes the base setup that is the same for every node in the cluster. With this in place, role-specific setup follows as per [provision.yml](./provision.yml), which mainly consists in creating some specific working directories, and in making the worker-nodes known to the leader processes. Specifying worker nodes in `etc/hadoop/workers` is how Hadoop can decide which nodes will be data nodes and node managers.

So far, Hadoop is downloaded, environments are prepared and working directories are created. It is time to look at the configuration options in a little more detail.


## Hadoop Configuration

All configuration files can be found in the [config](./config/) directory. Hadoop has some default configuration, but this can be overwritten in site-specific, i.e. role-specific, files. Hadoop configuration is designed such that the same set of configuration files can be deployed to every machine and the respective roles will only care about what is relevant for them. Let's take a look at a few details.

In [core-site.xml](./config/core-site.xml) we most importantly specify the address of the filesystem:

```xml
<property>
    <name>fs.defaultFS</name>
    <value>hdfs://master1:9000</value>
</property>
```

This is the main entry point. The address specifies how HDFS clients can talk to the name node.

In [hdfs-site.xml](./config/hdfs-site.xml) we specify which working directories to use for name and data nodes respectively. Two other options are interesting as well, `blocksize` and the default `replication` factor. Notice how both values are taken from our [vars file](./playbooks/vars.yml):

```xml
<property>
    <name>dfs.replication</name>
    <value>{{ hadoop_default_replication_factor }}</value>
</property>

<property>
    <name>dfs.blocksize</name>
    <value>{{ hadoop_blocksize_bytes }}</value>
</property>
```

The `replication` is set to the value two in our context, since we have only spun up two worker nodes.

The `blocksize` determines how large file system blocks will be. By default, this value is 128MB. Hadoop is built to landle *large* files! A larger blocksize means less overhead for `seek` operations and faster reading of consecutive pieces of data from disk. At the same time, a smaller block size makes it easier to evenly spread out files across the whole cluster and will reduce the storage overhead we encounter when storing smaller files. Think about it this way: if our blocksize is 128MB, Hadoop will reserve 128MB of storage even if the file we store is only 1 Byte in size. While the appropriate `blocksize` value will depend on the specific needs of a project, we set it to 1MB here, the smallest value allowed, so that we can easily create files with multiple blocks for our example application.

In [yarn-site.xml](./config/yarn-site.xml) we specify where to find the resource manager and whitelist some environment variables. Furthermore, we specify a few resource boundaries for the node managers according to this [suggestion](...):

```xml
<property>
   <name>yarn.scheduler.capacity.root.support.user-limit-factor</name>
   <value>2</value>
</property>

<property>
   <name>yarn.nodemanager.disk-health-checker.min-healthy-disks</name>
   <value>0.0</value>
</property>

<property>
   <name>yarn.nodemanager.disk-health-checker.max-disk-utilization-per-disk-percentage</name>
   <value>100.0</value>
</property>
```

Without these values, the node managers will not be able to estimate available resources and we will later run into problems when executing yarn jobs.

Finally, we prepare [mapred-site.xml](./config/mapred-site.xml) as suggested in the official setup guide.


## Running Hadoop

Assuming you started from scratch as we did here, you should now have a clean and readily configured minimal cluster installation of Hadoop running. We cannot do much with it yet, however, without first starting the respective daemon processes. Let's take this opportunity to get more familiar with the different nodes and accounts we have created.

### HDFS

As stated above, it is best practice to run HDFS processes as the user `hdfs`. Whoever starts these processes will automatically be considered superuser and have access to all of HDFS, so this account should exclusively be used for management tasks.

To start up HDFS, let's enter the namenode, switch to the `hdfs` user account (the password for every account is `hadoop`) and see if the environment is properly prepared:

```sh
# enter the namenode
vagrant ssh master1

# become hdfs (password: hadoop)
su - hdfs

# check if hadoop is there
hadoop version
hdfs version
```

If environment variables are set correctly, the `hdfs` as well as the `hadoop` command will be recognized. You can further inspect the setup by listing relevant variables (run `hadoop envvars`) and by verifying the current configuration (`hadoop conftest`).

With a clean setup, format the namenode first before starting the filesystem daemons:

```sh
# prepare the namenode
hdfs namenode -format

# start HDFS daemons
start-dfs.sh

# check running Java processes
jps
```

The namenode should run processes `NameNode` and `SecondaryNamenode` at this point. On a worker node, and from within the `hdfs` user account, `DataNode` should be listed on `jps` instead.

Try out a few commands on HDFS:

```sh
# create a directory
hdfs dfs -mkdir /raw

# create some example file
echo valuable information > test.txt

# hand over the file to hdfs
hdfs dfs -put test.txt /raw

# list directory contents
hdfs dfs -ls -R /
```

Hadoop offers functionality to check the setup and monitor system health. Helpful commands include:

```sh
# system setup overview
hdfs dfsadmin -printTopology

# system statistics
hdfs dfsadmin -report
```

A more convenient way to access this and other information is the dashboard which Hadoop exposes through a web interface, and which can by default be found at:

```md
# HDFS web interface at
http://master1:9870
```

Notice that to access the web interface from your local machine, you have to either specify the IP address directly (`http://192.168.50.2:9870`) or add the line `192.168.50.2 master1` to your machine's `/etc/hosts` file.

For a little experimentation, try stopping the datanode process on one of the workers (`hdfs --daemon stop datanode`). The health dashboard will notice that the node is no longer reachable, and after about 10 minutes will declare it dead. At this point, the namenode would schedule replication of the now under-replicated data if possible.

Let's clean up our test data for good measure. We remove the test file locally (`rm test.txt`) as well as from HDFS. The latter can be achieved either from the command line via `hdfs dfs -rm /raw/test.txt` or - why not - through the file explorer avaliable in the web interface. HDFS is ready.


## YARN

The provisioning script sets up YARN as well, Hadoop's default resource scheduling application. YARN has two roles: a *resource manager* that is responsible for overall scheduling and job assignment, and a *node manager* that is responsible for the resources of a single worker node. As the documentation suggests, we run the resource manager on its own machine and start it as the user `yarn`:

```sh
# log into the resource manager's machine
vagrant ssh master2

# assume the yarn role (password: hadoop)
su - yarn

# start the yarn processes
start-yarn.sh

# see if ResourceManager is running
jps
```

We should now be able to see the two worker nodes with `yarn node -list` which will show healthy nodes. If nothing appears here, try `yarn node -list -all`.


- TODO: start history server as mapred


## Running an Example Job

So far, we have seen the `hdfs` account that's responsible for HDFS administrative tasks, and the `yarn` account for YARN related tasks. An actual query should never be run as one of these users, but from a different account. The Ansible playbook creates a user `edge` on one of the machines and we will use this to run an example job.

Before running a job as user `edge`, we need to prepare the filesystem, which we will do using the `hdfs` account:

```sh
# enter the edge node
vagrant ssh edge

# perform administrative tasks as user hdfs
su - hdfs

# assign HDFS content to the hadoop group
hdfs dfs -chgrp -R hadoop /

# create a home directory for edge on HDFS
hdfs dfs -mkdir -p /user/edge

# hand the directory over the the user
hdfs dfs -chown edge /user/edge

# ensure traversal permissions for the hadoop group
hdfs dfs -chmod 775 /
```

At this point, we can create a bit of test data and run a simple streaming job to make sure everything works:

```sh
# execute jobs as edge user
su - edge

# create some fake data on the local filesystem
echo -e 'rock\npaper\nscissors' > lines_local.txt

# create a data directory on HDFS
hdfs dfs -mkdir data

# store the data on HDFS in edge's home directory
hdfs dfs -copyFromLocal lines_local.txt lines.txt

# run a linecount job
yarn jar $HADOOP_STREAMING_JAR \
  -mapper 'wc -l' \
  -numReduceTasks 0 \
  -input . \
  -output results01

# inspect the results
hdfs dfs -ls -R
hdfs dfs -text results01/*
```

If the job ran successfully, two mappers were started that output linecounts for different parts of the input files and stored them in two output files.

Similar to the HDFS health dashboard, the resource manager offers a web interface for tracking (and debugging) YARN jobs. You can reach this at `http://master2:8088/cluster`.

Finally, let's clean up again before we leave. We remove our local testfiles (`rm lines_local.txt`) and the data on HDFS as well:

```sh
# see what's there to clean up
hdfs dfs -ls

# remove test data
hdfs dfs -rm data/*
hdfs dfs -rm -r results01
```


## Summary and Outlook

We have deployed a minimal Hadoop cluster with two worker nodes on a couple of VMs. We have started HDFS daemons (as user `hdfs`) and YARN daemons (as user `yarn`) and we have executed a MapReduce job as a regular user `edge` on a separate edge node.

This setup was not concerned with security of even high availability and there are loads of topics we have not even touched upon, let alone all the many services that make up the Hadoop environment like Spark and Hive and HBase, to name some common ones. But we have seen some of the moving parts of the Hadoop core framework and are hopefully in a better position now to gauge which tasks installation managers like Ambari need perform.

A good next step would be to play around with this setup some more, perhaps use the example application to generate some fake data and understand how it is distributed across the cluster, and how different MapReduce jobs handle it.

Otherwise, it would not be time to see how we can use Ambari to configure a Hadoop cluster and to bring into play some more pieces of software that are considered to be central to a full-fledged Hadoop setup. There would be services like [Zookeeper](...) and [Ranger](...) on an infrastructure level, and [Hive](...), [Spark](...) or the job schedular [Oozie](...) at the application level.
