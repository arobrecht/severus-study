SNAPE

## Installation
Python>=3.10 is required.
Package requirements can be installed using the `requirements.txt` file by running:

```
pip install -r requirements.txt
```


## Snape uses Neo4j as its database:

### Create Neo4j Container
Run the following command to create a new Neo4j container named `neo4j-local`:

```sh
docker run --name neo4j-local \
  -e NEO4J_AUTH=neo4j/severus_study \  # Set Neo4j authentication (username/password)
  -p 7474:7474 -p 7687:7687 \          # Expose Neo4j web UI (7474) and Bolt protocol (7687)
  neo4j:4.4.37                         # Use Neo4j version 4.4.37
```

### Start the Neo4j Container
If the container is already created but stopped, use:

```sh
docker start neo4j-local
```

### Stop the Neo4j Container
To stop the running Neo4j container:

```sh
docker stop neo4j-local
```

### Check Running Containers
To list all currently running containers:

```sh
docker ps
```

### Remove Neo4j Container
To delete the `neo4j-local` container (make sure it's stopped first):

```sh
docker rm neo4j-local
```

---
## Using the built-in visualization
Snape can create a live visualization including the partner model and current graph state if enabled in the (severus-study) config:
```py
VISUALIZATION = True
```
#### Start the HTTP Server
The visualization is generated as an HTML page, this HTML page reloads itself automatically to update the visualization.
This is only possible if it is served via http. Therefore, it is required to start a simple http server.
Open a new terminal, navigate to the severus-study folder then:
```sh
python -m http.server 8000 # if your system already uses port 8000 change this to an unused port
```
#### View the visualization in your browser:
```url
http://localhost:8000/visualization.html
```


---


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