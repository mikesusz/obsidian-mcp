
**Phase 2.6: Smart Template Placeholders**

**Goal:** Support placeholder replacement in templates for common auto-filled values.

**Changes needed in `vault.py` (or wherever template processing happens):**

Add a function to replace placeholders before writing the file:

```python
def replace_placeholders(content: str) -> str:
    """Replace template placeholders with actual values."""
    from datetime import datetime

    now = datetime.now()

    replacements = {
        "{{TODAY}}": now.strftime("%Y-%m-%d"),
        "{{NOW}}": now.strftime("%Y-%m-%d %H:%M:%S"),
        "{{DATE}}": now.strftime("%Y-%m-%d"),  # alias for TODAY
        "{{TIME}}": now.strftime("%H:%M:%S"),
        "{{TIMESTAMP}}": str(int(now.timestamp())),
        "{{YEAR}}": now.strftime("%Y"),
        "{{MONTH}}": now.strftime("%m"),
        "{{DAY}}": now.strftime("%d"),
    }

    for placeholder, value in replacements.items():
        content = content.replace(placeholder, value)

    return content
```

**In `create_note_from_template`:**
1. Read template content
2. Call `replace_placeholders(content)` before writing
3. Write the processed content to new file

**Supported placeholders:**
- `{{TODAY}}` → "2026-02-26"
- `{{NOW}}` → "2026-02-26 15:30:45"
- `{{DATE}}` → "2026-02-26" (same as TODAY)
- `{{TIME}}` → "15:30:45"
- `{{TIMESTAMP}}` → "1708966245"
- `{{YEAR}}` → "2026"
- `{{MONTH}}` → "02"
- `{{DAY}}` → "26"

**Example templates:**

New Book:
```yaml
date: "{{TODAY}}"
```

PROJECT:
```
# PROJECT:
Created: {{NOW}}
```

Journal entry:
```
# {{TODAY}} Journal Entry
Time: {{TIME}}
```

**Testing:**
- Create note from template with `{{TODAY}}` → should have actual date
- Multiple placeholders in one template → all replaced
- No placeholders → works as before (no change)

**README update:**
Document available placeholders and show examples

