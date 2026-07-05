class ModuleRegistry:

    def __init__(self):
        self.modules = {}

    def register(self, name):
        self.modules[name] = "READY"

    def unregister(self, name):
        if name in self.modules:
            del self.modules[name]

    def show(self):
        print("\n========== JAGUAR MODULE REGISTRY ==========\n")

        for name, status in self.modules.items():
            print(f"✓ {name:<25} {status}")

        print("\nTotal Modules :", len(self.modules))
