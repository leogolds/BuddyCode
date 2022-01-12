from common.merge import SynchronizedDocument, SynchronizedDocumentServer
from queue import SimpleQueue
from diff_match_patch import diff_match_patch


def test_SynchronizedDocument():
    c = SynchronizedDocument()
    s = SynchronizedDocument(uid=c.uid)

    # c/s._shadow == c/s._shadow == ''
    # c/s._text == c/s._text == ''
    c_text = "asdf"
    s_text = "ASDF"
    c.update_text(c_text)
    s.update_text(s_text)

    # half sync c -> s
    s.apply_patch(c.get_patch())
    assert c._text == s._shadow

    # half sync s -> c
    c.apply_patch(s.get_patch())
    assert c._text == s._text
    assert c.shadow_version == s.shadow_version

    # At this point c._text == s._text == 'asdfASDF'
    # client deletes replaces 'f' with newline
    # server adds '1234' to current text
    c.update_text("\n".join(c._text.split("f")))
    s.update_text(s._text + "1234")

    # half sync c -> s
    s.apply_patch(c.get_patch())
    assert c._text == s._shadow

    # half sync s -> c
    c.apply_patch(s.get_patch())
    assert c._text == s._text
    assert c.shadow_version == s.shadow_version


def test_SynchronizedDocumentServer():
    c1 = SynchronizedDocument()
    c2 = SynchronizedDocument(doc_id=c1.doc_id)
    s = SynchronizedDocumentServer(doc_id=c1.doc_id)

    # c/s._shadow == c/s._shadow == ''
    # c/s._text == c/s._text == ''
    c1_text = "asdf"
    c2_text = "something completely different"
    c1.update_text(c1_text)
    c2.update_text(c2_text)

    # sync c1 -> s
    s.apply_patch(c1.uid, c1.get_patch())
    c1.apply_patch(s.get_patch(c1.uid))
    # sync c2 -> s
    s.apply_patch(c2.uid, c2.get_patch())
    c2.apply_patch(s.get_patch(c2.uid))
    # as union(c1_text, c2_text) == None, best effort means shared_document == c2_text
    # c1 applies current patch to get back in sync
    c1.apply_patch(s.get_patch(c1.uid))
    # c1, c2 update their copy
    c1.update_text(c1._text + "\nasdf")
    c2.update_text(c2._text + "1234")
    s.apply_patch(c1.uid, c1.get_patch())
    c1.apply_patch(s.get_patch(c1.uid))
    s.apply_patch(c2.uid, c2.get_patch())
    c2.apply_patch(s.get_patch(c2.uid))
    # at this point, c1 is still one sync behind
    # another patch brings c1 into sync
    c1.apply_patch(s.get_patch(c1.uid))

    assert c1._text == c2._text


def test_diff_sync_simplified():
    # Implementation based on: https://neil.fraser.name/writing/sync/
    c_shadow = "asdf"
    s_shadow = "asdf"

    c_text = "asdf\nASDF"
    s_text = "asdF"

    dmp = diff_match_patch()

    c_patch = dmp.patch_make(c_shadow, c_text)
    c_shadow = c_text
    s_shadow = dmp.patch_apply(c_patch, s_shadow)[0]
    s_text = dmp.patch_apply(c_patch, s_text)[0]

    s_patch = dmp.patch_make(s_shadow, s_text)
    s_shadow = s_text
    c_shadow = dmp.patch_apply(s_patch, c_shadow)[0]
    c_text = dmp.patch_apply(s_patch, c_text)[0]
    assert c_text == s_text
    assert c_text == "asdF\nASDF"


def test_diff_sync():
    c_shadow = "asdf"
    s_shadow = "asdf"

    c_text = "asdf\nASDF"
    s_text = "asdF"

    dmp = diff_match_patch()

    # initially, s_shadow == c_shadow == c_client
    c_diff = dmp.diff_main(c_shadow, c_text)  # 1a, 1b, 2
    c_shadow = c_text  # 3
    s_shadow_patch = dmp.patch_make(s_shadow, c_diff)  # 4a, 4b
    s_shadow_update = dmp.patch_apply(s_shadow_patch, s_shadow)  # 5
    s_text_patch = dmp.patch_make(s_text, c_diff)  # 6a, 6b
    s_text_update = dmp.patch_apply(s_text_patch, s_text)  # 7
    # half sync check
    assert c_text == s_shadow_update[0]

    # c_text == s_shadow_update -> s_text_update
    s_diff = dmp.diff_main(s_shadow_update[0], s_text_update[0])
    s_shadow = s_text_update[0]
    # c_shadow == s_shadow_update
    c_shadow_patch = dmp.patch_make(c_shadow, s_diff)
    c_shadow_update = dmp.patch_apply(c_shadow_patch, s_shadow)
    # c_shadow_update == s_text_update
    # c_text == s_shadow_update
    c_text_patch = dmp.patch_make(c_text, s_diff)
    c_text_update = dmp.patch_apply(c_text_patch, c_text)
    # Check latest c/s text are synced,
    assert c_text_update[0] == s_text_update[0]

    # At this point, shadows are not synced
    c_diff = dmp.diff_main(c_shadow, c_text_update[0])  # 1a, 1b, 2
    c_shadow = c_text_update[0]  # 3
    # Now shadows are synced
    s_shadow_patch = dmp.patch_make(s_shadow, c_diff)  # 4a, 4b
    s_shadow_update = dmp.patch_apply(s_shadow_patch, s_shadow)  # 5
    s_text_patch = dmp.patch_make(s_text_update[0], c_diff)  # 6a, 6b
    s_text_update = dmp.patch_apply(s_text_patch, s_text_update[0])  # 7
    # one and a half sync check
    # all text/shadow should now be in sync
    assert c_text_update[0] == s_shadow_update[0]
    assert c_text_update[0] == s_text_update[0]
    assert c_text_update[0] == c_shadow_update[0]
