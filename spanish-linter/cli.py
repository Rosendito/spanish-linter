import os
import re
from pathlib import Path
import click
import fasttext
import urllib.request

MODEL_URL = "https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin"
MODEL_PATH = Path.home() / ".models" / "fasttext" / "lid.176.bin"
WHITELIST_FILE = Path(".spanish-linter-whitelist")

STRING_REGEX = re.compile(r"""(["'])(?:(?=(\\?))\2.)*?\1""")
INLINE_COMMENT_REGEX = re.compile(r"""(?://|#)\s*(.+)""")
BLOCK_COMMENT_LINE_REGEX = re.compile(r"""^\s*\*?\s*(.+)""")

EXCLUDED_PATTERNS_DEFAULT = [
    r"localhost", r"PHP_URL_HOST", r"MAIL_HOST", r"APP_URL", r"[A-Z_]{2,}",
]

excluded_patterns = []
whitelist = set()
model = None


def ensure_model():
    if not MODEL_PATH.exists():
        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        click.echo("⬇️  Downloading fastText model...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)


def is_spanish(text):
    global model
    cleaned = text.strip("\"' ")

    if cleaned in whitelist:
        return False
    if len(cleaned) <= 3:
        return False
    if re.search(r"[#]?[0-9A-Fa-f]{6,8}", cleaned):
        return False
    if re.match(r"^[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$", cleaned):
        return False
    if re.fullmatch(r"https?://\S+", cleaned):
        return False
    if re.fullmatch(r"[\w\-_/]+(\.\w+)?", cleaned):
        return False
    if len(cleaned.split()) < 2:
        return False
    letters = re.findall(r"[a-zA-ZáéíóúÁÉÍÓÚñÑ]", cleaned)
    if len(letters) / len(cleaned) < 0.4:
        return False
    for pattern in excluded_patterns:
        if re.search(pattern, cleaned):
            return False

    if model is None:
        model = fasttext.load_model(str(MODEL_PATH))
    predictions = model.predict(cleaned, k=1)
    lang = predictions[0][0].replace("__label__", "")
    confidence = predictions[1][0]
    return lang == "es" and confidence >= 0.50


def check_file(filepath):
    results = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            in_block_comment = False
            for lineno, line in enumerate(f, 1):
                if "/*" in line:
                    in_block_comment = True
                if in_block_comment:
                    match = BLOCK_COMMENT_LINE_REGEX.search(line)
                    if match:
                        comment = match.group(1).strip()
                        if is_spanish(comment):
                            results.append((filepath, lineno, comment))
                    if "*/" in line:
                        in_block_comment = False
                    continue
                for match in STRING_REGEX.findall(line):
                    full_match = match[0]
                    if is_spanish(full_match):
                        results.append((filepath, lineno, full_match.strip("\"'")))
                match = INLINE_COMMENT_REGEX.search(line)
                if match:
                    comment = match.group(1).strip()
                    if is_spanish(comment):
                        results.append((filepath, lineno, comment))
    except Exception:
        pass
    return results


@click.command()
@click.argument("path", type=click.Path(exists=True), default=".")
@click.option("--include", "-i", multiple=True, default=["**/*.php", "**/*.js", "**/*.ts"],
              help="Glob patterns for files to include.")
@click.option("--exclude", "-e", multiple=True, default=["vendor/**", "node_modules/**", ".git/**"],
              help="Glob patterns for paths to exclude.")
@click.option("--exclude-pattern", "-p", multiple=True,
              help="Regex patterns to exclude from Spanish detection.")
def main(path, include, exclude, exclude_pattern):
    """
    spanish-linter: Detects unintended Spanish in code strings or comments.
    """
    ensure_model()

    # Cargar whitelist local si existe
    if WHITELIST_FILE.exists():
        with open(WHITELIST_FILE, "r", encoding="utf-8") as f:
            whitelist.update(line.strip() for line in f if line.strip())

    path = Path(path)
    global excluded_patterns
    excluded_patterns[:] = list(exclude_pattern) if exclude_pattern else EXCLUDED_PATTERNS_DEFAULT

    matches = []
    all_files = set()
    for pattern in include:
        all_files.update(path.glob(pattern))

    for file in all_files:
        if any(file.match(ex) for ex in exclude):
            continue
        matches.extend(check_file(file))

    for filepath, lineno, text in matches:
        click.echo(f"{filepath}:{lineno}: '{text}'")
