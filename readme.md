# spanish-linter

**A CLI tool to detect unintended Spanish in code comments or strings.**

This tool is useful for enforcing consistent language use in multilingual or English-only codebases. It scans source files for Spanish content using a fastText model, and allows fine-grained control via glob filters, regex excludes, and a whitelist.

**Model**: Uses Facebook's fastText `lid.176.bin` language detection model (176 languages supported). The model downloads automatically on first use (~917MB) to `~/.models/fasttext/` and runs offline with 50% confidence threshold.

---

## 🚀 Installation

```bash
git clone https://github.com/your-org/spanish-linter.git
cd spanish-linter
bash install.sh
```

This will:

- Install Python and pipx (via Homebrew, if needed)
- Download the fastText language detection model
- Install `spanish-linter` globally via pipx

---

## 🔍 Usage

```bash
spanish-linter [path] [options]
```

### Example

```bash
spanish-linter . \
  --include '**/*.php' \
  --exclude 'vendor/**' \
  --exclude-pattern 'APP_NAME' \
  --exclude-pattern '[A-Z_]{3,}'
```

---

## ⚙️ Options

| Option                    | Description                                          |
| ------------------------- | ---------------------------------------------------- |
| `--include`, `-i`         | Glob patterns for files to include (default: PHP/JS) |
| `--exclude`, `-e`         | Glob patterns for paths to exclude                   |
| `--exclude-pattern`, `-p` | Regex patterns to ignore matching content            |

---

## 🧪 Whitelist support

You can prevent specific strings from being flagged by adding a `.spanish-linter-whitelist` file in the directory where you run the tool.

Each line represents one exact string to ignore:

```txt
Dirección de envío
Hola mundo
Mensaje de error genérico
```

If a detected string matches any line in the whitelist, it will be skipped.

---

## 📦 Development

Install dependencies in a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Then run:

```bash
spanish-linter --help
```
