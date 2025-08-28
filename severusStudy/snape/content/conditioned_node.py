from ..decision_making.triple_action import ActionType


class ConditionedNode:
    """Represents a graph node for a triple with preconditions as references to other nodes (e.g. other triples).

    Attributes:
        id: Node id (hashed :triple string).
        _lou: Current estimated level of understanding.
        _was_seen: Flag indicating if the node already was presented to the explainee.
        templates: Dictionary keyed by ActionType containing lists of possible templates.
        triple: String representation of the triple.
        dependencies: List of node ids as references to preconditions of this node.
        complexity: Given complexity of this node as a number.
        block: Block id (as string) this node belongs to.
    """

    _lou: float
    _was_seen: bool

    @property
    def lou(self):
        return self._lou

    @lou.setter
    def lou(self, value):
        self._was_seen = True
        self._lou = value

    @property
    def was_seen(self):
        return self._was_seen

    @was_seen.setter
    def was_seen(self, value):
        self._was_seen = value

    id: int
    templates: dict[ActionType, list[str]]
    triple: str
    classes_triple: tuple
    dependencies: list[dict]
    complexity: float
    block: str
    has_example: bool
    has_comparison: bool
    templates_combined: dict[int, dict[ActionType, list[str]]] = {}

    def __init__(
            self,
            id: int,
            block: str,
            triple: str,
            has_example: bool,
            has_comparison: bool,
            dependencies: list[dict],
            complexity: float,
            classes_triple: tuple | None,
            lou: float = 0.0,

    ):
        """Create a new graph node with optional preconditions as references to other nodes.

        Args:
            block: Block id (as string) this node belongs to.
            triple: Triple this node represents.
            dependencies: Preconditions as list of node ids.
            complexity: Number indicating the estimated complexity of this node.
        """
        self._lou = lou
        self._was_seen = True if lou > 0.0 else False
        self.id = id
        self.block = block
        self.triple = triple
        self.has_example = has_example
        self.has_comparison = has_comparison
        self.classes_triple = classes_triple
        self.dependencies = dependencies
        self.complexity = complexity

    def reset(self):
        """Reset the internal level of understanding but not the :was_seen flag."""
        self._lou = 0
