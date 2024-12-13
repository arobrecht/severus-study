## Build dependencies

* Python 3.10


### Run dependencies

* Python >= 3.10
* flask
* flask-socketio
* flask-wtf
* WTForms
* email_validator
* eventlet
* tornado
* werkzeug
* numpy
* matplotlib
* networkx
* gensim
* pyvis
* nltk
* pandas
* sklearn
* scikit-learn
* numpy~=1.24.3
* matplotlib~=3.7.1
* tqdm
* neo4j
* pomdp-py
* gensim~=4.3.1
* networkx~=3.1
* pyvis~=0.3.2
* nltk~=3.8.1
* pandas~=2.0.3
* scikit-learn~=1.2.2
* embeddings~=0.0.8
* owlready2


SNAPE

## Installation
Python>=3.10 is required.
Package requirements can be installed using the `requirements.txt` file by running:

```
conda create -n "adaptive_explanation" python==3.10
pip install -r requirements.txt
```

Snape uses Neo4j as its database:

1. download and unzip neo4j community
2. optional: rename folder, e.g 'snape_neo4j'
3. navigate to the unziped folder, e.g: .../snape_neo4j'
3. start the database by running:

```
./bin/neo4j start
```

4. open the webinterface (most likeley: loacalhost:7678, starting the db should print this on the terminal) and change the default password to 'severus_study' (password defined in model_update). When opening the webinterface you will first need to give the standard username: neo4j and password: neo4j and then you will be asked to set a new password which should be: severus_study
5. stop the databse after changning the default password:

```
./bin/neo4j stop
```

Additionally when it is desired to run multiple SNAPE instances on the same machine every instance needs its own neo4j installation and database.
In this case you need to adjust the ports used by each installation

1. navigate into neo4j folger, e.g: 'snape_neo4j_instance_XXX'
2. open file /conf/neo4j.conf
3. adjust server port under '#Bolt connector' change server.bolt.listen_address=:YOUR_PORT
4. adjust webinterface port under '# HTTP Connector' change server.http.listen_address=:YOUR_PORT
5. save file
6. ensure that each instance uses unique ports for the server and the webinteface (increment each port by one for each instance)
7. change default password as described above (use correct webinterface port when connecting to the db)
8. repeat steps for each instance

Java 21 is required for neo4j

## Usage

Starting the database:

1. navigate into neo4j folder, e.g: 'snape_neo4j'
2. start the db by running:

```
./bin/neo4j start
```

Stopping the database:

1. navigate into neo4j folger, e.g: 'snape_neo4j'
2. stop the db by running:

```
./bin/neo4j stop
```

The easiest way to manage multiple instances at once, is to open a terminal for each instance and keep it open while the instance is running. When you're done just run the stop command as described above.

The simulation can be started with
```
python study_simulation.py
``
