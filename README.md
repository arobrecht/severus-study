# Adaptive Explanations as Co-Constructed Processes: SNAPE and SNAPE-PM
This code supplements the thesis _Adaptive Explanations as Co-Constructed Processes -- Modeling a Rational Explainer Through the Interaction of Dynamic Partner Models and Non-Stationary Decision Making_. A [video of the agent](https://doi.org/10.17605/OSF.IO/DAQV9) and preregistrations of the studies on the effects of [dynamic decision-making](https://doi.org/10.17605/OSF.IO/EBH27) and [extended partner-modeling](https://doi.org/10.17605/OSF.IO/DAQV9) on adaptive explanations utilizing the code can be found at OSF.


# Setup Instructions

Follow the steps below to set up and run the project:

---

### 1. Clone the Project
```bash
git clone https://github.com/arobrecht/severus-study.git
```

---

### 2. Create a Conda Environment
```bash
conda create --name severus-study python=3.10
```

---

### 3. Activate the Environment
```bash
conda activate severus-study
```

---

### 4. Install Python Requirements
```bash
pip install -r requirements.txt
```

---

### 5. Install Frontend Dependencies
```bash
npm install
```

---

### 6. Build the Frontend
```bash
npm run build
```

---

### 7. Create a Neo4j Docker Container
```bash
docker run --name neo4j-local   -e NEO4J_AUTH=neo4j/severus_study   -p 7474:7474 -p 7687:7687   neo4j:4.4.37
```

---

### 8. Start Neo4j (if stopped)
```bash
docker start neo4j-local
```

---

### 9. Disable NLU in Configuration (If not manually set up)
In `severus-study/config.py`, set:
```python
NLU_LLM = False
```

---

### 10. Start the Study
```bash
python runStudy.py
```

---

### 11. Open in Browser
Navigate to:
```
http://localhost:37000
```
#### Potential Redirection Errors
Browser Cookies for localhost may cause redirection errors. If this occurs, manually delete all cookies for localhost in the settings of your browser.


---
## Using the built-in visualization
Snape can create a live visualization including the partner model and current graph state if enabled in `severus-study/config.py`:
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

## Licensing notes
Emoji images are screenshots from Googles' open Noto Font, not sure how this is handled :)
