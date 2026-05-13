import asyncio
import os
import pytest
from backend.desktop.file_manager import file_manager
from backend.desktop.context_manager import context_manager
from backend.core.task_manager import background_agent
from backend.memory.database import get_connection

@pytest.mark.asyncio
async def test_file_indexing_and_search():
    """Validates filesystem indexing stability and search correctness."""
    test_file = os.path.abspath("workspace/test_index.txt")
    with open(test_file, "w") as f:
        f.write("This is a test document for FRIDAY file intelligence.")
    
    # Trigger manual index
    await file_manager.index_file(test_file)
    
    # Search metadata
    results = file_manager.search_files("test_index")
    assert len(results) > 0
    assert results[0]['name'] == "test_index.txt"
    
    # Cleanup
    os.remove(test_file)

@pytest.mark.asyncio
async def test_audit_logging():
    """Validates audit logging correctness."""
    event_name = "TEST_EVENT"
    background_agent.audit_log(event_name, "test_component", {"key": "value"})
    
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM system_audit_log WHERE event = ?", (event_name,))
        row = cursor.fetchone()
        assert row is not None
        assert row['component'] == "test_component"
    finally:
        conn.close()

@pytest.mark.asyncio
async def test_context_retrieval():
    """Validates window tracking and clipboard access."""
    window = context_manager.get_active_window()
    assert isinstance(window, str)
    
    clipboard = context_manager.get_clipboard_content()
    # Might be None or string depending on env, but should not crash
    assert clipboard is None or isinstance(clipboard, str)

@pytest.mark.asyncio
async def test_background_task_persistence():
    """Validates task queue recovery."""
    task_id = "test_task_123"
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO background_tasks (id, name, status, scheduled_at) VALUES (?, ?, ?, ?)",
            (task_id, "Persistence Test", "pending", "2020-01-01T00:00:00")
        )
        conn.commit()
    finally:
        conn.close()
    
    # Run one recovery cycle
    await background_agent._recover_and_process_tasks()
    
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM background_tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        assert row['status'] == 'completed'
    finally:
        conn.close()
