## Obsidian MCP Server - Phase 2.5: Template-Based Note Creation

**Goal**: Enable creation of new files from ANY template in the `templates/` directory, making this a generic template system rather than PROJECT-specific.

**What's changing:**
- Add ability to create new files from any template in `templates/`
- Auto-discover available templates (no hardcoded list)
- Support naming conventions like "TEMPLATE_NAME {user_input}.md"
- Maintain safety controls around file creation

**New MCP Tools:**

### 1. list_templates

**Description**: List all available templates in the templates/ directory

**Input:** None

**Returns:**
```json
{
  "templates": [
    {
      "name": "PROJECT",
      "path": "templates/PROJECT.md",
      "size": 100,
      "description": "General project template"
    },
    {
      "name": "WRITING PROJECT",
      "path": "templates/WRITING PROJECT.md",
      "size": 96,
      "description": "Writing project template"
    },
    {
      "name": "New Book",
      "path": "templates/New Book.md",
      "size": 87,
      "description": "Book tracking template"
    }
  ]
}
```

**Implementation:**
- Scan `{VAULT_PATH}/templates/` directory
- Return all .md files found
- Description comes from first line of template if it's a comment, otherwise generic

### 2. create_note_from_template

**Description**: Create a new note from a template, optionally with a custom name/suffix

**Input:**
- `template_name` (string, required) - Name of template (e.g., "PROJECT", "RECIPE")
- `note_suffix` (string, optional) - Custom name/suffix for the new note
- `field_values` (object, optional) - Key-value pairs to fill in template placeholders

**Returns:**
```json
{
  "success": true,
  "file_path": "PROJECT replacing the deck.md",
  "message": "Created new note from template",
  "template_used": "templates/PROJECT.md"
}
```

**Behavior:**

1. **Find template:**
   - Look for `templates/{template_name}.md`
   - If not found, return error listing available templates

2. **Determine output filename:**
   - If `note_suffix` provided: `{template_name} {note_suffix}.md`
   - If not provided: `{template_name} {timestamp}.md` or just `{template_name}.md`
   - Examples:
     - template: "PROJECT", suffix: "deck replacement" → "PROJECT deck replacement.md"
     - template: "RECIPE", suffix: "chocolate cake" → "RECIPE chocolate cake.md"
     - template: "New Book", suffix: "The Expanse" → "New Book The Expanse.md"

3. **Check for existing file:**
   - If file exists, return error: "Note already exists: {filepath}"

4. **Read and process template:**
   - Read template content
   - If `field_values` provided, attempt to fill in placeholders:
     - Replace `# {KEY}:` with `# {KEY}:\n{value}`
     - Support common patterns like PROJECT:, NEXT ACTION:, etc.
     - If template has structure, preserve it

5. **Create file:**
   - Write to vault root
   - Log creation to stderr

**Example Flows:**

**PROJECT creation:**
```
User: "Create a new project about replacing the deck"
→ create_note_from_template("PROJECT", "replacing the deck")
→ Creates "PROJECT replacing the deck.md"
```

**RECIPE creation (new template added by user):**
```
User has templates/RECIPE.md in their vault
User: "Create a new recipe for chocolate cake"
→ create_note_from_template("RECIPE", "chocolate cake")
→ Creates "RECIPE chocolate cake.md"
```

**With field values:**
```
User: "Create a project for kitchen remodel with next action: get quotes"
→ create_note_from_template(
    "PROJECT",
    "kitchen remodel",
    {"NEXT ACTION": "get contractor quotes", "PURPOSE/PRINCIPLES": "modernize kitchen"}
  )
```

**Safety Requirements:**
- Template name must exist in `templates/` directory
- Note suffix sanitized (letters, numbers, spaces, hyphens, underscores only)
- Max filename length: 200 characters
- Files created only at vault root
- Check for existing file before creating
- Path traversal protection in both template_name and note_suffix
- Log all creations to stderr

**Error Handling:**
- Template not found → "Template '{name}' not found. Available templates: PROJECT, WRITING PROJECT, RECIPE"
- File already exists → "Note already exists: {filepath}"
- Invalid characters → "Note name contains invalid characters"
- Template directory missing → "Templates directory not found"

**Benefits of this approach:**
- ✅ Works with any template user creates
- ✅ No hardcoded template types
- ✅ Chef can add RECIPE template
- ✅ Developer can add CODE_REVIEW template
- ✅ Teacher can add LESSON_PLAN template
- ✅ Completely extensible by user

**Testing Checklist:**
1. List templates returns all templates
2. Create note from PROJECT template
3. Create note from WRITING PROJECT template
4. Create note with field_values pre-filled
5. Attempt duplicate creation (should fail)
6. Invalid template name (should fail with helpful list)
7. Invalid note suffix with special chars (should fail)
8. Path traversal in template_name (should fail)

**README Updates:**
- Document both new tools
- Explain templates/ directory convention
- Show examples with different template types
- Emphasize extensibility (users can add their own templates)
- Provide examples of custom templates
