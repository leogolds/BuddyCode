from pymongo import MongoClient


class DBConnector:
    def __init__(self) -> None:
        self.client = MongoClient(
            "mongodb://mongodb:27017/",
            username="root",
            password="pass12345"
            # "mongodb://localhost:27017/",
            # username="root",
            # password="pass12345",
        )
        self.db = self.client["testdb"]["test_collection"]

    def get(self, uid):
        return self.db.find_one({"uid": uid}, {"_id": 0})

    def update(self, uid, data):
        query = {"uid": uid}
        operation = {"$set": {"code_window": data}}
        self.db.update_one(query, operation, upsert=True)
