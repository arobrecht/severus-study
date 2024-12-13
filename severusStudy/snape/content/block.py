class Block:
    """Explanation block class.

    Attributes:
        id: Block identifier as string.
        name: Block name representation as string.
        node_ids: List of node ids (int) contained in block.
        question: Validation question as string.
        valid_answers: List of valid answers to validation :question.
    """

    id: str
    name: str
    nodes_ids: list[int]
    question: str
    valid_answers: list[str]

    def __init__(
        self,
        id: str,
        name: str,
        nodes_ids: list[int],
        question: str,
        valid_answers: list[str],
    ):
        """Create a new explanation block instance.

        Args:
            id: Block identifier.
            name: Block name.
            nodes_ids: List of node ids contained in block.
            question: Validation question of block.
            valid_answers: List of valid answers to validation :question.
        """
        self.id = id
        self.name = name
        self.node_ids = nodes_ids
        self.question = question
        self.valid_answers = valid_answers
