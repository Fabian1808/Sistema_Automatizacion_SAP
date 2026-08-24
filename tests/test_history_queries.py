import sqlite3

from sap_document_automation.services.state_service import StateService


def test_create_batch_stores_username_and_running_status(tmp_path):
    svc = StateService(base_dir=tmp_path)
    svc.create_batch("b1", "hes", ["1", "2"], username="usuarioTI")
    batch = svc.get_batch("b1")
    assert batch["username"] == "usuarioTI"
    assert batch["status"] == "RUNNING"


def test_set_batch_status_roundtrip(tmp_path):
    svc = StateService(base_dir=tmp_path)
    svc.create_batch("b1", "hes", ["1"])
    svc.set_batch_status("b1", "PARTIAL")
    assert svc.get_batch("b1")["status"] == "PARTIAL"
    assert svc.get_batch("b1")["finished_at"] != ""
    svc.set_batch_status("b1", "RUNNING")
    assert svc.get_batch("b1")["finished_at"] == ""


def test_list_batches_returns_counts_and_pagination(tmp_path):
    svc = StateService(base_dir=tmp_path)
    for i in range(3):
        batch_id = f"b{i}"
        svc.create_batch(batch_id, "hes", [f"d{i}a", f"d{i}b"])
        svc.mark_success(batch_id, f"d{i}a", "", 1.0)
        svc.mark_failed(batch_id, f"d{i}b", "boom")

    rows = svc.list_batches(limit=2, offset=0)
    assert len(rows) == 2
    first = rows[0]
    assert first["ok_count"] == 1
    assert first["failed_count"] == 1
    assert first["total_duration"] >= 1.0
    page2 = svc.list_batches(limit=2, offset=2)
    assert len(page2) == 1
    assert svc.count_batches() == 3


def test_migration_adds_columns_to_legacy_database(tmp_path):
    db_path = tmp_path / "batches.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE batches (
                batch_id TEXT PRIMARY KEY,
                module_id TEXT NOT NULL,
                total_documents INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                config_snapshot TEXT
            )
            """
        )
        conn.execute(
            "INSERT INTO batches VALUES ('legacy', 'hes', 1, 't', 't', '{}')"
        )
    # Abrir con el servicio debe migrar sin borrar datos
    svc = StateService(base_dir=tmp_path)
    legacy = svc.get_batch("legacy")
    assert legacy is not None
    assert legacy["username"] == ""
    assert legacy["status"] == ""
    svc.set_batch_status("legacy", "COMPLETED")
    assert svc.get_batch("legacy")["status"] == "COMPLETED"
