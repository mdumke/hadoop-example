# Hadoop Cluster Setup

Current setup works with Vagrant (2.2.6) and Virtualbox (5.1.38). To adapt to your environment, change the ansible [inventory](inventory).

```sh
# start virtual machines
vagrant up

# run the ansible playbook
ansible-playbook provision.yml -i inventory
```

To work with Hadoop, enter the masternode as user `hdfs` (with password `hduser`). Here, you need to format the namenode and start the filesystem daemons:

```sh
# enter the namenode
vagrant ssh master1

# become hdfs (password: hduser)
su - hdfs

# check hadoop is recognized
hdfs version

# prepare the namenode
hdfs namenode -format

# start HDFS daemons
start-dfs.sh

# check Java processes are running
jps
```

The namenode should run processes `NameNode` and `SecondaryNamenode` at this point. On a worker node, within the `hdfs` user account, `DataNode` should be listed on `jps`. Try out a few commands on HDFS:

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

If you need to reset Hadoop, there is a playbook for that as well:

```
# stop daemons on the namenode
stop-dfs.sh

# on your local machine, run the playbook
ansible-playbook playbooks/reset-hadoop.yml -i inventory
```


