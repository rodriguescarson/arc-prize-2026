"""Agents follow the ARC-AGI-3-Agents contract so the same class can be spliced into a Kaggle notebook:

    class MyAgent:
        game_id: str
        def is_done(self, frames: list[FrameData], latest_frame: FrameData) -> bool
        def choose_action(self, frames: list[FrameData], latest_frame: FrameData) -> GameAction

`frames` is the full history (FrameData objects; .frame is a list of 64x64 int grids, .state, .levels_completed,
.win_levels, .available_actions). ACTION6 needs .set_data({"x":..,"y":..}) on a 64x64 grid.
Only standard-library + numpy inside agents, so they run in the no-internet Kaggle kernel.
"""
