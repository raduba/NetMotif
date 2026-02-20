from enum import Enum
from typing import Callable, Tuple, Dict

# (State, progress towards it in [0, 1])
# This should, at minimum, be called with progress=0 and progress=1.
type ProgressUpdate = Callable[[ProgressState, float], None] | None

type Logger = Callable[[str], None] | None

class ProgressState(Enum):
    ESU = 0,
    LABELING = 1,
    RANDOM = 2,

PROGRESS_LABELS = {
    ProgressState.ESU: "ESU algorithm in progress...",
    ProgressState.LABELING: "Labeling algorithm in progress...",
    ProgressState.RANDOM: "Random graph generation in progress...",
}

def create_scoped_progress() -> ProgressUpdate:
    """
    Manages creating/deleting multiple progress bars.
    When progress reaches 1, the bar is deleted.
    """

    import streamlit as st

    active_bars: Dict[ProgressState, st.progress] = {}

    def progress(state: ProgressState, progress: float):
        text = PROGRESS_LABELS[state]
        if progress == 1:
            text += " Done!"

        if not state in active_bars:
            active_bars[state] = st.progress(progress, text=text)
        else:
            active_bars[state].progress(progress, text=text)

        if progress == 1:
            active_bars[state].empty()
            del active_bars[state]

    return progress