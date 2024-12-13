from abc import abstractmethod

from severusStudy.snape.content.conditioned_node import ConditionedNode


class OntologyManagement:

    @abstractmethod
    def get_node(self, node_id: int) -> ConditionedNode:
        ...

    @abstractmethod
    def set_lou(self, node_id: int, lou: float):
        ...

    @abstractmethod
    def set_node_was_seen(self, node_id: int):
        ...

    @abstractmethod
    def set_node_not_seen(self, node_id: int):
        ...

    @abstractmethod
    def get_block_nodes(self, block):
        ...

    @abstractmethod
    def match_triple(self, triple):
        ...