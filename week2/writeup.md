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
TODO
```

Generated/Modified Code Snippets:
```
TODO: List all modified code files with the relevant line numbers. (We anticipate there may be multiple scattered changes here – just produce as comprehensive of a list as you can.)
```


### Exercise 4: Use Agentic Mode to Automate a Small Task
Prompt: 
```
TODO
``` 

Generated Code Snippets:
```
TODO: List all modified code files with the relevant line numbers.
```


### Exercise 5: Generate a README from the Codebase
Prompt: 
```
TODO
``` 

Generated Code Snippets:
```
TODO: List all modified code files with the relevant line numbers.
```


## SUBMISSION INSTRUCTIONS
1. Hit a `Command (⌘) + F` (or `Ctrl + F`) to find any remaining `TODO`s in this file. If no results are found, congratulations – you've completed all required fields. 
2. Make sure you have all changes pushed to your remote repository for grading.
3. Submit via Gradescope. 