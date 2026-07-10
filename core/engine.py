class Engine:

    name = "BaseEngine"

    def run(self, state, bus):
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement run()."
        )
