import os
import re
from pathlib import Path
import click
import fasttext
import urllib.request
import fnmatch

MODEL_URL = "https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin"
MODEL_PATH = Path.home() / ".models" / "fasttext" / "lid.176.bin"
WHITELIST_FILE = Path(".spanish-linter-whitelist")

STRING_REGEX = re.compile(r"""(["'])(?:(?=(\\?))\2.)*?\1""")
INLINE_COMMENT_REGEX = re.compile(r"""(?://|#)\s*(.+)""")
BLOCK_COMMENT_LINE_REGEX = re.compile(r"""^\s*\*?\s*(.+)""")

EXCLUDED_PATTERNS_DEFAULT = [
    r"localhost", r"PHP_URL_HOST", r"MAIL_HOST", r"APP_URL",
]

excluded_patterns = []
whitelist = set()
model = None


def ensure_model():
    if not MODEL_PATH.exists():
        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        click.echo("⬇️  Downloading fastText model...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)


def is_spanish(text, debug=False):
    global model
    cleaned = text.strip("\"' ")

    # Check whitelist first
    if cleaned in whitelist:
        if debug:
            print(f"DEBUG: Text '{cleaned}' found in whitelist")
        return False, 0
    
    if len(cleaned) <= 3:
        if debug:
            print(f"DEBUG: Text '{cleaned}' too short (<= 3)")
        return False, 0
    if re.search(r"[#]?[0-9A-Fa-f]{6,8}", cleaned):
        if debug:
            print(f"DEBUG: Text '{cleaned}' looks like hex")
        return False, 0
    if re.match(r"^[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$", cleaned):
        if debug:
            print(f"DEBUG: Text '{cleaned}' no letters")
        return False, 0
    if re.fullmatch(r"https?://\S+", cleaned):
        if debug:
            print(f"DEBUG: Text '{cleaned}' is URL")
        return False, 0
    if re.fullmatch(r"[\w\-_/]+(\.\w+)?", cleaned):
        if debug:
            print(f"DEBUG: Text '{cleaned}' looks like path/filename")
        return False, 0
    if len(cleaned.split()) < 2:
        if debug:
            print(f"DEBUG: Text '{cleaned}' less than 2 words")
        return False, 0
    
    letters = re.findall(r"[a-zA-ZáéíóúÁÉÍÓÚñÑ]", cleaned)
    if len(letters) / len(cleaned) < 0.4:
        if debug:
            print(f"DEBUG: Text '{cleaned}' not enough letters ({len(letters)}/{len(cleaned)} = {len(letters)/len(cleaned):.2%})")
        return False, 0
    
    # Check excluded patterns
    for pattern in excluded_patterns:
        if re.search(pattern, cleaned):
            if debug:
                print(f"DEBUG: Text '{cleaned}' matches excluded pattern '{pattern}'")
            return False, 0

    # Load model if not loaded
    if model is None:
        if debug:
            print("DEBUG: Loading FastText model...")
        try:
            model = fasttext.load_model(str(MODEL_PATH))
            if debug:
                print("DEBUG: FastText model loaded successfully")
        except Exception as e:
            if debug:
                print(f"DEBUG: Error loading FastText model: {e}")
            return False, 0
    
    if debug:
        print(f"DEBUG: Analyzing text: '{cleaned}'")
    try:
        predictions = model.predict(cleaned, k=1)
        lang = predictions[0][0].replace("__label__", "")
        confidence = predictions[1][0]
        
        is_spanish = lang == "es" and confidence >= 0.50
        if debug:
            print(f"DEBUG: Result - Language: {lang}, Confidence: {confidence:.2%}, Is Spanish: {is_spanish}")
        
        return is_spanish, confidence
    except Exception as e:
        if debug:
            print(f"DEBUG: Error during prediction: {e}")
        return False, 0


def check_file(filepath, debug=False):
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
                        is_es, confidence = is_spanish(comment, debug)
                        if is_es:
                            results.append((filepath, lineno, comment, "es", confidence))
                    if "*/" in line:
                        in_block_comment = False
                    continue
                for match in STRING_REGEX.finditer(line):
                    full_string = match.group(0)  # La cadena completa con comillas
                    cleaned = full_string[1:-1]   # Quitar las comillas de inicio y final
                    is_es, confidence = is_spanish(cleaned, debug)
                    if is_es:
                        results.append((filepath, lineno, cleaned, "es", confidence))
                match = INLINE_COMMENT_REGEX.search(line)
                if match:
                    comment = match.group(1).strip()
                    is_es, confidence = is_spanish(comment, debug)
                    if is_es:
                        results.append((filepath, lineno, comment, "es", confidence))
    except Exception:
        pass
    return results


def should_exclude_file(file_path, exclude_patterns):
    """Check if a file should be excluded based on exclude patterns."""
    file_str = str(file_path)
    for pattern in exclude_patterns:
        # Convert glob pattern to work with fnmatch
        if fnmatch.fnmatch(file_str, pattern) or fnmatch.fnmatch(file_str, f"*/{pattern}"):
            return True
        # Also check if any part of the path matches the pattern
        parts = file_path.parts
        for i in range(len(parts)):
            partial_path = "/".join(parts[i:])
            if fnmatch.fnmatch(partial_path, pattern):
                return True
    return False


@click.command()
@click.argument("path", type=click.Path(exists=True), default=".")
@click.option("--include", "-i", multiple=True, default=["**/*.php", "**/*.js", "**/*.ts"],
              help="Glob patterns for files to include.")
@click.option("--exclude", "-e", multiple=True, default=["vendor/**", "node_modules/**", ".git/**"],
              help="Glob patterns for paths to exclude.")
@click.option("--exclude-pattern", "-p", multiple=True,
              help="Regex patterns to exclude from Spanish detection.")
@click.option("--debug", is_flag=True, help="Show debug information with detected language and confidence.")
def main(path, include, exclude, exclude_pattern, debug):
    """
    spanish-linter: Detects unintended Spanish in code strings or comments.
    """
    if debug:
        print(f"DEBUG: Starting with path={path}, debug={debug}")
    ensure_model()

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
    
    # Filter out excluded files
    filtered_files = []
    for file in all_files:
        if should_exclude_file(file, exclude):
            if debug:
                print(f"DEBUG: File {file} excluded by pattern")
            continue
        filtered_files.append(file)
    
    if debug:
        print(f"DEBUG: Found {len(filtered_files)} files after filtering: {[str(f) for f in filtered_files[:10]]}{'...' if len(filtered_files) > 10 else ''}")

    for file in filtered_files:
        if debug:
            print(f"DEBUG: Checking file {file}")
        file_matches = check_file(file, debug)
        if debug:
            print(f"DEBUG: File {file} produced {len(file_matches)} matches")
        matches.extend(file_matches)

    if debug:
        print(f"DEBUG: Total matches: {len(matches)}")
    for filepath, lineno, text, lang, confidence in matches:
        confidence_str = f"{confidence:.2%}" if debug else ""
        lang_str = f"[{lang}]" if debug else ""
        click.echo(f"{filepath}:{lineno}: {lang_str}{confidence_str} '{text}'")


if __name__ == "__main__":
    main()
