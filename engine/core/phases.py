from enum import Enum

class Phase(Enum):
    REFRESH = 'REFRESH_PHASE'
    DRAW = 'DRAW_PHASE'
    DON = 'DON_PHASE'
    MAIN = 'MAIN_PHASE'
    END = 'END_PHASE'

class PhaseManager:
    """
    Manages phase transitions.
    """
    @staticmethod
    def next_phase(current: Phase) -> Phase:
        # Standard One Piece TCG Phase Flow
        if current == Phase.REFRESH:
            return Phase.DRAW
        elif current == Phase.DRAW:
            return Phase.DON
        elif current == Phase.DON:
            return Phase.MAIN
        elif current == Phase.MAIN:
            return Phase.END
        elif current == Phase.END:
            return Phase.REFRESH # Next turn
        return Phase.REFRESH
