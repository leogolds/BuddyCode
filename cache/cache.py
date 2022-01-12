from pymongo import mongo_client
from common.merge import SynchronizedDocumentServer
from mongo_connector import DBConnector
from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every
from pydantic import BaseModel
from queue import Queue, SimpleQueue
from collections import defaultdict
from fastapi.responses import PlainTextResponse
from fastapi.logger import logger
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta

import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

log.error("starting")

q = SimpleQueue()
db = DBConnector()


class Item(BaseModel):
    patch: str
    uid: str


app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def get_latest_data(doc_id: str):
    return PlainTextResponse(
        cache.get_document_server(doc_id).shared_document,
    )


@app.post("/")
async def post_update(doc_id: str, item: Item):
    server = cache.get_document_server(doc_id)
    server.apply_patch(uid=item.uid, patch=item.patch)

    return PlainTextResponse(
        server.get_patch(item.uid),
    )


class SynchronizedCache:
    def __init__(self) -> None:
        self.cache = {}
        self.work_queue = defaultdict(SimpleQueue)
        self.document_servers = {}

    def get_document_server(self, doc_id: str) -> SynchronizedDocumentServer:
        try:
            server = self.document_servers[doc_id]
            return server
        except KeyError:
            base = db.get(doc_id)
            initial_doc = base["code_window"] if base else ""
            server = SynchronizedDocumentServer(doc_id=doc_id, initial_doc=initial_doc)
            self.document_servers[doc_id] = server
            return server


cache = SynchronizedCache()


@app.on_event("startup")
@repeat_every(seconds=120)
def update_db_and_cleanup_cache():
    """dump up to date documents to db and cleanup stale (last access > 10 minutes) cache records"""
    now = datetime.now
    log.error(f"{now()}: updating db")
    cleanup = []

    for doc_id, document in cache.document_servers.items():
        db.update(doc_id, document.shared_document)
        if document.last_accessed + timedelta(minutes=10) > now():
            cleanup.append(doc_id)

    log.error(
        f"{now()}: finished updating db with {len(cache.document_servers)} documents"
    )
    log.error(f"{now()}: cleaning up {len(cleanup)} stale records")

    for doc_id in cleanup:
        del cache.document_servers[doc_id]

    log.error(
        f"{now()}: finished cleaning with {len(cache.document_servers)} active documents"
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9000)
