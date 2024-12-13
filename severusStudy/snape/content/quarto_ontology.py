import csv
import itertools
import random
import re
import types

import numpy as np
import owlready2.prop
from owlready2 import get_ontology, Thing, ObjectProperty, ThingClass, \
    comment, Ontology

from severusStudy.snape.content.conditioned_node import ConditionedNode

COMMENT_SEPERATOR = ";"
VALID_BLOCKNAMES = ["Spiel", "Spieler", "Ende", "Spielziel",
                    "Spielzuege", "Spielfiguren", "Spielbrett",
                    "Strategien", "Additional", "NO_BLOCK"]
ENCODING = "utf-8"

ONTOLOGY_PREFIX = "QO"


class QuartoOntology:
    onto_filepath: str
    onto: Ontology
    string_to_onto_class: dict

    def __init__(self, onto_filepath):
        # self.onto_set_diff = {owlready2.prop.ObjectPropertyClass}
        self.onto_filepath = onto_filepath
        self.onto = get_ontology(ONTOLOGY_PREFIX)
        self.string_to_onto_class = {}
        self.initialize_ontology()

    def initialize_ontology(self):
        with self.onto:
            onto_csv_path = self.onto_filepath
            with open(onto_csv_path, newline="", encoding=ENCODING) as csv_file:
                reader = csv.reader(csv_file, delimiter=";")
                _ = next(reader)
                for i, line in enumerate(reader):
                    if line[0] == "":
                        continue
                    if i < 1:
                        continue
                    if len(line) <= 1:
                        continue
                    if line[0].strip()[0] == "#":
                        continue
                    try:
                        block, triple, condition, complexity = line
                    except Exception as e:
                        print("Missing info in csv,", line)
                        block, triple = line
                    triple = triple.replace(" ", "")
                    s_string, p_string, o_string = triple[1:].split(",")
                    o_string = o_string.split(")")[0]

                    s_class = types.new_class(s_string, (Thing,))
                    p_class = types.new_class(p_string, (ObjectProperty,))
                    o_class = types.new_class(o_string, (Thing,))

                    self.string_to_onto_class[s_string] = s_class
                    self.string_to_onto_class[p_string] = p_class
                    self.string_to_onto_class[o_string] = o_class

                    exec(f"s_class.{p_string}.append(o_class)")

                    self.set_triple_block((s_class, p_class, o_class), block)

                    self.set_dependencies((s_class, p_class, o_class), new_dependencies=condition.strip())

            # sync_reasoner()

    def get_complexity(self):
        complexity_dictionary = {}
        with self.onto:
            onto_csv_path = self.onto_filepath
            with open(onto_csv_path, newline="", encoding=ENCODING) as csv_file:
                reader = csv.reader(csv_file, delimiter=";")
                _ = next(reader)
                for i, line in enumerate(reader):
                    if line[0] == "":
                        continue
                    if i < 1:
                        continue
                    if len(line) <= 1:
                        continue
                    if line[0].strip()[0] == "#":
                        continue
                    try:
                        block, triple, condition, complexity = line
                        triple = triple.replace(" ", "")
                        complexity_dictionary[triple] = complexity
                    except Exception as e:
                        print("Missing info in csv,", line)
                        block, triple = line
        return (complexity_dictionary)

    def dependency_string_to_tuple_list(self, dependency_string: str):
        dependency_string = dependency_string.replace(" ", "")
        # if len(dependency_string) == 0:
        #     return []
        dep_strings = re.findall(r"\(([A-Za-z0-9_,]+)\)", dependency_string)
        result = []
        for ds in dep_strings:
            s, p, o = ds.split(",")
            result.append((self.string_to_onto_class[s], self.string_to_onto_class[p], self.string_to_onto_class[o]))
        return result

    def get_class_ancestors(self, source: ThingClass) -> list[ThingClass]:
        """
        Returns relevant ancestors for the source class.
        :param c:
        :return:
        """
        return source.ancestors(False, True).difference({owlready2.Thing})

    def get_ingoing_relations_from_entity(self, node: ThingClass):
        relevant_triples = []
        descendants: list[ThingClass] = node.inverse_restrictions()
        for d in descendants:
            for rel in d.ancestors(False, True).difference({owlready2.Thing}):
                if rel.value == node:
                    relevant_triples.append((d, rel.property, rel.value))
        return relevant_triples

    def get_outgoing_relations_from_entity(self, node: ThingClass):
        relevant_triples = []

        ancestors: list[ThingClass] = self.get_class_ancestors(node)
        for a in ancestors:
            # if isinstance(a, owlready2.class_construct.Restriction):
            relevant_triples.append((node, a.property, a.value))
            # elif isinstance(a, owlready2.entity.ThingClass):
            #     relevant_triples.append((source, "ist_ein", a))
        return relevant_triples

    def get_triples_with_entity(self, node: ThingClass):
        """
        Retrieves all triples from the KG containing the source Node as subject or object.

        :param node: KG Node for which to get all out- and ingoing edges
        :return: list of triples with out- and ingoing kg connections
        """
        return self.get_ingoing_relations_from_entity(node) + self.get_outgoing_relations_from_entity(node)

    def parse_comment_string(self, c_string: str):
        if len(c_string) == 0:
            grounded = False
            block = "NO_BLOCK"
            dependency = []
            return grounded, block, dependency

        # unpack list
        if len(c_string) == 1:
            c_string = c_string[0]

        grounded_state = c_string.split(COMMENT_SEPERATOR)[0].split(":")[-1]
        match grounded_state:
            case "True":
                grounded = True
            case "False":
                grounded = False
            case _:
                assert False, "Something went wrong in ontology comment, grounded state not bool"
        block = c_string.split(COMMENT_SEPERATOR)[1].split(":")[-1]

        dependencies = c_string.split(COMMENT_SEPERATOR)[2].split(":")[-1]
        return grounded, block, dependencies

    def build_comment_string(self, grounded: bool, block: str, dependencies: list[tuple]):
        assert block in VALID_BLOCKNAMES, f"Wrong block; {block}"
        assert isinstance(grounded, bool), "Grounded state not bool"
        comment_string = f"grounded:{str(grounded)}{COMMENT_SEPERATOR}block:{block}{COMMENT_SEPERATOR}dependencies:{dependencies}"
        return comment_string

    def set_triple_block(self, triple: tuple, new_block):
        assert new_block in VALID_BLOCKNAMES, f"Wrong block; {new_block}"
        s, p, o = triple
        grounded, _, dependencies = self.parse_comment_string(comment[s, p, o])
        comment[s, p, o] = self.build_comment_string(grounded, new_block, dependencies)

    def get_triple_block(self, triple: tuple) -> str:
        s, p, o = triple
        _, block, _ = self.parse_comment_string(comment[s, p, o])
        return block

    def set_dependencies(self, triple: tuple, new_dependencies: list[tuple]):
        s, p, o = triple
        grounded, block, _ = self.parse_comment_string(comment[s, p, o])
        comment[s, p, o] = self.build_comment_string(grounded, block, new_dependencies)

    def get_dependencies(self, triple: tuple):
        s, p, o = triple
        _, _, dependencies = self.parse_comment_string(comment[s, p, o])
        return self.dependency_string_to_tuple_list(dependencies)

    def get_explanation_block(self, blockname):
        assert blockname in VALID_BLOCKNAMES, f"Unknown blockname; {blockname}"
        return list(filter(lambda x: self.get_triple_block(x) == blockname, self.get_all_triples()))

    def get_all_triples(self):

        triples = set()

        for c in self.onto.classes():
            for trip in self.get_triples_with_entity(c):
                if trip not in triples:
                    triples.add(trip)

        return triples


def parse_ontology(onto_fp, verification_path, templates_path):
    from .block import Block

    ontology_tool = QuartoOntology(onto_fp)
    block_dict = {}
    blocks_to_nodes = {}
    complexities = ontology_tool.get_complexity()
    nodes = {}
    triple_to_nodes = {}
    additional_information = ontology_tool.get_explanation_block("Additional")
    res = ontology_tool.get_all_triples()
    for triple in res:
        blockname = ontology_tool.get_triple_block(triple)

        node = ConditionedNode(
            id=hash(str(triple).replace("QO.", "").strip()),
            block=blockname,
            triple=str(triple).replace("QO.", "").strip(),
            complexity=int(complexities[str(triple).replace("QO.", "").replace(" ", "")]),
            # complexity = 1,
            classes_triple=triple,
            dependencies=[],
        )
        nodes[node.id] = node
        triple_to_nodes[triple] = node

        if blockname not in blocks_to_nodes.keys():
            blocks_to_nodes[blockname] = [node]
        else:
            blocks_to_nodes[blockname].append(node)

    for i in triple_to_nodes:
        pass
    for node_id, node in nodes.items():
        # relations = ontology_tool.get_triples_with_entity(node.classes_triple[0]) \
        #             + ontology_tool.get_triples_with_entity(node.classes_triple[-1])
        # node.dependencies = [triple_to_nodes[rel].id for rel in relations]
        deps = ontology_tool.get_dependencies(node.classes_triple)
        node.dependencies = [{"id": triple_to_nodes[dep].id} for dep in deps]

    # get verification questions and answers from file
    verification_dict = {}
    with open(verification_path, newline="", encoding=ENCODING) as csv_file:
        reader = csv.reader(csv_file, delimiter=";")
        for i, (block_id, block_name, question, answer) in enumerate(reader):
            block_id = block_id.strip()
            answers = [x.strip().lower() for x in answer.split(",")]
            verification_dict[block_id] = {"question": question, "answers": answers}

    for blockname in blocks_to_nodes.keys():

        if blockname != "Additional":
            block = Block(blockname, blockname,
                          [node.id for node in blocks_to_nodes[blockname]],
                          verification_dict[blockname]["question"], verification_dict[blockname]["answers"])
        else:
            block = Block(blockname, blockname,
                          [node.id for node in blocks_to_nodes[blockname]],
                          "Kapisch?", ["ja"])
        block_dict[blockname] = block

    baseline_block_dict = {name: [] for name in block_dict.keys()}
    return block_dict, list(nodes.values()), baseline_block_dict, additional_information
