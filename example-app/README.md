# Example Application
Before we go and explore the different parts of Hadoop, let's consider an example data application, including some test data. This can help us understand the map-reduce execution pattern and review Unix pipelines, without the overhead of having to think about a distributed filesystem, resource schedulers, and the like.


## Tracking Birds
To keep things simple, we'll start with a tiny example application that allows users to record which birds they have seen and where. In the first version, all we care about is which birds have been observed and in which country. We store this data in csv format on our filesystem as

```txt
Stork,LY
Hawk,IL
Goose,LY
Goose,LY
Turkey,EE
Bald eagle,BD
```

As you see, our list is not sorted in any way, and birds and country codes can appear multiple times, and even the same bird-country combination can appear multiple times.


## Command Line Statistics on Test Data
To get started, we'll generate some fake data. A random combination of a bunch of birdnames and country codes should suffice for now. Use the data generator in [birds.py](scripts/birds.py) to create a set of test data:

```sh
# a place to keep our data
mkdir data

# generate 50 fake observation in two files
python scripts/birds.py -n 20 > data/birds1.csv
python scripts/birds.py -n 30 > data/birds2.csv
```

At this point, we have simulated user activity and collected data to multiple files. These files stand for a large dataset that is split into multiple parts and potentially over multiple machines, as will be the case with Hadoop. But for now, it's all on our local filesystem and we can start asking some questions. The Unix command line can become a powerful analysis tool in this context.

```sh
# how many observations do we have in total?
cat data/birds*.csv | wc -l

# how many unique birds are there?
cat data/birds*.csv | sort | cut -d , -f 1 | uniq | wc -l

# what are the top five most observed birds?
cat data/birds*.csv \
  | sort \
  | cut -d , -f 1 \
  | uniq -c \
  | sort -t ' ' -k1,1 -nr \
  | head -n 5
```

Using the command line, we can create powerful streaming pipelines that can help us answer simple questions. However, more elaborate questions, for instance: how many different species are observed in each country on average, would require quite a lot of effort to answer in this way. Moreover, what if our data does not neatly fit onto a single computer? It seems we need to take this a step further and if we want to handle massive amounts of distributed data at some point - enter MapReduce.


## Programming with Mappers and Reducers
In functional programming we have concepts called `map` and `reduce` that are often used in combination. Both operate on collections of data. A *mapping* replaces each item in the collection with the result of passing the item through some function. A *reduction* (or folding, or accumulation) combines all values into a single final value.

As an example, assume we have a list of birds and want to count the total number of characters used in this list. One way to do this would be to loop through all the names and add the respective length to a running total:

```py
""" counting characters using a loop """

birds = ['Stork', 'Dove', 'Sparrow', 'Flamingo']

total = 0
for name in birds:
    total += len(name)
```

This is already an example of a `reduce` operation: we have compressed the list of names into a single number.

In this example, we have counted the number of characters while iterating over the names. A second approach would be to first count the characters of each word, and then, in a second step, sum up all the counts.

```py
""" Counting characters in two steps """

birds = ['Stork', 'Dove', 'Sparrow', 'Flamingo']

# map
word_lengths = [len(name) for name in names]

# reduce
total = sum(word_lengths)
```

We can see how a *map* and *reduce* step work together to achieve the desired result. This seemingly simple pattern can be very powerful. As Jeffrey Dean and Sanjay Ghemawat write in their [seminal paper](https://research.google/pubs/pub62/) accompanying their implementation of *MapReduce* at Google:

> We realized that most of our computations involved applying a *map* operation to every logical "record" in our input in order to compute a set of intermediate key/value pairs, and then applying a *reduce* operation to all the values that shared the same key, in order to combine the derived data appropriately.

In our examples, we have not encountered any key/value pairs because counting characters was such a simple exercise that we got away without them. But already in the previous section, when we were counting birds by species, we needed to add up all the bird in one species, so we were implicitely already using the species as group keys.

The formalization using key/value pairs as well as the application of reducers to intermediate results with identical keys is where Google's MapReduce pattern goes beyond the *mappers* and *reducers* we know from functional programming.

In the next part, we will take a look at the whole framework and try to answer our open question from before that was too complicated for a simple Unix pipeline.


## Analysing Birds with MapReduce
How many different species live in each country on average? That's a more elaborate question now. Let's see how we can answer the question using MapReduce.

First, we probably want to group the birds by country and then in a second step count how many unique species are in each one. We can start by going over all observations and for each one output first the country, then the bird.

To illustrate this, we start with some **raw observation data**:

```txt
Stork,LY
Hawk,IL
Goose,LY
Goose,LY
Bald eagle,BD
```

This is turned into a list of `<key><TAB><value>` pairs with the **country listed first**:

```txt
LY      Stork
IL      Hawk
LY      Goose
LY      Goose
BD      Bald eagle
```

Now let's **sort** this list so that we have consecutive observations for each country:

```txt
BD      Bald eagle
IL      Hawk
LY      Goose
LY      Goose
LY      Stork
```

At this point, we can **count unique birds** per country:

```txt
BD      1
IL      1
LY      2
```

To determine the average, we need to sum up all the numbers and divide by the number of countries. Because there won't be more than 250 countries, this can easily be done on a single computer. However, in a Big Data context, the resulting aggregations may still amount to Terabytes of data sitting on various machines. In a case like this, it might be necessary to go through another round of map and reduce to boil down the data enough to handle the results on one machine.

In our case, however, there is no need to go through the full process again. Instead, we can apply another reducer that computes the mean - or even have the same reducer handle this computation as well. For illustration purposes, let's take the first approach.

The code for the previously described map and reduce steps can be found in [mapper.py](scripts/mapper.py), [reducer-count.py](scripts/reducer-count.py) and [reducer-mean.py](scripts/reducer-mean.py). If permissions on the scripts allow for execution, we can build the pipeline to answer the original question:

```sh
# average species per country
cat data/birds*.csv \
  | scripts/mapper.py \
  | sort \
  | scripts/reducer-count.py \
  | scripts/reducer-mean.py
```

Notice the `sort` operation is necessary for the first reducer the work - it expects all observations for one country to be consecutive. Notice also how we *chained* the second reducer to the first. In many analytics scenarios, more complex questions are answered by building long chaings and even trees of map and reduce steps that build upon one another.

