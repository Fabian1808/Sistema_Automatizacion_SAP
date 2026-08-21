import tempfile
from pathlib import Path

from app.services.state_service import StateService, DocumentState, DocumentRecord


def test_create_batch_and_get_pending(tmp_path):
    svc = StateService(base_dir=tmp_path)
    batch_id = "test-batch-1"
    ids = ["1042866626", "1042866631", "1042866650"]
    svc.create_batch(batch_id, "hes", ids)

    pending = svc.get_pending(batch_id)
    assert len(pending) == 3
    assert all(d.state == DocumentState.PENDING for d in pending)


def test_mark_success_and_get_completed(tmp_path):
    svc = StateService(base_dir=tmp_path)
    batch_id = "test-batch-2"
    svc.create_batch(batch_id, "hes", ["1042866626"])
    svc.mark_processing(batch_id, "1042866626")
    test_file = tmp_path / "1042866626.pdf"
    test_file.write_bytes(b"%PDF-1.7 test content")
    svc.mark_success(batch_id, "1042866626", str(test_file), 1.5)

    completed = svc.get_completed(batch_id)
    assert len(completed) == 1
    assert completed[0].state == DocumentState.SUCCESS
    assert completed[0].duration == 1.5
    assert completed[0].file_hash != ""


def test_mark_failed(tmp_path):
    svc = StateService(base_dir=tmp_path)
    batch_id = "test-batch-3"
    svc.create_batch(batch_id, "hes", ["1042866626"])
    svc.mark_failed(batch_id, "1042866626", "HES no encontrada")

    failed = svc.get_failed(batch_id)
    assert len(failed) == 1
    assert failed[0].state == DocumentState.FAILED
    assert "HES no encontrada" in failed[0].error


def test_duplicate_detection_by_hash(tmp_path):
    svc = StateService(base_dir=tmp_path)
    batch_id = "test-batch-4"
    svc.create_batch(batch_id, "hes", ["1042866626", "1042866631"])
    test_file = tmp_path / "1042866626.pdf"
    test_file.write_bytes(b"%PDF-1.7 test content")
    svc.mark_success(batch_id, "1042866626", str(test_file), 1.0)

    duplicate = svc.find_duplicate_by_hash("dummy-hash")
    assert duplicate is None

    doc1 = svc.get_documents(batch_id, [DocumentState.SUCCESS])[0]
    duplicate2 = svc.find_duplicate_by_hash(doc1.file_hash)
    assert duplicate2 is not None
    assert duplicate2.document_id == "1042866626"


def test_skip_duplicate(tmp_path):
    svc = StateService(base_dir=tmp_path)
    batch_id = "test-batch-5"
    svc.create_batch(batch_id, "hes", ["1042866626"])
    test_file = tmp_path / "1042866626.pdf"
    test_file.write_bytes(b"%PDF-1.7 test content")
    svc.mark_success(batch_id, "1042866626", str(test_file), 1.0)

    svc.mark_skipped_duplicate(batch_id, "1042866626", str(test_file))
    docs = svc.get_documents(batch_id)
    assert len(docs) == 1
    assert docs[0].state == DocumentState.SKIPPED_DUPLICATE


def test_batch_summary(tmp_path):
    svc = StateService(base_dir=tmp_path)
    batch_id = "test-batch-6"
    svc.create_batch(batch_id, "hes", ["1", "2", "3"])
    test_file = tmp_path / "1.pdf"
    test_file.write_bytes(b"x")
    svc.mark_success(batch_id, "1", str(test_file), 1.0)
    svc.mark_failed(batch_id, "2", "error")
    svc.mark_processing(batch_id, "3")

    summary = svc.get_batch_summary(batch_id)
    assert summary["SUCCESS"] == 1
    assert summary["FAILED"] == 1
    assert summary["PROCESSING"] == 1
    assert summary["PENDING"] == 0


def test_list_batches(tmp_path):
    svc = StateService(base_dir=tmp_path)
    svc.create_batch("batch-a", "hes", ["1"])
    svc.create_batch("batch-b", "macro", ["2"])
    batches = svc.list_batches(limit=10)
    assert len(batches) == 2
    assert batches[0]["batch_id"] == "batch-b"