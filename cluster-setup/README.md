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

