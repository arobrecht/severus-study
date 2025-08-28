# This config.py has all values needed for the snape module

#Config for explanation process
USE_POP = False
POP_ORDER = [['Spiel'],
             ['Spielbrett', 'Spielfiguren'],
             ['Spieler', 'Spielzüge','Spielziel'],
             ['Ende', 'Strategien']]

#Config for db
NEO4J = True
NEO4J_HOST = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "severus_study"

# Config for Partner Model
CARRY_OVER = 10
DBN_MAX_SIZE = 20

# Configs for MCTS
TIME_LIMIT = 3000
SEARCH_LIMIT = 3000
EXPLORATION_CONSTANT = 1
MCTS_TRIPLE_NUM = 5             # max number of actions calculated by mcts -> for visualization
MAX_COMBINED_ACTIONS = 3        # number of actions that can be combined
COMBINABLE_MOVES = [1, 3, 4, 7]    # moves which are allowed to be combined -> /decision_making/triple_action.ActionType

# Configs for conditioned explanation
# required LOU of a node to be considered as grounded
TERMINAL_THRESHOLD = 0.65
# minimum initial lou
INIT_LOU = 0.0
# maximum LOU for actions (except PROVIDE) to be selected for search in mcts
POSSIBLE_ACTION_THRESHOLD = 0.7
# adjustent of lou for feedback
LOU_FEEDBACK_ADJUSTMENT = 0.35
