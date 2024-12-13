SNAPE

## Installation
Python>=3.10 is required.
Package requirements can be installed using the `requirements.txt` file by running:

```
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

4. open the webinterface (most likeley: loacalhost:7678, starting the db should print this on the terminal) and change the default password to 'severus_study' (password defined in model_update)
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

CLI arguments as printed by running `python main.py --help`:

```
usage: main.py [-h] [--use_gui | --no-use_gui] [--partner PARTNER] [--runs RUNS] [--show_debug | --no-show_debug] [--baseline | --no-baseline]
               [--partner_update | --no-partner_update]

This programm explains the game "Quarto!".

options:
  -h, --help            show this help message and exit
  --use_gui, --no-use_gui
                        Interact with the SNAPE model via a simple GUI. (default: False)
  --partner PARTNER     The initial partner model to use. (default: None)
  --runs RUNS           Number of runs for evaluation without gui. (default: 1)
  --show_debug, --no-show_debug
                        Show current model state in the gui. (default: False)
  --baseline, --no-baseline
                        Only provide triples. (default: False)
  --partner_update, --no-partner_update
                        Do not update partner model, disable feedback. (default: True)
```