import pytest
from fastapi.testclient import TestClient

from week2.app.main import app
from week2.tests.test_extract import _ollama_available

client = TestClient(app)


def test_extract_and_mark_done():
    response = client.post(
        "/action-items/extract",
        json={"text": "- [ ] Test task", "save_note": False},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1

    item_id = data["items"][0]["id"]
    done_response = client.post(f"/action-items/{item_id}/done", json={"done": True})
    assert done_response.status_code == 200
    assert done_response.json()["done"] is True


def test_create_and_get_note():
    response = client.post("/notes", json={"content": "hello note"})
    assert response.status_code == 201
    note_id = response.json()["id"]

    get_response = client.get(f"/notes/{note_id}")
    assert get_response.status_code == 200
    assert get_response.json()["content"] == "hello note"


def test_extract_rejects_blank_text():
    response = client.post("/action-items/extract", json={"text": "   "})
    assert response.status_code == 422


@pytest.mark.skipif(
    not _ollama_available(),
    reason="Ollama is not running; start it or set OLLAMA_HOST",
)
def test_extract_llm_endpoint():
    response = client.post(
        "/action-items/extract-llm",
        json={"text": "- [ ] Deploy staging", "save_note": False},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) >= 1


def test_list_notes():
    client.post("/notes", json={"content": "first note"})
    client.post("/notes", json={"content": "second note"})

    response = client.get("/notes")
    assert response.status_code == 200
    notes = response.json()
    assert len(notes) >= 2
    contents = {note["content"] for note in notes}
    assert "first note" in contents
    assert "second note" in contents
