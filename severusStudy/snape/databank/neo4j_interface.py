import logging

from neo4j import GraphDatabase
import pandas as pd
from severusStudy.snape.databank import parse_ontology
from severusStudy.snape.onotology_management.ontology_management import OntologyManagement
from severusStudy.snape.content.conditioned_node import ConditionedNode


def _format_string(input_str):
    # Remove outer parentheses
    stripped_str = input_str.strip('()')

    # Split by '),(' and '), ('
    tuples = [t.strip() for t in stripped_str.replace('), (', '),(').split('),(')]

    formatted_list = []
    for t in tuples:
        # Split each tuple by commas and strip any surrounding whitespace and parentheses
        elements = [elem.strip().strip('()') for elem in t.split(',')]
        # Append only the first and last element of the tuple
        formatted_list.append([elements[0], elements[1], elements[2]])

    return formatted_list


class Neo4jInterface(OntologyManagement):

    def __init__(self, uri: str, login: str, password: str):
        """
        Initialize the Neo4jInterface and db

        Args:
            uri: URI of the Neo4j database
            login: Login username
            password: Login password
        """
        logging.getLogger("neo4j").setLevel(logging.ERROR)
        self.uri = uri
        self.login = login
        self.password = password
        self.driver = None
        self.connect()
        _initialize_db(self.driver)

    def connect(self):
        """
        Connect the interface to the database
        """
        print('Connecting to Neo4j...')
        self.driver = GraphDatabase.driver(self.uri, auth=(self.login, self.password))

    def close(self):
        """
        Close the connection to the database.
        """
        if self.driver:
            print('Closing connection to Neo4j...')
            self.driver.close()

    def set_lou(self, node_id: int, lou: float) -> bool:
        """
        Set the lou of a triple by setting the lou of its relation_node

        Args:
            node_id: id of the triple
            lou: desired lou of the triple.

        Returns:
            True if the lou was successfully set, False otherwise.
        """

        with self.driver.session() as session:
            result = session.execute_write(_set_lou, node_id, lou)
        return result

    def get_node(self, node_id) -> ConditionedNode:
        """
        Get a conditioned node from the db using the node_id

        Args:
            node_id: id of the node

        Returns:
            conditioned_node object of the node including all values, None if the node does not exist.
        """
        with self.driver.session() as session:
            result = session.execute_write(_get_triple, node_id)
        return result

    def get_block_nodes(self, block: str) -> dict[str, ConditionedNode]:
        """
        Get all nodes in a block of the ontology

        Args:
            block: name as string

        Returns:
            dictionary containing all conditioned_node of the block(key = node_id)
        """
        triple_dict = {}
        with self.driver.session() as session:
            result = session.execute_write(_get_triple_block_id, block)
            if result is None:
                return None
            for node_id in result:
                t = session.execute_read(_get_triple, node_id)
                if t is None:
                    continue
                triple_dict[t.id] = t

        return triple_dict

    def match_triple(self, triple: str) -> tuple[dict[str, ConditionedNode], int]:
        """
        Tries to match a given triple to a triple in the database;
        q_type explanation:\n
        0 = triple not found in database\n
        1 = triple matches found but with question mark\n
        2 = correct match for full triple found\n
        3 = triple found in database with distance = 1\n

        Args:
            triple: The triple to match, in the format: 'entity_1 relation entity_2'

        Returns:
            Dict of matching triples(key = node_id) and q_type

        """

        matches_dict = {}
        decr_lou_amount = 0.2
        with self.driver.session() as session:
            matches, q_type = session.execute_write(_match_triple, triple)
            for res in matches:
                triple = session.execute_read(_get_triple, res)
                if triple is None:
                    continue
                session.execute_write(_decr_lou, triple.id, decr_lou_amount)

                triple = session.execute_read(_get_triple, res)
                matches_dict[triple.id] = triple
        return matches_dict, q_type

    def set_node_was_seen(self, node_id) -> bool:
        """
        Set the was_seen attribute of a node to true

        Args:
            node_id: id of the node

        Returns:
            True if the was_seen attribute was set, False otherwise.

        """
        with self.driver.session() as session:
            result = session.execute_write(_set_node_seen, node_id)
        return result

    def set_node_not_seen(self, node_id) -> bool:
        """
        Set the was_seen attribute of a node to false

        Args:
            node_id:

        Returns:
            True if the was_seen attribute was set to false, False otherwise.

        """
        with self.driver.session() as session:
            result = session.execute_write(_set_node_not_seen, node_id)
        return result


#      <----------- NEO4J QUERIES BELOW ----------->

def _match_triple(tx, triple):
    entity_1, relation, entity_2 = triple.split(' ')

    if entity_1 != '?' and entity_2 != '?' and relation != '?':

        q_type = 2

        query = f"""
                MATCH (node_entity_1:QUARTO_ENTITY) 
                MATCH (node_entity_2:QUARTO_ENTITY)

                MATCH (node_entity_1) -[:TRIPLE_RELATION]-> (relation_node:RELATION_NODE)
                MATCH (relation_node:RELATION_NODE) -[:TRIPLE_RELATION]-> (node_entity_2)

                WHERE node_entity_1.name = '{entity_1}' 
                AND node_entity_2.name = '{entity_2}' 
                AND relation_node.relation = '{relation}'

                RETURN relation_node.node_id AS node_id
                """
    else:

        q_type = 1

        query = f"""
                MATCH (node_entity_1:QUARTO_ENTITY) 
                MATCH (node_entity_2:QUARTO_ENTITY)

                MATCH (node_entity_1) -[:TRIPLE_RELATION]-> (relation_node:RELATION_NODE)
                MATCH (relation_node:RELATION_NODE) -[:TRIPLE_RELATION]-> (node_entity_2)

                WHERE (node_entity_1.name = '{entity_1}' AND relation_node.relation = '{relation}') 
                OR (node_entity_2.name = '{entity_2}' AND relation_node.relation = '{relation}')
                OR (node_entity_1.name = '{entity_1}' AND node_entity_2.name = '{entity_2}')
                RETURN relation_node.node_id AS node_id
                """
    result = tx.run(query)

    if result.peek() is None:

        q_type = 3

        query = f"""
                MATCH (node_entity_1:QUARTO_ENTITY) 
                MATCH (node_entity_2:QUARTO_ENTITY)

                MATCH (node_entity_1) -[:TRIPLE_RELATION]-> (relation_node:RELATION_NODE)
                MATCH (relation_node:RELATION_NODE) -[:TRIPLE_RELATION]-> (node_entity_2)
 
                WHERE (node_entity_1.name = '{entity_1}' AND relation_node.relation = '{relation}')
                OR (node_entity_2.name = '{entity_2}'  AND relation_node.relation = '{relation}')
                OR (node_entity_1.name = '{entity_1}' AND node_entity_2.name = '{entity_2}')

                RETURN relation_node.node_id AS node_id
                """
        result = tx.run(query)

    if result.peek() is None:
        q_type = 0

    matches = []
    for res in result:
        matches.append(res.get('node_id'))

    return matches, q_type


def _set_lou(tx, node_id, lou):

    query = f"""
            MATCH (relation_node:RELATION_NODE) WHERE relation_node.node_id = {node_id}
            SET relation_node.lou = {lou}
            RETURN relation_node
            """

    result = tx.run(query)
    record = result.single()

    if record:
        return True
    else:
        return False


def _set_node_seen(tx, node_id):

    query = f"""
            MATCH (relation_node:RELATION_NODE) WHERE relation_node.node_id = {node_id}
            SET relation_node.was_seen = true
            RETURN relation_node
            """

    result = tx.run(query)
    record = result.single()

    if record:
        return True
    else:
        return False


def _set_node_not_seen(tx, node_id):

    query = f"""
            MATCH (relation_node:RELATION_NODE) WHERE relation_node.node_id = {node_id}
            SET relation_node.was_seen = false
            RETURN relation_node
            """

    result = tx.run(query)
    record = result.single()

    if record:
        return True
    else:
        return False


def _decr_lou(tx, node_id, decr_amount):

    query = f"""
            MATCH (relation_node:RELATION_NODE) WHERE relation_node.node_id = {node_id} 
            SET relation_node.lou = relation_node.lou - {decr_amount}
            RETURN relation_node
            """

    result = tx.run(query)
    record = result.single()

    if record:
        return True
    else:
        return False


def _get_triple(tx, node_id):

    query = f"""
            MATCH (relation_node:RELATION_NODE) WHERE relation_node.node_id = {node_id}

            MATCH (node_entity_precondition_1) -[:TRIPLE_RELATION]-> (relation_node_precondition:RELATION_NODE)
            MATCH (relation_node_precondition:RELATION_NODE) -[:TRIPLE_RELATION]-> (node_entity_precondition_2)

            MATCH (relation_node) -[:PRECONDITION]-> (relation_node_precondition)

            RETURN node_entity_precondition_1.name AS entity_1,
                   node_entity_precondition_2.name AS entity_2, 
                   relation_node_precondition.node_id AS node_id,
                   relation_node_precondition.relation AS relation, 
                   relation_node_precondition.block AS block, 
                   relation_node_precondition.lou AS lou, 
                   relation_node_precondition.was_seen AS was_seen,
                   relation_node_precondition.complexity AS complexity 
            """
    result_dependencies = tx.run(query)

    dependencies_list = []
    for res in result_dependencies:

        node_dict = {'id': res.get('node_id'),
                     'block': res.get('block'),
                     'lou': res.get('lou'),
                     'triple': f"""{res.get('entity_1')} {res.get('relation')} {res.get('entity_2')}""",
                     'was_seen': res.get('was_seen'),
                     'complexity': res.get('complexity')}

        dependencies_list.append(node_dict)

    query = f"""
            MATCH (relation_node:RELATION_NODE) WHERE relation_node.node_id = {node_id}
            
            MATCH (node_entity_1) -[:TRIPLE_RELATION]-> (relation_node:RELATION_NODE)
            MATCH (relation_node:RELATION_NODE) -[:TRIPLE_RELATION]-> (node_entity_2)

            RETURN node_entity_1.name AS entity_1,
                   node_entity_2.name AS entity_2, 
                   relation_node.node_id AS node_id,
                   relation_node.relation AS relation, 
                   relation_node.block AS block, 
                   relation_node.lou AS lou, 
                   relation_node.complexity AS complexity 
            """
    result = tx.run(query)

    if result.peek() is None:
        return None

    res = result.single()

    node_id = res.get('node_id')
    triple = f"""{res.get('entity_1')} {res.get('relation')} {res.get('entity_2')}"""
    block = res.get('block')
    lou = res.get('lou')
    complexity = res.get('complexity')

    node = ConditionedNode(id=node_id, block=block, triple=triple, dependencies=dependencies_list,
                           complexity=complexity,
                           lou=lou, classes_triple=None)
    return node


def _get_triple_block_id(tx, block):

    query = f"""
            MATCH (relation_node:RELATION_NODE) WHERE relation_node.block = '{block}'
            RETURN  relation_node.node_id AS node_id
            """
    result = tx.run(query)

    if result.peek() is None:
        return None

    node_ids = []
    for rec in result:
        node_ids.append(rec.get('node_id'))

    return node_ids


def _delete_all(tx):

    # Delete all nodes and relationships
    query = f"""
            MATCH (n)
            DETACH DELETE n
            """
    tx.run(query)


def _create_conditions(tx, entity_1, entity_2, relation_1, entity_3, entity_4, relation_2):

    query = f"""
            MATCH ({{name: '{entity_1}'}}) -[:TRIPLE_RELATION]-> (relation_node_1:RELATION_NODE)
            MATCH (relation_node_1:RELATION_NODE {{relation: '{relation_1}'}}) -[:TRIPLE_RELATION]-> ({{name: '{entity_2}'}})

            MATCH ({{name: '{entity_3}'}}) -[:TRIPLE_RELATION]-> (relation_node_2:RELATION_NODE)
            MATCH (relation_node_2:RELATION_NODE {{relation: '{relation_2}'}}) -[:TRIPLE_RELATION]-> ({{name: '{entity_4}'}})

            MERGE (relation_node_1)-[:PRECONDITION]->(relation_node_2)
            """
    tx.run(query)


def _create_triple(tx, entity_a, relation, entity_b, domain, block, complexity, node_id):
    """
        Create nodes and relationship for a triple including added lou

        :param entity_a: first entity of the triple
        :param relation: relation of the triple
        :param entity_b: second entity of the triple
        :param domain: domain label for the triple, e.g: quarto
        :param block: block of the triple
        :param complexity: complexity of the triple
    """

    query = f"""
            MERGE (node_entity_1: {domain} {{name: '{entity_a}'}})
            MERGE (node_entity_2: {domain} {{name: '{entity_b}'}})
            CREATE (relation_node:RELATION_NODE {{node_id: {node_id},
                                                  lou: 0,
                                                  complexity: {complexity},
                                                  was_seen: false,
                                                  block: '{block}',
                                                  relation: '{relation}'}})  
            MERGE (node_entity_1) -[:TRIPLE_RELATION]-> (relation_node)
            MERGE (relation_node) -[:TRIPLE_RELATION]-> (node_entity_2)
            """
    tx.run(query)


def _initialize_db(driver):
    # ensure parsed ontology is available
    parse_ontology.parse_quarto_ontology()

    # read ontologies
    df_quarto = pd.read_csv('severusStudy/snape/content/ontologies/new_ontology_parsed.csv')
    with driver.session() as session:

        node_id = 0
        # clear db
        session.execute_write(_delete_all)

        # add quarto nodes
        for _, row in df_quarto.iterrows():
            session.execute_write(_create_triple, row['Start Node'], row['Relation'], row['End Node'],
                                  'QUARTO_ENTITY', row['Block'], row['Complexity'], node_id)
            node_id = node_id + 1

        # add conditions between quarto nodes
        for _, row in df_quarto.iterrows():
            if str(row['Condition']) == 'nan':
                continue
            cond_list = _format_string(str(row['Condition']))
            for triple in cond_list:
                session.execute_write(_create_conditions, row['Start Node'], row['End Node'], row['Relation'],
                                      triple[0], triple[2], triple[1])

    return 0
