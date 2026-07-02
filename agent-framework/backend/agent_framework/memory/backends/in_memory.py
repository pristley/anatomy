class InMemoryDB:
    def __init__(self):
        self.store = {}
    def add(self, key, value):
        self.store[key] = value
    def get(self, key):
        return self.store.get(key)
