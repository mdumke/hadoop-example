# Hadoop Cluster Setup

Current setup works with Vagrant (2.2.6) and Virtualbox (5.1.38). To adapt to your environment, change the ansible [inventory](inventory).

```sh
# start virtual machines
vagrant up

# run the ansible playbook
ansible-playbook provision.yml -i inventory
```

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

Hadoop offers a dashboard with a node overview and low-level health statistics through a web-interface:

```md
# HDFS web interface at
http://<master-ip>:9870
```

Try stopping the datanode process on one of the workers (`hdfs --daemon stop datanode`). The health dashboard will notice that the node is no longer reachable, and after a few minutes will declare it dead. At this point, the namenode would schedule replication of the now under-replicated data.

If you need to reset Hadoop, there is a playbook for that as well:

```
# reset HDFS
ansible-playbook playbooks/reset-hadoop.yml -i inventory
```

