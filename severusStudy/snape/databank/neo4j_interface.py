import logging
import os
import time
import json
from typing import Any

from neo4j import GraphDatabase, basic_auth, Query
from ..onotology_management.ontology_management import OntologyManagement
from ..content.conditioned_node import ConditionedNode


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

    def __init__(self, uri: str, admin_login: str, admin_password: str, user_id: str, user_default_password='default_password') -> None:
        """
        Initialize the Neo4jInterface and db

        Args:
            uri: URI of the Neo4j database
            admin_login: admin login username
            admin_password: admin login password
            user_id: id of the user to be added to the database
            user_default_password: new user default password
        """
        logging.getLogger("neo4j").setLevel(logging.ERROR)
        self.uri = uri
        self.driver = None

        # Step 1: Use admin connection to create user
        self.user_id = str(user_id)
        self._create_db_user(admin_login, admin_password, self.user_id, user_default_password)

        # Step 2: Connect as the new user
        self.password = user_default_password
        self.driver = self._connect()

        # Step 3: Initialize the database with the user driver
        _initialize_db(self.driver, self.user_id)


    def _create_db_user(self, admin_login, admin_password, user_to_create, user_password):
        """
        Uses a temporary admin connection to create a new user if they don't already exist.
        """
        admin_driver = None
        try:
            admin_driver = GraphDatabase.driver(self.uri, auth=basic_auth(admin_login, admin_password))

            with admin_driver.session() as session:
                create_user_query = Query("""
                        CREATE USER $user IF NOT EXISTS
                        SET PASSWORD $password
                        SET PASSWORD CHANGE NOT REQUIRED
                        """)
                session.run(create_user_query, user=user_to_create, password=user_password)


                print(f"User '{user_to_create}' is configured.")
        except Exception as e:
            print(f"An error occurred during the user creation: {e}")
            raise
        finally:
            if admin_driver:
                admin_driver.close()


    def _connect(self):
        """
        Connects the interface to the database using the specific user's credentials.
        """
        print(f"Connecting to Neo4j as user '{self.user_id}'...")
        try:
            driver = GraphDatabase.driver(self.uri, auth=basic_auth(self.user_id, self.password))
            driver.verify_connectivity()
            print("Connection successful.")
            return driver
        except Exception as e:
            print(f"Failed to connect as user '{self.user_id}': {e}")
            raise


    def close(self):
        """
        Closes the connection to the database.
        """
        if self.driver:

            print(f"Deleting graph for user '{self.user_id}'...")
            with (self.driver.session() as session):
                session.execute_write(_delete_all, self.user_id)

            print(f"Closing connection for user '{self.user_id}'...")
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
            result = session.execute_write(_set_lou, node_id, lou, self.user_id)
        return result


    def get_node(self, node_id: int) -> ConditionedNode:
        """
        Get a conditioned node from the db using the node_id

        Args:
            node_id: id of the node

        Returns:
            conditioned_node object of the node including all values, None if the node does not exist.
        """
        with self.driver.session() as session:
            result = session.execute_write(_get_triple, node_id, self.user_id)
        return result


    def get_block_nodes(self, block: str) -> dict[Any, Any] | None:
        """
        Get all nodes in a block of the ontology

        Args:
            block: name as string

        Returns:
            dictionary containing all conditioned_node of the block(key = node_id)
        """
        triple_dict = {}
        with self.driver.session() as session:
            result = session.execute_write(_get_triple_block_id, block, self.user_id)
            if result is None:
                return None
            for node_id in result:
                t = session.execute_read(_get_triple, node_id, self.user_id)
                if t is None:
                    continue
                triple_dict[t.id] = t

        return triple_dict


    def match_triple(self, triple: str) -> dict[Any, Any]:
        """
        Tries to match a given triple to a triple in the db, uses levenshtein distance -> allow two typos\n
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
            matches= session.execute_write(_get_node_id, triple, self.user_id)
            for res in matches:
                triple = session.execute_read(_get_triple, res, self.user_id)
                if triple is None:
                    continue
                session.execute_write(_decr_lou, triple.id, decr_lou_amount, self.user_id)

                triple = session.execute_read(_get_triple, res, self.user_id)
                matches_dict[triple.id] = triple
        return matches_dict


    def set_node_was_seen(self, node_id: int) -> bool:
        """
        Set the was_seen attribute of a node to true

        Args:
            node_id: id of the node

        Returns:
            True if the was_seen attribute was set, False otherwise.

        """
        with self.driver.session() as session:
            result = session.execute_write(_set_node_seen, node_id, self.user_id)
        return result


    def set_node_not_seen(self, node_id: int) -> bool:
        """
        Set the was_seen attribute of a node to false

        Args:
            node_id:

        Returns:
            True if the was_seen attribute was set to false, False otherwise.

        """
        with self.driver.session() as session:
            result = session.execute_write(_set_node_not_seen, node_id, self.user_id)
        return result


    def get_node_examples(self, node_id: int) -> [str]:
        """
        Get all example templates for a node, returns empty list if none exist

        Args:
            node_id: of the node

        Returns:
            List of examples, empty list if none exist.

        """
        with self.driver.session() as session:
            result = session.execute_write(_get_node_examples, node_id, self.user_id)
        return result


    def get_node_comparisons(self, node_id: int) -> [str]:
        """
        Get all comparison triples for a node, returns empty list if none exist
        Matches all comparison triples with distance <= 1

        Args:
            node_id: of the node

        Returns:
            List of comparison triples, empty list if none exist.

        """
        with self.driver.session() as session:
            result = session.execute_write(_get_node_comparisons, node_id, self.user_id)
        return result


    def set_node_used_in_comparisons(self, triple_id: int, domain: str) -> bool:
        """
        Set the used_in_comparisons attribute of a comparison node to true

        Args:
            triple: the comparison triple
            domain: the domain of the triple

        Returns:
            True if the used_in_comparisons attribute was set, False otherwise.
        """
        with self.driver.session() as session:
            result = session.execute_write(_set_node_used_in_comparisons, triple_id, domain, self.user_id)
        return result

#      <----------- NEO4J QUERIES BELOW ----------->

def _get_node_id(tx, triple, user_id):

    triple = triple.replace('(', '')
    triple = triple.replace(')', '')
    entity_1, relation, entity_2 = triple.split(', ')

    query = f"""
            MATCH (user: USER {{user_id: '{user_id}'}})
    
            MATCH (user) -[:OWNS]-> (node_entity_1:QUARTO_ENTITY) 
            MATCH (user) -[:OWNS]-> (node_entity_2:QUARTO_ENTITY)

            MATCH (node_entity_1) -[:TRIPLE_RELATION]-> (relation_node:RELATION_NODE)
            MATCH (user) -[:OWNS]-> (relation_node:RELATION_NODE) -[:TRIPLE_RELATION]-> (node_entity_2)

            WHERE node_entity_1.name = '{entity_1}' 
            AND node_entity_2.name = '{entity_2}'
            AND relation_node.relation = '{relation}'

            RETURN relation_node.node_id AS node_id
            """

    result = tx.run(query)
    matches = []
    for res in result:
        print(dict(res))
        matches.append(res.get('node_id'))
    return matches


def _set_lou(tx, node_id, lou, user_id):
    query = f"""
            MATCH (user: USER {{user_id: '{user_id}'}})
    
            MATCH (user) -[:OWNS]-> (relation_node:RELATION_NODE) WHERE relation_node.node_id = {node_id}
            SET relation_node.lou = {lou}
            RETURN relation_node
            """

    result = tx.run(query)
    record = result.single()

    if record:
        return True
    else:
        return False


def _set_node_seen(tx, node_id, user_id):
    query = f"""
            MATCH (user: USER {{user_id: '{user_id}'}})
    
            MATCH (user) -[:OWNS]-> (relation_node:RELATION_NODE) WHERE relation_node.node_id = {node_id}
            SET relation_node.was_seen = true
            RETURN relation_node
            """

    result = tx.run(query)
    record = result.single()

    if record:
        return True
    else:
        return False


def _set_node_not_seen(tx, node_id, user_id):
    query = f"""
            MATCH (user: USER {{user_id: '{user_id}'}})
    
            MATCH (user) -[:OWNS]-> (relation_node:RELATION_NODE) WHERE relation_node.node_id = {node_id}
            SET relation_node.was_seen = false
            RETURN relation_node
            """

    result = tx.run(query)
    record = result.single()

    if record:
        return True
    else:
        return False


def _decr_lou(tx, node_id, decr_amount, user_id):
    query = f"""
            MATCH (user: USER {{user_id: '{user_id}'}})
            
            MATCH (user) -[:OWNS]-> (relation_node:RELATION_NODE) WHERE relation_node.node_id = {node_id} 
            SET relation_node.lou = relation_node.lou - {decr_amount}
            RETURN relation_node
            """

    result = tx.run(query)
    record = result.single()

    if record:
        return True
    else:
        return False


def _get_triple(tx, node_id, user_id):
    query = f"""
            MATCH (user: USER {{user_id: '{user_id}'}})
    
            MATCH (user) -[:OWNS]-> (relation_node:RELATION_NODE) WHERE relation_node.node_id = {node_id}

            MATCH (user) -[:OWNS]-> (node_entity_precondition_1) -[:TRIPLE_RELATION]-> (relation_node_precondition:RELATION_NODE)
            MATCH (user) -[:OWNS]-> (relation_node_precondition:RELATION_NODE) -[:TRIPLE_RELATION]-> (node_entity_precondition_2)
            MATCH (user) -[:OWNS]-> (node_entity_precondition_2)

            MATCH (user) -[:OWNS]-> (relation_node) -[:PRECONDITION]-> (relation_node_precondition)

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
            MATCH (user: USER {{user_id: '{user_id}'}})
    
            MATCH (user) -[:OWNS]-> (relation_node:RELATION_NODE) WHERE relation_node.node_id = {node_id}
            
            MATCH (user) -[:OWNS]-> (node_entity_1) -[:TRIPLE_RELATION]-> (relation_node:RELATION_NODE)
            MATCH (relation_node:RELATION_NODE) -[:TRIPLE_RELATION]-> (node_entity_2)
            MATCH (user) -[:OWNS]-> (node_entity_2)

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

    query = f"""
            MATCH (user: USER {{user_id: '{user_id}'}})    
            
            MATCH (user) -[:OWNS]-> (relation_node:RELATION_NODE) WHERE relation_node.node_id = {node_id}
            MATCH (relation_node) -[:EXAMPLE_RELATION]-> (example_node:EXAMPLE_NODE)
            MATCH (user) -[:OWNS]-> (example_node)
            RETURN example_node.example AS example
                """
    results = tx.run(query)
    has_example = False
    if results.peek() is not None:
        has_example = True

    query = f"""
            MATCH (user: USER {{user_id: '{user_id}'}})
    
            MATCH (user) -[:OWNS]-> (entity_1) -[:TRIPLE_RELATION]-> (relation_node:RELATION_NODE_COMPARISON)
            MATCH (user) -[:OWNS]-> (relation_node) -[:TRIPLE_RELATION]-> (entity_2)
            MATCH (user) -[:OWNS]-> (entity_2)

            WHERE (entity_1.name = '{res.get('entity_1')}' AND entity_2.name = '{res.get('entity_2')}'
                        AND relation_node.used_in_comparison = false AND relation_node.block = '{block}')
                        
            OR (entity_1.name = '{res.get('entity_1')}' AND relation_node.relation = '{res.get('relation')}' 
                        AND relation_node.used_in_comparison = false AND relation_node.block = '{block}')
                        
            OR (entity_2.name = '{res.get('entity_2')}' AND relation_node.relation = '{res.get('relation')}' 
                        AND relation_node.used_in_comparison = false AND relation_node.block = '{block}')

            RETURN entity_1.name AS entity_1, entity_2.name AS entity_2, relation_node.relation AS relation
            """
    results = tx.run(query)
    has_comparison = False
    if results.peek() is not None:
        has_comparison = True

    node = ConditionedNode(id=node_id, block=block, triple=triple,
                           has_example=has_example,
                           has_comparison=has_comparison,
                           dependencies=dependencies_list,
                           complexity=complexity,
                           lou=lou,
                           classes_triple=None)
    return node


def _get_triple_block_id(tx, block, user_id):
    query = f"""
            MATCH (user: USER {{user_id: '{user_id}'}})
            
            MATCH (user) -[:OWNS]-> (relation_node:RELATION_NODE) WHERE relation_node.block = '{block}'
            RETURN  relation_node.node_id AS node_id
            """
    result = tx.run(query)

    if result.peek() is None:
        return None

    node_ids = []
    for rec in result:
        node_ids.append(rec.get('node_id'))

    return node_ids


def _get_node_examples(tx, node_id, user_id):

    query = f"""
            MATCH (user: USER {{user_id: '{user_id}'}})
    
            MATCH (user) -[:OWNS]-> (relation_node:RELATION_NODE) WHERE relation_node.node_id = {node_id}
            MATCH (relation_node ) -[:EXAMPLE_RELATION]-> (example_node:EXAMPLE_NODE)
            MATCH (user) -[:OWNS]-> (example_node)
            RETURN example_node.example AS example
            """
    results = tx.run(query)

    examples = []
    for rec in results:
        examples.append(rec.get('example'))

    return examples


def _get_node_comparisons(tx, node_id, user_id):
    query = f"""
            MATCH (user: USER {{user_id: '{user_id}'}})    
            
            MATCH (user) -[:OWNS]-> (relation_node:RELATION_NODE) WHERE relation_node.node_id = {node_id}
            MATCH (user) -[:OWNS]-> (entity_1:QUARTO_ENTITY) -[TRIPLE_RELATION]-> (relation_node)
            MATCH (relation_node) -[:TRIPLE_RELATION]-> (entity_2:QUARTO_ENTITY)
            MATCH (user) -[:OWNS]-> (entity_2)
            RETURN entity_1.name AS entity_1, entity_2.name AS entity_2, relation_node.relation AS relation, relation_node.block as block
            """
    result = tx.run(query)
    result_triple = result.single()

    entity_1 = result_triple.get('entity_1')
    entity_2 = result_triple.get('entity_2')
    relation = result_triple.get('relation')
    block = result_triple.get('block')

    query = f"""
            MATCH (user: USER {{user_id: '{user_id}'}})
    
            MATCH (user) -[:OWNS]-> (entity_1) -[:TRIPLE_RELATION]-> (relation_node:RELATION_NODE_COMPARISON)
            MATCH (user) -[:OWNS]-> (relation_node) -[:TRIPLE_RELATION]-> (entity_2)
            MATCH (user) -[:OWNS]-> (entity_2)
            
            WHERE (entity_1.name = '{entity_1}' AND entity_2.name = '{entity_2}' AND relation_node.used_in_comparison = false AND relation_node.block = '{block}')
            OR (entity_1.name = '{entity_1}' AND relation_node.relation = '{relation}' AND relation_node.used_in_comparison = false AND relation_node.block = '{block}')
            OR (entity_2.name = '{entity_2}' AND relation_node.relation = '{relation}' AND relation_node.used_in_comparison = false AND relation_node.block = '{block}')
            
            RETURN relation_node.node_id AS comparison_id, labels(entity_1) AS domain
            """

    comparison_results = tx.run(query)
    comparison_triples = [{'triple_id': res.get('comparison_id'), 'domain': res.get('domain')} for res in comparison_results]

    return comparison_triples


def _set_node_used_in_comparisons(tx, triple_id, domain, user_id):

    query = f"""
                MATCH (user: USER {{user_id: '{user_id}'}})
    
                MATCH (user) -[:OWNS]-> (entity_1: {domain}) -[:TRIPLE_RELATION]-> (relation_node:RELATION_NODE_COMPARISON)
                MATCH (user) -[:OWNS]-> (relation_node) -[:TRIPLE_RELATION]-> (entity_2)
                MATCH (user) -[:OWNS]-> (entity_2)
 
                WHERE relation_node.node_id = {triple_id}
                
                SET relation_node.used_in_comparison = true
                
                RETURN relation_node.relation
                """
    result = tx.run(query)
    record = result.single()

    if record:
        return True
    else:
        return False


def _delete_all(tx, user_id):
    # Delete all nodes and relationships
    query = f"""
            MATCH (:USER {{user_id: '{user_id}'}}) -[:OWNS]-> (n)
            DETACH DELETE n
            """
    tx.run(query)


def _create_conditions(tx, triple_id, condition_triple_id, user_id):
    query = f"""
            MATCH (user: USER {{user_id: '{user_id}'}})   
       
            MATCH (user) -[:OWNS]-> (relation_node_1:RELATION_NODE {{node_id: {triple_id}}})
            MATCH (user) -[:OWNS]-> (relation_node_2:RELATION_NODE {{node_id: {condition_triple_id}}})
  
            MERGE (relation_node_1)-[:PRECONDITION]->(relation_node_2)
            """
    tx.run(query)


def _create_triple(tx, entity_a, relation, entity_b, domain, block, complexity, node_id, user_id):
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
            MATCH (user: USER {{user_id: '{user_id}'}})
            
            MERGE (node_entity_1: {domain} {{name: '{entity_a}', user_id: '{user_id}'}})
            MERGE (node_entity_2: {domain} {{name: '{entity_b}', user_id: '{user_id}'}})
            CREATE (relation_node:RELATION_NODE {{node_id: {node_id},
                                                  lou: 0,
                                                  complexity: {complexity},
                                                  was_seen: false,
                                                  block: '{block}',
                                                  relation: '{relation}',
                                                  user_id: '{user_id}'}})  
            MERGE (node_entity_1) -[:TRIPLE_RELATION]-> (relation_node)
            MERGE (relation_node) -[:TRIPLE_RELATION]-> (node_entity_2)
            
            MERGE (user)-[:OWNS]->(node_entity_1)
            MERGE (user)-[:OWNS]->(relation_node)
            MERGE (user)-[:OWNS]->(node_entity_2)
            """
    tx.run(query)


def _create_comparison_triple(tx, entity_a, relation, entity_b, domain, block, node_id, user_id):
    """
        Create nodes and relationship for a triple

        :param entity_a: first entity of the triple
        :param relation: relation of the triple
        :param entity_b: second entity of the triple
        :param domain: domain label for the triple, e.g: quarto
        :param node_id: node id of the triple
    """

    query = f"""
            MATCH (user: USER {{user_id: '{user_id}'}})
            
            MERGE (node_entity_1: {domain} {{name: '{entity_a}', user_id: '{user_id}'}})
            MERGE (node_entity_2: {domain} {{name: '{entity_b}', user_id: '{user_id}'}})
            CREATE (relation_node:RELATION_NODE_COMPARISON {{node_id: {node_id},
                                                  block: '{block}',
                                                  relation: '{relation}',
                                                  used_in_comparison: false,
                                                  user_id: '{user_id}'}})  
            MERGE (node_entity_1) -[:TRIPLE_RELATION]-> (relation_node)
            MERGE (relation_node) -[:TRIPLE_RELATION]-> (node_entity_2)
            
            MERGE (user)-[:OWNS]->(node_entity_1)
            MERGE (user)-[:OWNS]->(relation_node)
            MERGE (user)-[:OWNS]->(node_entity_2)
            """
    tx.run(query)


def _add_example(tx, node_id, example, user_id):
    """
        Create example node and reference to the triple

        :param node_id: id of triple
        :param example: example sentence
    """

    query = f"""
            MATCH (user: USER {{user_id: '{user_id}'}})
            
            MATCH (user) -[:OWNS]-> (relation_node: RELATION_NODE) WHERE relation_node.node_id = {node_id}

            CREATE (example_node: EXAMPLE_NODE {{example: '{example}', user_id: '{user_id}'}})
            CREATE (relation_node) -[:EXAMPLE_RELATION]-> (example_node)
            CREATE (user)-[:OWNS]-> (example_node)
            """
    tx.run(query)


def _add_user_node(tx, user_id):
    query = f"""
            CREATE (:USER {{user_id: '{user_id}'}})
            """
    tx.run(query)


def _initialize_db(driver, user_id):

    print('Initializing database...')

    ONTOLOGY_PATH = '../content/ontology.json'
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), ONTOLOGY_PATH), 'r', encoding='utf-8') as f:
        ontology = json.load(f)

    with (driver.session() as session):
        start = time.time()

        session.execute_write(_add_user_node, user_id)
        session.execute_write(_delete_all, user_id)

        for triple_id, triple_data in ontology.items():


            domain = f"{str(triple_data['domain']).upper()}_ENTITY"

            # TODO remove after adding utterances for BestOf4
            if domain == "BESTOF4_ENTITY":
                continue

            if domain == 'QUARTO_ENTITY':
                session.execute_write(_create_triple, triple_data['start_node'], triple_data['relation'],
                                      triple_data['end_node'], domain, triple_data['block'],
                                      triple_data['attributes']['complexity'], triple_id, user_id)

                examples = triple_data['attributes']['examples']
                if len(examples) > 0:
                    for example in examples:
                        session.execute_write(_add_example, triple_id, example, user_id)

            else:
                session.execute_write(_create_comparison_triple, triple_data['start_node'], triple_data['relation'],
                                      triple_data['end_node'], domain, f"{triple_data['block']}", triple_id, user_id)


        # after adding all triples add condition relations
        for triple_id, triple_data in ontology.items():
            if triple_data['domain'] == "Quarto":
                conditions = triple_data['attributes']['conditions']
                if len(conditions) > 0:
                    for condition_triple_id in conditions:
                        session.execute_write(_create_conditions, triple_id, condition_triple_id, user_id)


    total = (time.time() - start) * 1000
    print(f'Finished database setup in: {total:.2f} ms')
    return 0
