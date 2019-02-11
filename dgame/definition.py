from typing import Tuple


class BoardDefinition:
    """
        This is an abstract class definition how a board is structured.
        The Game engine should be able to handle any kind of board given its definition.

        This class holds the adajency list used by the dgame engine to resolve orders
    """
    PROVINCE_DB: Tuple[any]

    def province_from_string(self, name: str) -> 'Provinces':
        raise NotImplementedError
