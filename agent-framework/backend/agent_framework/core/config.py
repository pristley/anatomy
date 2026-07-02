import os

class Config:
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./dev.db")
