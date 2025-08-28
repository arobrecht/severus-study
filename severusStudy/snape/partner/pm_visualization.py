from matplotlib import pyplot as plt
from itertools import chain
import matplotlib.colors as mcolors
from py2neo import Graph
from pyvis.network import Network
import networkx as nx
import base64
import numpy as np
import os

def get_color_from_value(value) -> hex:
    """
    Map lou to color gradient from red 0 to green 1

    Args:
        value: lou

    Returns: hex color

    """
    norm = mcolors.Normalize(vmin=0, vmax=1)
    cmap = plt.get_cmap("RdYlGn")  # Red to Green colormap
    return mcolors.to_hex(cmap(norm(value)))  # Convert to hex color code


def get_base64_image(filename) -> base64:
    """
    generate base64 string of file for html embedding

    Args:
        filename: path to file

    Returns: base 64 string

    """

    try:
        with open(filename, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode("utf-8")
        return base64_image
    except FileNotFoundError:
        print(f"Error: The file '{filename}' does not exist.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def create_graph_html(current_block, user_id):
    """
    Generate html graph using pyvis for current block

    Args:
        current_block: block currently under discussion

    """
    # connect to neo4j to retrieve all data
    graph = Graph(os.getenv("NEO4J_URI", "bolt://localhost:7687"), auth=("neo4j", "severus_study"))
    query = f"""
            MATCH (user: USER {{user_id: '{user_id}'}}) 
            MATCH (n)-[r]->(m) WHERE (user)-[:OWNS]->(n)
            RETURN n, r, m
            """
    graph_data = graph.run(query).data()

    # create nx graph
    G = nx.DiGraph()

    # fill nx graph
    seen_nodes = set()
    for record in graph_data:

        # all node data is saved in the relation when loading neo4j data via py2neo
        relation = record["r"]

        # Check if current relation is triple relation or precondition relation
        # CASE: triple relation (entity_1) -> (relation_node) OR (relation_node) -> (entity_2)
        if type(relation.relationships[0]).__name__ == 'TRIPLE_RELATION':

            # check relation direction (entity_1)->(relation_node) OR (relation_node)->(entity_2)
            if str(relation.relationships[0].start_node.labels) == ':QUARTO_ENTITY':
                start_node = relation.relationships[0].start_node
                end_node = relation.relationships[0].end_node
            elif str(relation.relationships[0].start_node.labels) == ':RELATION_NODE':
                start_node = relation.relationships[0].end_node
                end_node = relation.relationships[0].start_node
            else:
                continue

            # only process nodes in the current block
            block = end_node['block']
            if block != current_block:
                continue

            # retrieve relation properties
            relation_name = end_node['relation']
            lou = end_node['lou']
            relation_node_id = end_node['node_id']

            # calculate color using lou
            color = get_color_from_value(lou)

            # only add relation node if not seen before
            if relation_node_id not in seen_nodes:
                G.add_node(relation_node_id, label=relation_name, color=color, lou=lou, block=block, shape='box')
                seen_nodes.add(relation_node_id)

            # add quarto entity node
            name = start_node['name']
            G.add_node(name, label=name, color=color, block=block, shape='circle') # quarto entity

            # check direction of relation for edge direction
            if str(relation.relationships[0].start_node.labels) == ':QUARTO_ENTITY':
                G.add_edge(name,relation_node_id)
            else:
                G.add_edge(relation_node_id, name)


    if len(list(G.nodes)) == 0:
        return

    # iterate over all nodes with circle shape -> quarto entity
    for node_id, attributes in G.nodes(data=True):
        total_lou = 0
        num_related = 0
        # only process entity nodes
        if attributes.get('shape') == 'circle':

            # iterate over all related nodes
            for related_node in chain(G.neighbors(node_id), G.predecessors(node_id)):
                total_lou += G.nodes[related_node].get('lou', 0)
                num_related += 1

            # set color of entity to average color
            if num_related > 0:
                attributes['color'] = get_color_from_value(total_lou / num_related)


    # create pyvis network and set options
    net = Network(notebook=True, height="750px", width="100%", cdn_resources="remote", )
    net.from_nx(G)
    net.set_options("""
        var options = {
            "edges": {
                "arrows": {
                    "to": { "enabled": true, "scaleFactor": 0.5 }
                }
            },
            "physics": {
                "enabled": true
            },
            "layout": {
                "randomSeed": 42
            }
        }
        """)
    # save network as html file
    net.write_html("graph.html")

    # open saved network to append js code
    with open("graph.html", "a") as f:

        #  * js code to check is the source file changed, reload if the file changed
        #  * only works if file is served via http, reload not allowed using 'file://'
        #  * create http server: 'python -m http.server 8000'
        #  * open: http://localhost:8000/visualization.html
        #  * stop server afterward

        #language=javascript
        f.write("""
        <script type="text/javascript">
            let lastModified = null;

            function checkForChanges() {
                fetch(location.href + '?t=' + Date.now(), { cache: 'no-cache' })
                    .then(response => {
                        const newLastModified = response.headers.get('Last-Modified');
        
                        if (lastModified && newLastModified && lastModified !== newLastModified) {
                            location.reload();
                        }
        
                        lastModified = newLastModified;
                    })
                    .catch(err => {
                        console.error('Error fetching file:', err);
                    })
            }
            
            setInterval(checkForChanges, 500);
        </script>
        """)


def create_plots(pm_data, actions_data):
    """
    Generate the history plot of pm observables and bar plot of mcts actions

    Args:
        pm_data: logs of utterance_id, pm parameter, ...
        actions_data: list of actions from mcts

    """

    # <---- pm history plot ---->

    if not pm_data:
        return
    # retrieve pm observables
    utterance_ids = [item["utterance_id"] for item in pm_data]
    cooperativeness = [item["cooperativeness"] for item in pm_data]
    cognitive_load = [item["cognitive_load"] for item in pm_data]
    attentiveness = [item["attentiveness"] for item in pm_data]
    expertise = [item["expertise"] for item in pm_data]

    # plot data
    plt.figure(figsize=(12, 8))
    plt.plot(utterance_ids, cooperativeness, label="Cooperativeness", marker='o')
    plt.plot(utterance_ids, cognitive_load, label="Cognitive Load", marker='s')
    plt.plot(utterance_ids, attentiveness, label="Attentiveness", marker='^')
    plt.plot(utterance_ids, expertise, label="Expertise", marker='d')

    # configure plot
    plt.xlabel("Utterance ID", size=16)
    plt.ylabel("Value", size=16)
    plt.legend(prop={'size': 16}, loc=2)
    plt.grid()
    plt.savefig("pm_history.png", dpi=200, bbox_inches='tight')
    plt.close()



    #  <---- actions bar plot ---->
    # only process if at least one action was chosen
    if not actions_data:
        return

    # retrieve actions and their reward
    actions = actions_data.get("action")
    rewards = actions_data.get("expectedReward")
    action_reward_pairs = list(zip(actions, rewards))

    # sort reward to select top 5 pairs
    sorted_pairs = sorted(action_reward_pairs, key=lambda x: x[1], reverse=True)
    top_pairs = sorted_pairs[:5]

    # create string for triple + move
    top_actions = [f"{a.action_type.name} \n ({a.triple})" for a, _ in top_pairs]
    top_rewards = [r for _, r in top_pairs]

    # Create the horizontal bar plot
    plt.figure(figsize=(12, 8))
    y_positions = np.arange(len(top_actions))
    plt.barh(y_positions, top_rewards, color='skyblue')
    plt.yticks(y_positions, top_actions, size=16)
    plt.xlabel("Expected Reward", size=16)
    plt.gca().invert_yaxis()  # Invert y-axis for descending order
    plt.savefig("top_actions.png", dpi=200, bbox_inches='tight')
    plt.close()


def create_combined_html(block, last_action, last_feedback, utterance):
    """
    Generate combined HTML file of graph and plots.

    Args:
        block: current block under discussion
        last_action: last action chosen by model
        last_feedback: last feedback from partner
        utterance: utterance from model
    """

    # Load graph HTML file
    try:
        with open("graph.html", "r") as f:
            pyvis_html_content = f.read()
    except FileNotFoundError:
        print(f"Error: The file graph.html does not exist.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

    # Parse plots as base64
    history_plot_data = get_base64_image("pm_history.png")
    bar_plot_data = get_base64_image("top_actions.png")

    if not history_plot_data or not bar_plot_data:
        return

    # Format last action and last feedback
    if not last_action:
        last_action = "None"

    if last_feedback:
        last_feedback = f'SUB: {last_feedback["sub"]}, BC: {last_feedback["bc"]}'
    else:
        last_feedback = "None"

    # HTML code to combine everything
    combined_html = f"""
    <html>
    <head>
        <title>SNAPE Visualization</title>
        <meta charset="UTF-8">
        <style>
            .legend-container {{
                display: flex;
                align-items: center;
                gap: 8px;
                margin-top: 15px;
            }}
            .legend-gradient {{
                height: 15px;
                width: 180px;
                background: linear-gradient(to right, #d73027, #f46d43, #fdae61, #fee08b, #d9ef8b, #a6d96a, #1a9850);
                border: 2px solid #ccc;
            }}
            .legend-text {{
                font-size: 20px;
                font-family: Arial, sans-serif;
            }}
        </style>
    </head>
    <body>
        <div class="container-fluid">
            <h1 class="text-center my-4">SNAPE - partner model visualization</h1>
            <div class="row">
                <div class="col-lg-8">
                    <h4 class="text-left">Block: {block}</h4>
                    <h4 class="text-left">Last action: {last_action}</h4>
                    <h4 class="text-left">Last feedback: {last_feedback}</h4>
                    <h4 class="text-left">Utterance: {utterance}</h4>
                    {pyvis_html_content}

                    <!-- Legend: Added minimally without affecting existing layout -->
                    <div class="legend-container">
                        <div class="legend-text">
                            <span style="font-weight: bold;">LEGENDE:</span>
                        </div>
                        <div class="legend-text">
                            <span style="color: #d73027; font-weight: bold;">Entität ist nicht gegrounded (Rot)</span>
                        </div>
                        <div class="legend-gradient"></div>
                        <div class="legend-text">
                            <span style="color: #1a9850; font-weight: bold;">Entität ist gegrounded (Grün)</span>
                        </div>
                    </div>
                </div>
                <div class="col-lg-4">
                    <h3 class="text-left">Partner model plots</h3>
                    <div id="graph1">
                        <h4>Change of DBN observables</h4>
                        <img src="data:image/png;base64,{history_plot_data}" style="width: 100%; height: auto; border: 2px solid lightgray;">
                    </div>
                    <div id="graph2" style="margin-top: 20px;">
                        <h4>Top 5 actions ranked by expected reward</h4>
                        <img src="data:image/png;base64,{bar_plot_data}" style="width: 100%; height: auto; border: 2px solid lightgray;">
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    # Save combined HTML file
    with open("visualization.html", "w", encoding='utf-8') as f:
        f.write(combined_html)


def create_visualization(block, pm_data, actions, last_action, last_feedback, utterance, user_id):
    """
    Create visualization.html containing the graph and plots of pm observables\n
    View visualization:\n
    1. In severus-study: start http server 'python -m http.server 8000'\n
    2. Open: http://localhost:8000/visualization.html

    Args:
        block: current block
        pm_data: logged data from study_simulation
        actions: mcts output
        last_action: action selected by model
        last_feedback: feedback from partner

    """
    if not actions:
        return
    create_plots(pm_data, actions)
    create_graph_html(block, user_id)
    create_combined_html(block, last_action, last_feedback, utterance)
