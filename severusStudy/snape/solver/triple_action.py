from enum import IntEnum


class ActionType(IntEnum):
    """Enum for type of explanation."""

    PROVIDE_DECLARATIVE = 1
    PROVIDE_COMPARISON = 2
    DEEPEN_REPEAT = 3
    DEEPEN_ADDITIONAL = 4
    DEEPEN_EXAMPLE = 5
    DEEPEN_COMPARISON = 6
    ANSWER_DECLARATIVE = 7
    ANSWER_SUMMARIZE = 8
    ANSWER_POLAR = 9
    STRUCTURE_SUMMARIZE = 10
    STRUCTURE_BRIDGING = 11
    STRUCTURE_COMPREHENSION = 12
    STRUCTURE_MENTALIZE = 13


class TripleAction:
    """Explanation action referencing triple to be performed by MCTS.

    Attributes:
        type: Explanation type
        triple: Corresponding triple as string.
        triple_id: Corresponding triple id.
    """

    action_type: ActionType
    triple: str
    triple_id: int

    def __init__(self, action_type: ActionType, triple: str, node_id: int):
        self.action_type = action_type
        self.triple = triple
        self.triple_id = node_id

    def __str__(self):
        return str((self.action_type, self.triple))

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return self.action_type == other.action_type and self.triple == other.triple

    def __hash__(self):
        return hash((self.action_type, self.triple))

    @property
    def log(self):
        return [self.triple, self.action_type]
