from time import perf_counter


class TraceRecorder:
    def __init__(self, interval=1):
        self.interval = interval
        self.frames = []
        self.last_frame = None
        self.duration = 0.0

    def __call__(
        self,
        state,
        iteration,
        objective_value,
        best_value,
        **details,
    ):
        started = perf_counter()

        frame = {
            "iteration": iteration,
            "objective_value": objective_value,
            "best_value": best_value,
            "placements": [
                vars(placement).copy()
                for ship_state in state.ships
                for placement in ship_state.placements
            ],
            **details,
        }

        self.last_frame = frame

        if iteration == 0 or iteration % self.interval == 0:
            self.frames.append(frame)

        self.duration += perf_counter() - started

    def finish(self):
        if self.last_frame is None:
            return self.frames

        if not self.frames:
            self.frames.append(self.last_frame)
        elif self.frames[-1]["iteration"] != self.last_frame["iteration"]:
            self.frames.append(self.last_frame)

        return self.frames