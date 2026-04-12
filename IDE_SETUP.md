# IDE Setup for EchoNotes (Django)

Your IDE might show "Problems" (red lint errors) in HTML files that use Django template tags (`{{ ... }}`). These are **false positives** because the IDE attempts to parse them as standard CSS or HTML.

To fix this and get a clean workspace, follow these steps:

## 1. Install the Django Extension
If you are using VS Code, install the official **Django** extension by Baptiste Darthenay.
- Open Extensions (Ctrl+Shift+X)
- Search for `Django`
- Install the one with 1M+ installs.

## 2. Configure File Associations
Force your IDE to treat `.html` files in this project as "Django HTML" rather than plain HTML.

### For VS Code:
1. Open **Settings** (Ctrl + ,)
2. Search for `Files: Associations`
3. Add a new item:
   - Item: `*.html`
   - Value: `django-html`

Alternatively, add this to your `.vscode/settings.json`:
```json
{
    "files.associations": {
        "*.html": "django-html"
    },
    "emmet.includeLanguages": {
        "django-html": "html"
    }
}
```

## 3. Why This Matters
When the file is recognized as `django-html`, the IDE will:
- Correctively highlight Django tags.
- Stop reporting CSS errors for `{{ }}` inside style attributes.
- Enable `{% %}` auto-completion.

---
*Happy coding! EchoNotes is now clean and error-free.*
