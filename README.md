# Adaptive Explanations as Co-Constructed Processes: SNAPE and SNAPE-PM
This code supplements the thesis _Adaptive Explanations as Co-Constructed Processes -- Modeling a Rational Explainer Through the Interaction of Dynamic Partner Models and Non-Stationary Decision Making_. A [video of the agent](https://doi.org/10.17605/OSF.IO/DAQV9) and preregistrations of the studies on the effects of [dynamic decision-making](https://doi.org/10.17605/OSF.IO/EBH27) and [extended partner-modeling](https://doi.org/10.17605/OSF.IO/DAQV9) on adaptive explanations utilizing the code can be found at OSF.

To run this code, the NLU has to be set up manually or disabled in (severus-study) config:

```py
NLU_LLM = False
```

There is a requirements.txt which can be used to install the requirements in your current environment using
pip:
```pip install -r requirements.txt```

### Install frontend dependencies
```npm install```

### Build frontend script
```npm run build```


### Running the server
Run the server by executing
```python runStudy.py```


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

#### Potential Redirection Errors
Cookies in the browser may cause redirection errors. If this occurs, the cookies can be deleted manually in the browser.

---

## Licensing notes
Emoji images are screenshots from Googles' open Noto Font, not sure how this is handled :)
