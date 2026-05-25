# Week 2 Write-up

Tip: To preview this markdown file

- On Mac, press `Command (⌘) + Shift + V`
- On Windows/Linux, press `Ctrl + Shift + V`

## INSTRUCTIONS

Fill out all of the `TODO`s in this file.

## YOUR RESPONSES

For each exercise, please include what prompts you used to generate the answer, in addition to the location of the generated response. Make sure to clearly add comments in your code documenting which parts are generated.

### Exercise 1: Scaffold a New Feature

Prompt:

```text
你是一个python软件开发者。当前文件在项目里用于提取action item
请分析extract_action_items()这个函数作为参考。
修改要求：实现基于LLM的提取方式，函数名为extract_action_items_llm()。
使用Ollama中的模型，避免使用较大模型。
输出为JSON格式，可以以 https://ollama.com/blog/structured-outputs 这个网站为参考.
可选模型可参考 https://ollama.com/library。
```

Generated Code Snippets:

```git
# TODO: List all modified code files with the relevant line numbers.
 import os
 import re
 from typing import List
-import json
-from typing import Any
-from ollama import chat
+
 from dotenv import load_dotenv
+from ollama import Client
+from pydantic import BaseModel, Field

 load_dotenv()

+# Small, efficient model suitable for structured extraction (see https://ollama.com/library).
+DEFAULT_OLLAMA_MODEL = "llama3.2:3b"
+DEFAULT_OLLAMA_HOST = "http://localhost:11434"
+
+# trust_env=False avoids routing local requests through a system HTTP proxy (502 on Windows).
+_ollama_client = Client(
+    host=os.getenv("OLLAMA_HOST", DEFAULT_OLLAMA_HOST),
+    trust_env=False,
+)
+
+
+class ActionItemsResponse(BaseModel):
+    """JSON schema for Ollama structured output: array of action item strings."""
+
+    action_items: list[str] = Field(
+        description="Action items extracted from the notes, without bullet markers or checkboxes."
+    )
+
 BULLET_PREFIX_PATTERN = re.compile(r"^\s*([-*•]|\d+\.)\s+")
 KEYWORD_PREFIXES = (
     "todo:",
@@ -87,3 +105,49 @@ def _looks_imperative(sentence: str) -> bool:
         "investigate",
     }
     return first.lower() in imperative_starters
+
+
+def extract_action_items_llm(text: str) -> List[str]:
+    """Extract action items from free-form notes using an Ollama LLM with structured JSON output."""
+    stripped = text.strip()
+    if not stripped:
+        return []
+
+    model = os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)
+
+    response = _ollama_client.chat(
+        model=model,
+        messages=[
+            {
+                "role": "system",
+                "content": (
+                    "You extract actionable tasks from meeting notes and to-do lists. "
+                    "Return each item as a concise imperative phrase. "
+                    "Ignore narrative text that is not an action item. "
+                    "Return as JSON."
+                ),
+            },
+            {
+                "role": "user",
+                "content": stripped,
+            },
+        ],
+        format=ActionItemsResponse.model_json_schema(),
+        options={"temperature": 0},
+    )
+
+    parsed = ActionItemsResponse.model_validate_json(response.message.content)
+
+    # Deduplicate while preserving order (same behavior as extract_action_items).
+    seen: set[str] = set()
+    unique: List[str] = []
+    for item in parsed.action_items:
+        cleaned = item.strip()
+        if not cleaned:
+            continue
+        lowered = cleaned.lower()
+        if lowered in seen:
+            continue
+        seen.add(lowered)
+        unique.append(cleaned)
+    return unique

```

### Exercise 2: Add Unit Tests

Prompt:

```text
你是一名python软件开发者。接下来，为extract_action_items_llm()函数编写单元测试。
测试包含以下情况：bullet lists, keyword-prefixed lines, empty input。
测试脚本代码文件为week2/tests/test_extract.py。
如果测试结果有误，请根据报错进行进一步调整。
```

Generated Code Snippets:

```git
 import os
+
+import httpx
 import pytest

-from ..app.services.extract import extract_action_items
+from ..app.services.extract import extract_action_items, extract_action_items_llm
+
+
+def _ollama_available() -> bool:
+    """Return True when the local Ollama server responds."""
+    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
+    try:
+        response = httpx.get(f"{host.rstrip('/')}/api/tags", timeout=5.0, trust_env=False)
+        return response.status_code == 200
+    except (httpx.HTTPError, OSError):
+        return False
+
+
+def _assert_contains_item(items: list[str], expected: str) -> None:
+    """Match action items case-insensitively (LLM wording may vary slightly)."""
+    needle = expected.lower()
+    assert any(needle in item.lower() for item in items), (
+        f"Expected an item containing {expected!r}, got {items!r}"
+    )


 def test_extract_bullets_and_checkboxes():
@@ -17,3 +37,50 @@ def test_extract_bullets_and_checkboxes():
     assert "Set up database" in items
     assert "implement API extract endpoint" in items
     assert "Write tests" in items
+
+
+def test_extract_action_items_llm_empty_input():
+    assert extract_action_items_llm("") == []
+    assert extract_action_items_llm("   \n\t  ") == []
+
+
+@pytest.mark.skipif(
+    not _ollama_available(),
+    reason="Ollama is not running; start it or set OLLAMA_HOST",
+)
+def test_extract_action_items_llm_bullet_list():
+    text = """
+    Sprint notes:
+    - [ ] Set up database
+    * implement API extract endpoint
+    1. Write tests
+    We discussed timelines but no decision yet.
+    """.strip()
+
+    items = extract_action_items_llm(text)
+
+    assert len(items) >= 3
+    _assert_contains_item(items, "database")
+    _assert_contains_item(items, "API")
+    _assert_contains_item(items, "tests")
+
+
+@pytest.mark.skipif(
+    not _ollama_available(),
+    reason="Ollama is not running; start it or set OLLAMA_HOST",
+)
+def test_extract_action_items_llm_keyword_prefixed_lines():
+    text = """
+    Standup:
+    TODO: Review pull request
+    action: Deploy staging environment
+    next: Schedule retrospective
+    General discussion only.
+    """.strip()
+
+    items = extract_action_items_llm(text)
+
+    assert len(items) >= 3
+    _assert_contains_item(items, "pull request")
+    _assert_contains_item(items, "staging")
+    _assert_contains_item(items, "retrospective")

```

### Exercise 3: Refactor Existing Code for Clarity

Prompt:

```text
你是一名python软件开发者。
请重构后端的代码, 特别侧重于定义明确的 API 契约/架构、数据库层清理、应用生命周期/配置，以及错误处理。
要求保证代码清晰整洁。
```

Generated/Modified Code Snippets:

```git
diff --git a/week2/app/db.py b/week2/app/db.py
deleted file mode 100644
index 40f2385..0000000
--- a/week2/app/db.py
+++ /dev/null
@@ -1,116 +0,0 @@
-from __future__ import annotations
-
-import sqlite3
-from pathlib import Path
-from typing import Optional
-
-
--- a/week2/app/db.py
+++ /dev/null
@@ -1,116 +0,0 @@
-from __future__ import annotations
-
-import sqlite3
-from pathlib import Path
-from typing import Optional
-
-
-BASE_DIR = Path(__file__).resolve().parents[1]
-DATA_DIR = BASE_DIR / "data"
-DB_PATH = DATA_DIR / "app.db"
-
-
-def ensure_data_directory_exists() -> None:
-    DATA_DIR.mkdir(parents=True, exist_ok=True)
-
-
-def get_connection() -> sqlite3.Connection:
-    ensure_data_directory_exists()
-    connection = sqlite3.connect(DB_PATH)
-    connection.row_factory = sqlite3.Row
-    return connection
-
-
-def init_db() -> None:
-    ensure_data_directory_exists()
-    with get_connection() as connection:
-        cursor = connection.cursor()
-        cursor.execute(
-            """
-            CREATE TABLE IF NOT EXISTS notes (
-                id INTEGER PRIMARY KEY AUTOINCREMENT,
-                content TEXT NOT NULL,
-                created_at TEXT DEFAULT (datetime('now'))
-            );
-            """
-        )
-        cursor.execute(
-            """
-            CREATE TABLE IF NOT EXISTS action_items (
-                id INTEGER PRIMARY KEY AUTOINCREMENT,
-                note_id INTEGER,
-                text TEXT NOT NULL,
-                done INTEGER DEFAULT 0,
-                created_at TEXT DEFAULT (datetime('now')),
-                FOREIGN KEY (note_id) REFERENCES notes(id)
-            );
-            """
-        )
-        connection.commit()
-
-
-def insert_note(content: str) -> int:
-    with get_connection() as connection:
-        cursor = connection.cursor()
-        cursor.execute("INSERT INTO notes (content) VALUES (?)", (content,))
-        connection.commit()
-        return int(cursor.lastrowid)
-
-
-def list_notes() -> list[sqlite3.Row]:
-    with get_connection() as connection:
-        cursor = connection.cursor()
-        cursor.execute("SELECT id, content, created_at FROM notes ORDER BY id DESC")
-        return list(cursor.fetchall())
-
-
-def get_note(note_id: int) -> Optional[sqlite3.Row]:
-    with get_connection() as connection:
-        cursor = connection.cursor()
-        cursor.execute(
-            "SELECT id, content, created_at FROM notes WHERE id = ?",
-            (note_id,),
-        )
-        row = cursor.fetchone()
-        return row
-
-
-def insert_action_items(items: list[str], note_id: Optional[int] = None) -> list[int]:
-    with get_connection() as connection:
-        cursor = connection.cursor()
-        ids: list[int] = []
-        for item in items:
-            cursor.execute(
-                "INSERT INTO action_items (note_id, text) VALUES (?, ?)",
-                (note_id, item),
-            )
-            ids.append(int(cursor.lastrowid))
-        connection.commit()
-        return ids
-
-
-def list_action_items(note_id: Optional[int] = None) -> list[sqlite3.Row]:
-    with get_connection() as connection:
-        cursor = connection.cursor()
-        if note_id is None:
-            cursor.execute(
-                "SELECT id, note_id, text, done, created_at FROM action_items ORDER BY id DESC"
-            )
-        else:
-            cursor.execute(
-                "SELECT id, note_id, text, done, created_at FROM action_items WHERE note_id = ? ORDER BY id DESC",
-                (note_id,),
-            )
-        return list(cursor.fetchall())
-
-
-def mark_action_item_done(action_item_id: int, done: bool) -> None:
-    with get_connection() as connection:
-        cursor = connection.cursor()
-        cursor.execute(
-            "UPDATE action_items SET done = ? WHERE id = ?",
-            (1 if done else 0, action_item_id),
-        )
-        connection.commit()
-
-
diff --git a/week2/app/main.py b/week2/app/main.py
index 6a3315e..3e23b41 100644
--- a/week2/app/main.py
+++ b/week2/app/main.py
@@ -1,30 +1,73 @@
 from __future__ import annotations

-from pathlib import Path
-from typing import Any, Dict, Optional
+from contextlib import asynccontextmanager
+from typing import AsyncIterator

-from fastapi import FastAPI, HTTPException
-from fastapi.responses import HTMLResponse
+from fastapi import FastAPI, Request
+from fastapi.exceptions import RequestValidationError
+from fastapi.responses import HTMLResponse, JSONResponse
 from fastapi.staticfiles import StaticFiles

-from .db import init_db
+from .config import get_settings
+from .database import init_db
+from .exceptions import AppError, NotFoundError, ValidationError
 from .routers import action_items, notes
-from . import db
+from .schemas import ErrorResponse

-init_db()

-app = FastAPI(title="Action Item Extractor")
+@asynccontextmanager
+async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
+    init_db()
+    yield
+
+
+app = FastAPI(title="Action Item Extractor", lifespan=lifespan)
+
+
+@app.exception_handler(NotFoundError)
+async def not_found_handler(_request: Request, exc: NotFoundError) -> JSONResponse:
+    return JSONResponse(
+        status_code=404,
+        content=ErrorResponse(detail=str(exc)).model_dump(),
+    )
+
+
+@app.exception_handler(ValidationError)
+async def validation_error_handler(_request: Request, exc: ValidationError) -> JSONResponse:
+    return JSONResponse(
+        status_code=400,
+        content=ErrorResponse(detail=str(exc)).model_dump(),
+    )
+
+
+@app.exception_handler(AppError)
+async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
+    return JSONResponse(
+        status_code=500,
+        content=ErrorResponse(detail=str(exc)).model_dump(),
+    )
+
+
+@app.exception_handler(RequestValidationError)
+async def request_validation_handler(
+    _request: Request, exc: RequestValidationError
+) -> JSONResponse:
+    errors = exc.errors()
+    detail = errors[0]["msg"] if errors else "Invalid request."
+    return JSONResponse(
+        status_code=422,
+        content=ErrorResponse(detail=detail).model_dump(),
+    )


 @app.get("/", response_class=HTMLResponse)
 def index() -> str:
-    html_path = Path(__file__).resolve().parents[1] / "frontend" / "index.html"
-    return html_path.read_text(encoding="utf-8")
+    settings = get_settings()
+    return (settings.frontend_dir / "index.html").read_text(encoding="utf-8")


 app.include_router(notes.router)
 app.include_router(action_items.router)

-
-static_dir = Path(__file__).resolve().parents[1] / "frontend"
-app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
\ No newline at end of file
+settings = get_settings()
+app.mount("/static", StaticFiles(directory=str(settings.frontend_dir)), name="static")
diff --git a/week2/app/routers/action_items.py b/week2/app/routers/action_items.py
index 38a03ea..edc2242 100644
--- a/week2/app/routers/action_items.py
+++ b/week2/app/routers/action_items.py
@@ -1,50 +1,55 @@
 from __future__ import annotations

-from typing import Any, Dict, List, Optional
-
-from fastapi import APIRouter, HTTPException
-
-from .. import db
+from typing import Optional
+
+from fastapi import APIRouter, Query
+
+from ..database import insert_action_items, insert_note, list_action_items, mark_action_item_done
+from ..schemas import (
+    ActionItemDetailResponse,
+    ActionItemResponse,
+    ExtractActionItemsRequest,
+    ExtractActionItemsResponse,
+    MarkActionItemDoneRequest,
+    MarkActionItemDoneResponse,
+)
 from ..services.extract import extract_action_items

-
 router = APIRouter(prefix="/action-items", tags=["action-items"])


-@router.post("/extract")
-def extract(payload: Dict[str, Any]) -> Dict[str, Any]:
-    text = str(payload.get("text", "")).strip()
-    if not text:
-        raise HTTPException(status_code=400, detail="text is required")
-
+@router.post("/extract", response_model=ExtractActionItemsResponse)
+def extract(body: ExtractActionItemsRequest) -> ExtractActionItemsResponse:
+    text = body.text.strip()
     note_id: Optional[int] = None
-    if payload.get("save_note"):
-        note_id = db.insert_note(text)
+    if body.save_note:
+        note = insert_note(text)
+        note_id = note.id

     items = extract_action_items(text)
-    ids = db.insert_action_items(items, note_id=note_id)
-    return {"note_id": note_id, "items": [{"id": i, "text": t} for i, t in zip(ids, items)]}
+    saved = insert_action_items(items, note_id=note_id)
+    return ExtractActionItemsResponse(
+        note_id=note_id,
+        items=[ActionItemResponse(id=item.id, text=item.text) for item in saved],
+    )


-@router.get("")
-def list_all(note_id: Optional[int] = None) -> List[Dict[str, Any]]:
-    rows = db.list_action_items(note_id=note_id)
+@router.get("", response_model=list[ActionItemDetailResponse])
+def list_all(note_id: Optional[int] = Query(default=None)) -> list[ActionItemDetailResponse]:
+    rows = list_action_items(note_id=note_id)
     return [
-        {
-            "id": r["id"],
-            "note_id": r["note_id"],
-            "text": r["text"],
-            "done": bool(r["done"]),
-            "created_at": r["created_at"],
-        }
-        for r in rows
+        ActionItemDetailResponse(
+            id=row.id,
+            note_id=row.note_id,
+            text=row.text,
+            done=row.done,
+            created_at=row.created_at,
+        )
+        for row in rows
     ]


-@router.post("/{action_item_id}/done")
-def mark_done(action_item_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
-    done = bool(payload.get("done", True))
-    db.mark_action_item_done(action_item_id, done)
-    return {"id": action_item_id, "done": done}
-
-
+@router.post("/{action_item_id}/done", response_model=MarkActionItemDoneResponse)
+def mark_done(action_item_id: int, body: MarkActionItemDoneRequest) -> MarkActionItemDoneResponse:
+    updated = mark_action_item_done(action_item_id, body.done)
+    return MarkActionItemDoneResponse(id=updated.id, done=updated.done)
diff --git a/week2/app/routers/notes.py b/week2/app/routers/notes.py
index 292c754..95fd71b 100644
--- a/week2/app/routers/notes.py
+++ b/week2/app/routers/notes.py
@@ -1,34 +1,20 @@
 from __future__ import annotations

-from typing import Any, Dict, List
-
-from fastapi import APIRouter, HTTPException
-
-from .. import db
+from fastapi import APIRouter

+from ..database import insert_note, require_note
+from ..schemas import CreateNoteRequest, NoteResponse

 router = APIRouter(prefix="/notes", tags=["notes"])


-@router.post("")
-def create_note(payload: Dict[str, Any]) -> Dict[str, Any]:
-    content = str(payload.get("content", "")).strip()
-    if not content:
-        raise HTTPException(status_code=400, detail="content is required")
-    note_id = db.insert_note(content)
-    note = db.get_note(note_id)
-    return {
-        "id": note["id"],
-        "content": note["content"],
-        "created_at": note["created_at"],
-    }
-
-
-@router.get("/{note_id}")
-def get_single_note(note_id: int) -> Dict[str, Any]:
-    row = db.get_note(note_id)
-    if row is None:
-        raise HTTPException(status_code=404, detail="note not found")
-    return {"id": row["id"], "content": row["content"], "created_at": row["created_at"]}
+@router.post("", response_model=NoteResponse, status_code=201)
+def create_note(body: CreateNoteRequest) -> NoteResponse:
+    note = insert_note(body.content.strip())
+    return NoteResponse(id=note.id, content=note.content, created_at=note.created_at)


+@router.get("/{note_id}", response_model=NoteResponse)
+def get_single_note(note_id: int) -> NoteResponse:
+    note = require_note(note_id)
+    return NoteResponse(id=note.id, content=note.content, created_at=note.created_at)

```

### Exercise 4: Use Agentic Mode to Automate a Small Task

Prompt:

```text
你是一名python软件开发者。
接下来，将LLM驱动的提取器集成到软件上作为新的endpoint。
更新前端文件使页面多出一个"Extract LLM"的按钮，按下它可以调用LLM驱动的endpoint。
同时暴露一个endpoint用来取回所有notes。
更新前端文件是页面多出一个“List Notes”按钮，按下它可以取回所有notes并且在页面上展现它们
```

Generated Code Snippets:

```git
diff --git a/week2/app/routers/action_items.py b/week2/app/routers/action_items.py
index edc2242..b967abd 100644
--- a/week2/app/routers/action_items.py
+++ b/week2/app/routers/action_items.py
@@ -2,7 +2,8 @@ from __future__ import annotations

 from typing import Optional

-from fastapi import APIRouter, Query
+from fastapi import APIRouter, HTTPException, Query
+from ollama import ResponseError

 from ..database import insert_action_items, insert_note, list_action_items, mark_action_item_done
 from ..schemas import (
@@ -13,7 +14,7 @@ from ..schemas import (
     MarkActionItemDoneRequest,
     MarkActionItemDoneResponse,
 )
-from ..services.extract import extract_action_items
+from ..services.extract import extract_action_items, extract_action_items_llm

 router = APIRouter(prefix="/action-items", tags=["action-items"])

@@ -34,6 +35,29 @@ def extract(body: ExtractActionItemsRequest) -> ExtractActionItemsResponse:
     )


+@router.post("/extract-llm", response_model=ExtractActionItemsResponse)
+def extract_llm(body: ExtractActionItemsRequest) -> ExtractActionItemsResponse:
+    text = body.text.strip()
+    note_id: Optional[int] = None
+    if body.save_note:
+        note = insert_note(text)
+        note_id = note.id
+
+    try:
+        items = extract_action_items_llm(text)
+    except ResponseError as exc:
+        raise HTTPException(
+            status_code=503,
+            detail="Ollama is unavailable. Ensure Ollama is running and the model is pulled.",
+        ) from exc
+
+    saved = insert_action_items(items, note_id=note_id)
+    return ExtractActionItemsResponse(
+        note_id=note_id,
+        items=[ActionItemResponse(id=item.id, text=item.text) for item in saved],
+    )
+
+
 @router.get("", response_model=list[ActionItemDetailResponse])
 def list_all(note_id: Optional[int] = Query(default=None)) -> list[ActionItemDetailResponse]:
     rows = list_action_items(note_id=note_id)
diff --git a/week2/app/routers/notes.py b/week2/app/routers/notes.py
index 95fd71b..de1ea7a 100644
--- a/week2/app/routers/notes.py
+++ b/week2/app/routers/notes.py
@@ -2,12 +2,20 @@ from __future__ import annotations

 from fastapi import APIRouter

-from ..database import insert_note, require_note
+from ..database import insert_note, list_notes, require_note
 from ..schemas import CreateNoteRequest, NoteResponse

 router = APIRouter(prefix="/notes", tags=["notes"])


+@router.get("", response_model=list[NoteResponse])
+def list_all_notes() -> list[NoteResponse]:
+    return [
+        NoteResponse(id=note.id, content=note.content, created_at=note.created_at)
+        for note in list_notes()
+    ]
+
+
 @router.post("", response_model=NoteResponse, status_code=201)
 def create_note(body: CreateNoteRequest) -> NoteResponse:
     note = insert_note(body.content.strip())
diff --git a/week2/frontend/index.html b/week2/frontend/index.html
index 1ace101..8292af4 100644
--- a/week2/frontend/index.html
+++ b/week2/frontend/index.html
@@ -7,12 +7,16 @@
     <style>
       body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, sans-serif; margin: 2rem auto; max-width: 800px; padding: 0 1rem; }
       h1 { font-size: 1.5rem; }
+      h2 { font-size: 1.125rem; margin-top: 1.5rem; }
       textarea { width: 100%; min-height: 160px; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, Liberation Mono, monospace; }
       button { padding: 0.5rem 1rem; }
-      .items { margin-top: 1rem; }
+      .items, .notes { margin-top: 1rem; }
       .item { display: flex; align-items: center; gap: 0.5rem; padding: 0.25rem 0; }
+      .note { border: 1px solid #e5e7eb; border-radius: 0.375rem; padding: 0.75rem; margin-bottom: 0.75rem; }
+      .note-meta { color: #6b7280; font-size: 0.875rem; margin-bottom: 0.5rem; }
+      .note-content { white-space: pre-wrap; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, Liberation Mono, monospace; font-size: 0.875rem; }
       .muted { color: #6b7280; font-size: 0.875rem; }
-      .row { display: flex; gap: 0.5rem; align-items: center; }
+      .row { display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap; }
     </style>
   </head>
   <body>
@@ -24,51 +28,104 @@
     <div class="row">
       <label class="row"><input id="save_note" type="checkbox" checked /> Save as note</label>
       <button id="extract">Extract</button>
+      <button id="extract-llm">Extract LLM</button>
+      <button id="list-notes" type="button">List Notes</button>
     </div>

     <div class="items" id="items"></div>

+    <h2>Saved Notes</h2>
+    <div class="notes" id="notes">
+      <p class="muted">Click "List Notes" to load saved notes.</p>
+    </div>
+
     <script>
       const $ = (sel) => document.querySelector(sel);
       const itemsEl = $('#items');
-      const btn = $('#extract');
-      btn.addEventListener('click', async () => {
+      const notesEl = $('#notes');
+
+      function escapeHtml(text) {
+        return text
+          .replace(/&/g, '&amp;')
+          .replace(/</g, '&lt;')
+          .replace(/>/g, '&gt;')
+          .replace(/"/g, '&quot;');
+      }
+
+      function renderActionItems(items) {
+        if (!items || items.length === 0) {
+          itemsEl.innerHTML = '<p class="muted">No action items found.</p>';
+          return;
+        }
+        itemsEl.innerHTML = items.map((it) => (
+          `<div class="item"><input type="checkbox" data-id="${it.id}" /> <span>${escapeHtml(it.text)}</span></div>`
+        )).join('');
+        itemsEl.querySelectorAll('input[type="checkbox"]').forEach((cb) => {
+          cb.addEventListener('change', async (e) => {
+            const id = e.target.getAttribute('data-id');
+            await fetch(`/action-items/${id}/done`, {
+              method: 'POST',
+              headers: { 'Content-Type': 'application/json' },
+              body: JSON.stringify({ done: e.target.checked }),
+            });
+          });
+        });
+      }
+
+      async function runExtract(endpoint, loadingMessage) {
         const text = $('#text').value;
         const save = $('#save_note').checked;
-        itemsEl.textContent = 'Extracting...';
+        itemsEl.textContent = loadingMessage;
         try {
-          const res = await fetch('/action-items/extract', {
+          const res = await fetch(endpoint, {
             method: 'POST',
             headers: { 'Content-Type': 'application/json' },
             body: JSON.stringify({ text, save_note: save }),
           });
-          if (!res.ok) throw new Error('Request failed');
+          if (!res.ok) {
+            const err = await res.json().catch(() => ({}));
+            throw new Error(err.detail || 'Request failed');
+          }
           const data = await res.json();
-          if (!data.items || data.items.length === 0) {
-            itemsEl.innerHTML = '<p class="muted">No action items found.</p>';
+          renderActionItems(data.items);
+        } catch (err) {
+          console.error(err);
+          itemsEl.textContent = err.message || 'Error extracting items';
+        }
+      }
+
+      $('#extract').addEventListener('click', () => {
+        runExtract('/action-items/extract', 'Extracting...');
+      });
+
+      $('#extract-llm').addEventListener('click', () => {
+        runExtract('/action-items/extract-llm', 'Extracting with LLM...');
+      });
+
+      $('#list-notes').addEventListener('click', async () => {
+        notesEl.textContent = 'Loading notes...';
+        try {
+          const res = await fetch('/notes');
+          if (!res.ok) {
+            const err = await res.json().catch(() => ({}));
+            throw new Error(err.detail || 'Request failed');
+          }
+          const notes = await res.json();
+          if (!notes.length) {
+            notesEl.innerHTML = '<p class="muted">No notes saved yet.</p>';
             return;
           }
-          itemsEl.innerHTML = data.items.map(it => (
-            `<div class="item"><input type="checkbox" data-id="${it.id}" /> <span>${it.text}</span></div>`
+          notesEl.innerHTML = notes.map((note) => (
+            `<article class="note">
+              <div class="note-meta">#${note.id} · ${escapeHtml(note.created_at)}</div>
+              <div class="note-content">${escapeHtml(note.content)}</div>
+            </article>`
           )).join('');
-          itemsEl.querySelectorAll('input[type="checkbox"]').forEach(cb => {
-            cb.addEventListener('change', async (e) => {
-              const id = e.target.getAttribute('data-id');
-              await fetch(`/action-items/${id}/done`, {
-                method: 'POST',
-                headers: { 'Content-Type': 'application/json' },
-                body: JSON.stringify({ done: e.target.checked }),
-              });
-            });
-          });
         } catch (err) {
           console.error(err);
-          itemsEl.textContent = 'Error extracting items';
+          notesEl.textContent = err.message || 'Error loading notes';
         }
       });
-
     </script>
   </body>
   </html>
-
-
diff --git a/week2/tests/test_api_smoke.py b/week2/tests/test_api_smoke.py
index 8983085..d285a5a 100644
--- a/week2/tests/test_api_smoke.py
+++ b/week2/tests/test_api_smoke.py
@@ -1,6 +1,8 @@
+import pytest
 from fastapi.testclient import TestClient

 from week2.app.main import app
+from week2.tests.test_extract import _ollama_available

 client = TestClient(app)

@@ -33,3 +35,30 @@ def test_create_and_get_note():
 def test_extract_rejects_blank_text():
     response = client.post("/action-items/extract", json={"text": "   "})
     assert response.status_code == 422
+
+
+@pytest.mark.skipif(
+    not _ollama_available(),
+    reason="Ollama is not running; start it or set OLLAMA_HOST",
+)
+def test_extract_llm_endpoint():
+    response = client.post(
+        "/action-items/extract-llm",
+        json={"text": "- [ ] Deploy staging", "save_note": False},
+    )
+    assert response.status_code == 200
+    data = response.json()
+    assert len(data["items"]) >= 1
+
+
+def test_list_notes():
+    client.post("/notes", json={"content": "first note"})
+    client.post("/notes", json={"content": "second note"})
+
+    response = client.get("/notes")
+    assert response.status_code == 200
+    notes = response.json()
+    assert len(notes) >= 2
+    contents = {note["content"] for note in notes}
+    assert "first note" in contents
+    assert "second note" in contents

```

### Exercise 5: Generate a README from the Codebase

Prompt:

```text
TODO
```

Generated Code Snippets:

```git
TODO: List all modified code files with the relevant line numbers.
```

## SUBMISSION INSTRUCTIONS

1. Hit a `Command (⌘) + F` (or `Ctrl + F`) to find any remaining `TODO`s in this file. If no results are found, congratulations – you've completed all required fields.
2. Make sure you have all changes pushed to your remote repository for grading.
3. Submit via Gradescope.
