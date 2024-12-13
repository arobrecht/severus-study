from severusStudy.snape.databank.neo4j_interface import Neo4jInterface


def test_match_triple():
    neo4j_uri = "bolt://localhost:7687"
    neo4j_login = "neo4j"
    neo4j_password = "snape-ontologie"
    neo = Neo4jInterface(neo4j_uri, neo4j_login, neo4j_password)

    # q_type = 1
    triple = '? sein_können Überraschend'
    result, q_type = neo.match_triple(triple)
    assert len(result.values()) == 1
    assert next(iter(result.values())).triple == 'Niederlage sein_können Überraschend'
    assert q_type == 1

    triple = 'Niederlage ? Überraschend'
    result, q_type = neo.match_triple(triple)
    assert len(result.values()) == 1
    assert next(iter(result.values())).triple == 'Niederlage sein_können Überraschend'
    assert q_type == 1

    triple = 'Niederlage sein_können ?'
    result, q_type = neo.match_triple(triple)
    assert len(result.values()) == 1
    assert next(iter(result.values())).triple == 'Niederlage sein_können Überraschend'
    assert q_type == 1

    # q_type = 2
    triple = 'Niederlage sein_können Überraschend'
    result, q_type = neo.match_triple(triple)
    assert len(result.values()) == 1
    assert next(iter(result.values())).triple == 'Niederlage sein_können Überraschend'
    assert q_type == 2

    # q_type = 3
    triple = 'Verlieren sein_können Überraschend'
    result, q_type = neo.match_triple(triple)
    assert len(result.values()) == 1
    assert next(iter(result.values())).triple == 'Niederlage sein_können Überraschend'
    assert q_type == 3

    triple = 'Niederlage ist Überraschend'
    result, q_type = neo.match_triple(triple)
    assert len(result.values()) == 1
    assert next(iter(result.values())).triple == 'Niederlage sein_können Überraschend'
    assert q_type == 3

    triple = 'Niederlage sein_können Unerwartet'
    result, q_type = neo.match_triple(triple)
    assert len(result.values()) == 1
    assert next(iter(result.values())).triple == 'Niederlage sein_können Überraschend'
    assert q_type == 3

    # q_type = 0
    triple = 'Verlieren ist Überraschend'
    result, q_type = neo.match_triple(triple)
    assert len(result.values()) == 0
    assert q_type == 0

    neo.close()


def test_set_lou():
    neo4j_uri = "bolt://localhost:7687"
    neo4j_login = "neo4j"
    neo4j_password = "snape-ontologie"
    neo = Neo4jInterface(neo4j_uri, neo4j_login, neo4j_password)

    neo.set_lou(0, 777)
    node = neo.get_node(0)
    assert node.lou == 777

    neo.set_lou(0, 0)
    node = neo.get_node(0)
    assert node.lou == 0

    result = neo.set_lou(777, 777)
    assert result is False

    neo.close()


def test_get_node():
    neo4j_uri = "bolt://localhost:7687"
    neo4j_login = "neo4j"
    neo4j_password = "snape-ontologie"
    neo = Neo4jInterface(neo4j_uri, neo4j_login, neo4j_password)

    node = neo.get_node(0)
    assert node.lou == 0
    assert node.block == 'Spiel'
    assert node.was_seen is False
    assert node.complexity == 1
    assert node.triple == 'Spiel sein Brettspiel'

    node = neo.get_node(3)
    assert node.lou == 0
    assert node.block == 'Spiel'
    assert node.was_seen is False
    assert node.complexity == 1
    assert node.triple == 'Spiel spieldauer_haben Zehn_Minuten'
    assert node.dependencies[0]['id'] == 0
    assert node.dependencies[0]['triple'] == 'Spiel sein Brettspiel'

    node = neo.get_node(777)
    assert node is None

    neo.close()


def test_get_block_nodes():
    neo4j_uri = "bolt://localhost:7687"
    neo4j_login = "neo4j"
    neo4j_password = "snape-ontologie"
    neo = Neo4jInterface(neo4j_uri, neo4j_login, neo4j_password)

    nodes = neo.get_block_nodes('Hello World!')
    assert nodes is None

    nodes = neo.get_block_nodes('Additional')
    assert len(nodes) == 37

    nodes = neo.get_block_nodes('Spiel')
    assert len(nodes) == 4
    assert nodes[0].triple == 'Spiel sein Brettspiel'
    assert nodes[1].triple == 'Brettspiel sein Gesellschaftsspiel'
    assert nodes[2].triple == 'Spiel sein Komplex'
    assert nodes[3].triple == 'Spiel spieldauer_haben Zehn_Minuten'

    nodes = neo.get_block_nodes('Spieler')
    assert len(nodes) == 5

    nodes = neo.get_block_nodes('Spiel')
    assert len(nodes) == 4

    nodes = neo.get_block_nodes('Ende')
    assert len(nodes) == 7

    nodes = neo.get_block_nodes('Spielziel')
    assert len(nodes) == 12

    nodes = neo.get_block_nodes('Spielzuege')
    assert len(nodes) == 21

    nodes = neo.get_block_nodes('Spielfiguren')
    assert len(nodes) == 8

    nodes = neo.get_block_nodes('Spielbrett')
    assert len(nodes) == 5

    nodes = neo.get_block_nodes('Strategien')
    assert len(nodes) == 5

    neo.close()


def test_set_node_was_seen():
    neo4j_uri = "bolt://localhost:7687"
    neo4j_login = "neo4j"
    neo4j_password = "snape-ontologie"
    neo = Neo4jInterface(neo4j_uri, neo4j_login, neo4j_password)

    node = neo.get_node(0)
    assert node.was_seen is False

    neo.set_node_was_seen(0)
    neo.set_lou(0,7)
    node = neo.get_node(0)
    assert node.was_seen is True

    result = neo.set_node_was_seen(777)
    assert result is False

    neo.close()


def test_set_node_not_seen():
    neo4j_uri = "bolt://localhost:7687"
    neo4j_login = "neo4j"
    neo4j_password = "snape-ontologie"
    neo = Neo4jInterface(neo4j_uri, neo4j_login, neo4j_password)

    neo.set_node_was_seen(0)
    neo.set_lou(0, 7)
    node = neo.get_node(0)
    assert node.was_seen is True

    neo.set_node_not_seen(0)
    neo.set_lou(0, 0)
    node = neo.get_node(0)
    assert node.was_seen is False

    result = neo.set_node_not_seen(777)
    assert result is False

    neo.close()


if __name__ == "__main__":
    test_get_node()
    test_match_triple()
    test_set_lou()
    test_get_block_nodes()
    test_set_node_was_seen()
    test_set_node_not_seen()
