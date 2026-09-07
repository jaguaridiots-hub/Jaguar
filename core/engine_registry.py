import time
import traceback

class EngineRegistry:

    def __init__(self):
        self.engines = []
        self._engine_names = set()  # for duplicate detection

    def register(self, engine):
        # Determine engine name – use engine.engine_name if set, else class name
        name = getattr(engine, "engine_name", engine.__class__.__name__)
        if name in self._engine_names:
            raise ValueError(f"Engine '{name}' already registered. Duplicate registration detected.")
        self._engine_names.add(name)
        self.engines.append(engine)

    def get_engine_names(self):
        """Return list of all registered engine names."""
        return list(self._engine_names)

    def run(self, state, bus, skip=None):
        if skip is None:
            skip = set()

        # Initialize tracking if not already present
        if not hasattr(state, "engine_status"):
            state.engine_status = {}

        if not hasattr(state, "engine_time"):
            state.engine_time = {}

        if not hasattr(state, "error"):
            state.error = None

        total_start = time.perf_counter()

        for engine in self.engines:
            name = getattr(engine, "engine_name", engine.__class__.__name__)
            if name in skip:
                continue

            print("\n" + "=" * 60)
            print(f"Running Engine : {name}")
            print("=" * 60)

            start = time.perf_counter()

            try:
                engine.run(state, bus)

                elapsed = time.perf_counter() - start

                state.engine_status[name] = "OK"
                state.engine_time[name] = elapsed

                print(f"✓ {name} completed")
                print(f"Time : {elapsed:.4f} sec")

            except Exception as e:
                elapsed = time.perf_counter() - start

                state.engine_status[name] = "FAILED"
                state.engine_time[name] = elapsed

                print(f"✗ {name} FAILED")
                print(f"Time : {elapsed:.4f} sec")
                print(f"Error : {e}")

                traceback.print_exc()

                state.error = {
                    "engine": name,
                    "error": str(e),
                    "elapsed": elapsed,
                }

                break

        total_elapsed = time.perf_counter() - total_start

        state.total_time = total_elapsed

        print("\n" + "=" * 60)
        print("JAGUAR PIPELINE FINISHED")
        print(f"Total Time : {total_elapsed:.4f} sec")
        print("=" * 60)

        return state
