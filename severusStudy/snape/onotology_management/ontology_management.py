from abc import abstractmethod

from ..content.conditioned_node import ConditionedNode


class OntologyManagement:

    @abstractmethod
    def get_node(self, node_id: int) -> ConditionedNode:
        ...

    @abstractmethod
    def set_lou(self, node_id: int, lou: float) -> bool:
        ...

    @abstractmethod
    def set_node_was_seen(self, node_id: int) -> bool:
        ...

    @abstractmethod
    def set_node_not_seen(self, node_id: int):
        ...

    @abstractmethod
    def get_block_nodes(self, block: str) -> dict[str, ConditionedNode]:
        ...

    @abstractmethod
    def match_triple(self, triple) -> dict[int, ConditionedNode]:
        ...

    @abstractmethod
    def get_node_examples(self, node_id: int) -> [str]:
        ...

    @abstractmethod
    def get_node_comparisons(self, node_id) -> [str]:
        ...

    @abstractmethod
    def set_node_used_in_comparisons(self, triple, domain) -> bool:
        ...