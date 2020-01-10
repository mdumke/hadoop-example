# Hadoop Cluster Setup

Current setup works with Vagrant (2.2.6) and Virtualbox (5.1.38). To adapt to your environment, change the ansible [inventory](inventory).

```sh
# start virtual machines
vagrant up

# run the ansible playbook
ansible-playbook provision.yml -i inventory
```

## HDFS

To work with HDFS, enter the masternode as user `hdfs` (with password `hduser`).

```sh
# enter the namenode
vagrant ssh master1

# become hdfs (password: hduser)
su - hdfs

# check hadoop is recognized
hdfs version
```

If environment variables are set correctly, the `hdfs` as well as the `hadoop` command will be recognized. You can further inspect the setup by listing relevant variables (`hadoop envvars`) and by verifying the current configuration (`hadoop conftest`).

With a clean setup, format the namenode first before starting the filesystem daemons:

```sh
# prepare the namenode
hdfs namenode -format

# start HDFS daemons
start-dfs.sh

# check Java processes are running
jps
```

The namenode should run processes `NameNode` and `SecondaryNamenode` at this point. On a worker node, within the `hdfs` user account, `DataNode` should be listed on `jps`.

Try out a few commands on HDFS:

```
# create a directory
hdfs dfs -mkdir /raw

# create some example file
echo valuable information > test.txt

# hand over the file to hdfs
hdfs dfs -put test.txt /raw

# list directory contents
hdfs dfs -ls -R /
```

Hadoop offers functionality to check the setup and monitor system health. Helful commands include

```sh
# system setup overview
hdfs dfsadmin -printTopology

# system statistics
hdfs dfsadmin -report
```

A more convenient way to access this and other information is the dashboard Hadoop exposes through a web-interface, which can by default be found at:

```md
# HDFS web interface at
http://<master-ip>:9870
```

Try stopping the datanode process on one of the workers (`hdfs --daemon stop datanode`). The health dashboard will notice that the node is no longer reachable, and after about 10 minutes will declare it dead. At this point, the namenode would schedule replication of the now under-replicated data if possible.


## YARN

The provisioning script sets up YARN as well, Hadoop's default resource scheduling application. YARN has two roles: a *resource manager* that is responsible for overall scheduling and job assignment, and a *node manager* that is responsible for the resources of a single worker node. As the documentation suggests, we run the resource manager on its own machine and start it as the user `yarn` (which makes `yarn` the superuser while the process runs):

```sh
# log into the resource manager's machine
vagrant ssh master2

# assume the yarn role
su - yarn

# start the yarn processes
start-yarn.sh
```

We should now be able to see the two worker nodes with `yarn node -list` which will show healthy nodes. If nothing appears here, try `yarn node -list -all`.


- TODO: start history server as mapred


## Running an Example Job

So far, we have seen the `hdfs` account that' responsible for HDFS administrative tasks, and the `yarn` account for YARN related tasks. An actual query should never be run as one of these users, but from a different account. The Ansible playbook creates a user `edge` on one of the machines and we will use this to run an example job.

Before running a job as user `edge`, we need to prepare the filesystem:

```sh
# perform administrative tasks as user hdfs
su - hdfs

# assign HDFS content to the hadoop group
hdfs dfs -chgrp -R hadoop /

# create a home directory on HDFS
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

