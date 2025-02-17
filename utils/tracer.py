import time
import threading
import signal
import os
from collections import defaultdict
from datetime import datetime

class Tracer:
    HTML_ROOT = "/tmp/tracer"
    GNUPLOT_CMD = "/usr/bin/gnuplot"
    enabled = False
    tracer_map = defaultdict(list)
    tracer_registry = {}
    tracer_id_registry = []
    tracer_map_lock = threading.Lock()
    process_version_info = ""

    class Tick:
        def __init__(self, name):
            self.name = name
            self.timestamp = time.monotonic()

    def __init__(self, name):
        self.name = name
        self.ticks = []
        self.ticks_reserve_size = 0

    def tick(self, tick_name):
        if Tracer.enabled:
            self.ticks.append(Tracer.Tick(tick_name))
            self.ticks_reserve_size = max(len(self.ticks), self.ticks_reserve_size)

    def end_trace(self):
        if Tracer.enabled:
            Tracer.tracer_map[self.name].append(self.ticks)

    @staticmethod
    def begin_trace(name, tracer_id=-1):
        if Tracer.enabled:
            return Tracer._begin_trace(name, tracer_id)
        else:
            return Tracer(name)  # dummy non-null

    @staticmethod
    def _begin_trace(name, tracer_id=-1):
        tracer = Tracer(name)
        Tracer.tracer_registry[name] = tracer
        return tracer

    @staticmethod
    def continue_or_begin_trace(name, tracer_id=-1, new_trace=None):
        if Tracer.enabled:
            return Tracer._continue_or_begin_trace(name, tracer_id, new_trace)
        else:
            return Tracer(name)

    @staticmethod
    def _continue_or_begin_trace(name, tracer_id=-1, new_trace=None):
        if name in Tracer.tracer_registry:
            tracer = Tracer.tracer_registry[name]
            if new_trace is not None:
                new_trace = False
            return tracer
        else:
            tracer = Tracer._begin_trace(name, tracer_id)
            if new_trace is not None:
                new_trace = True
            return tracer

    @staticmethod
    def enable_tracing(enable):
        Tracer.enabled = enable

    @staticmethod
    def register_signal_handler(sig):
        if Tracer.enabled:
            signal.signal(sig, Tracer.sighandle)

    @staticmethod
    def sighandle(signum, frame):
        Tracer.analyze()

    @staticmethod
    def analyze():
        with Tracer.tracer_map_lock:
            for name, tick_lists in Tracer.tracer_map.items():
                print(f"Analyzing {name}")
                for ticks in tick_lists:
                    for tick in ticks:
                        print(f"Tick: {tick.name} at {tick.timestamp}")

class AutoEndTrace:
    def __init__(self, tracer, is_new_trace):
        self.tracer = tracer
        self.is_new_trace = is_new_trace

    def __del__(self):
        if self.is_new_trace:
            self.tracer.end_trace()

# Example usage
if __name__ == "__main__":
    Tracer.enable_tracing(True)
    Tracer.register_signal_handler(signal.SIGUSR1)
    t1 = Tracer.begin_trace("My Trace")
    t1.tick("init_done")
    time.sleep(1)
    t1.tick("process_done")
    t1.end_trace()
    os.kill(os.getpid(), signal.SIGUSR1)
