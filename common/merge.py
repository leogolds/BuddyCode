from queue import Empty, Queue
from diff_match_patch import diff_match_patch
from uuid import uuid4
from collections import defaultdict
from datetime import datetime

dmp = diff_match_patch()


class SynchronizedDocument:
    # Implementation of differential synchronization as per: https://neil.fraser.name/writing/sync/
    def __init__(
        self, doc_id: str = None, uid: str = None, initial_doc: str = ""
    ) -> None:
        self.doc_id = doc_id if doc_id else uuid4().hex
        self.uid = uid if uid else uuid4().hex
        self._shadow = initial_doc
        self._text = initial_doc
        self.shadow_version = 0
        self.patch = None

    def update_text(self, new_text):
        self._text = new_text

    def apply_patch(self, patch):
        patch = dmp.patch_fromText(patch)
        self._shadow = dmp.patch_apply(patch, self._shadow)[0]
        self.shadow_version += 1
        self._text = dmp.patch_apply(patch, self._text)[0]

    def get_patch(self):
        self.patch = dmp.patch_make(self._shadow, self._text)
        self._shadow = self._text

        return dmp.patch_toText(self.patch)


class SynchronizedDocumentServer:
    # Implementation of multiuser differential synchronization as per: https://neil.fraser.name/writing/sync/
    def __init__(self, doc_id: str = None, initial_doc: str = "") -> None:
        self.doc_id = doc_id if doc_id else uuid4.hex
        self.shared_document = initial_doc
        self.documents = {}
        self.last_accessed = datetime.now()

    def get_patch(self, uid: str):
        return self._get_document(uid).get_patch()

    def _get_document(self, uid: str) -> SynchronizedDocument:
        self.last_accessed = datetime.now()
        # return document if exists, initialize and return otherwise
        try:
            doc = self.documents[uid]
            return doc
        except KeyError:
            doc = SynchronizedDocument(
                doc_id=self.doc_id, uid=uid, initial_doc=self.shared_document
            )
            self.documents[uid] = doc
            return doc

    def apply_patch(self, uid: str, patch: str):
        self._get_document(uid).apply_patch(patch)
        self.shared_document = self.documents[uid]._text
        for doc in self.documents.values():
            doc.update_text(self.shared_document)
