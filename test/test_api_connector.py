from common.merge import SynchronizedDocument
import uuid
from editor.api_connector import APIConnector
from time import sleep

api = APIConnector()


def test_empty_document():
    doc_id = uuid.uuid4().hex
    base = api.get_document(doc_id)

    assert base == ""


def test_update_document():
    c1 = SynchronizedDocument()

    c1.update_text("asdf")
    api.post_update(doc_id=c1.doc_id, uid=c1.uid, patch=c1.get_patch())

    result = api.get_document(c1.doc_id)

    assert result == c1._text


def test_multiuser_update_document():
    # c1 creating a new document
    c1 = SynchronizedDocument()
    c1.update_text("asdf")
    server_patch = api.post_update(doc_id=c1.doc_id, uid=c1.uid, patch=c1.get_patch())
    # as we have only one user contributing, the server patch should be empty
    assert server_patch == ""

    # c2 joins
    c2 = SynchronizedDocument(
        doc_id=c1.doc_id, initial_doc=api.get_document(doc_id=c1.doc_id)
    )
    assert c1._text == c2._text

    # c2 updates it's document and posts an update
    c2.update_text(c2._text + "\n1234")
    c2_patch = c2.get_patch()
    server_patch = api.post_update(doc_id=c2.doc_id, uid=c2.uid, patch=c2_patch)
    c2.apply_patch(server_patch)

    # c1 hasn't updated it's document so c1_patch is empty
    # c1 applies server patch and is in sync with c2
    c1_patch = c1.get_patch()
    assert c1_patch == ""
    server_patch2 = api.post_update(doc_id=c1.doc_id, uid=c1.uid, patch=c1_patch)
    c1.apply_patch(server_patch2)

    assert c2._text == c1._text
