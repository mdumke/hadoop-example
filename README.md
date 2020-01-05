# Hadoop Experiments

Let's get familiar with Hadoop and parts of its ecosystem. Before diving into the hardware setup, you might want to get a basic understanding of *MapReduce*, Hadoop's central execution pattern. Here it is introduced in the context of an example application that will be used later on:

[Example Application](example-app/)

We'll start the process of building the hardware setup simple, by running Hadoop in a single Java process using data on our system's regular old file system in a

[Single Process Setup](single-process-setup/)

A more advanced setup brings more parts of Hadoop into play, each running in a dedicated process, but still on just one machine. This is the

[Pseudo-Distributed Setup](single-node-setup-bkp)
