import re


# Languages whose files reference other project assets (CSS, JS, templates).
MARKUP_LANGUAGES = {"html", "htm"}

STYLESHEET_LANGUAGES = {"css"}

# Tags that load another project file.
ASSET_TAG_PATTERN = re.compile(
    r"<\s*(?P<tag>link|script)\b(?P<attributes>[^>]*)>",
    re.IGNORECASE | re.DOTALL,
)

# Attributes inside an HTML start tag, quoted or unquoted.
ATTRIBUTE_PATTERN = re.compile(
    r"""(?P<name>[a-zA-Z_:][-a-zA-Z0-9_:.]*)
        \s*=\s*
        (?:"(?P<double>[^"]*)"|'(?P<single>[^']*)'|(?P<bare>[^\s"'=<>`]+))""",
    re.VERBOSE | re.DOTALL,
)

# Jinja/Flask template composition: include, extends, import, from.
TEMPLATE_PATTERN = re.compile(
    r"""{%-?\s*(?P<tag>include|extends|import|from)\s+
        ["'](?P<path>[^"']+)["']""",
    re.IGNORECASE | re.VERBOSE,
)

# CSS @import statements.
CSS_IMPORT_PATTERN = re.compile(
    r"""@import\s+(?:url\(\s*)?["'](?P<path>[^"']+)["']""",
    re.IGNORECASE,
)

# References that never point at a file inside the project.
IGNORED_REFERENCE_PREFIXES = (
    "http://",
    "https://",
    "//",
    "data:",
    "mailto:",
    "tel:",
    "javascript:",
    "#",
)


def _referenced_line(source_code: str, offset: int) -> int:
    """Return the 1-based line number of a regex match."""

    return source_code.count("\n", 0, offset) + 1


def _is_local_reference(value: str | None) -> bool:
    """Return True when a reference can point at a project file."""

    reference = (value or "").strip()

    if not reference:
        return False

    if reference.lower().startswith(IGNORED_REFERENCE_PREFIXES):
        return False

    # Template expressions such as url_for('static', ...) are not paths.
    if "{{" in reference or "{%" in reference:
        return False

    return True


def _extract_attributes(raw_attributes: str) -> dict[str, str]:
    """Parse the attributes of a single HTML start tag."""

    attributes: dict[str, str] = {}

    for match in ATTRIBUTE_PATTERN.finditer(raw_attributes):
        value = match.group("double")

        if value is None:
            value = match.group("single")

        if value is None:
            value = match.group("bare")

        attributes.setdefault(match.group("name").lower(), value or "")

    return attributes


def _extract_markup_dependencies(source_code: str) -> list[dict]:
    """
    Extract stylesheet, script and template references from markup.

    HTML pages load CSS and JavaScript through <link> and <script> tags,
    and templates compose other templates through Jinja statements such
    as {% include 'navbar.html' %}. Tree-sitter does not report these as
    imports, so they are collected directly from the source text.
    """

    dependencies = []

    for match in ASSET_TAG_PATTERN.finditer(source_code):
        tag = match.group("tag").lower()
        attributes = _extract_attributes(match.group("attributes"))
        reference = None
        dependency_type = None

        if tag == "script":
            reference = attributes.get("src")
            dependency_type = "script"

        else:
            relationship = attributes.get("rel", "").lower()

            # Only stylesheet links load another project file. Icons and
            # preconnects do not create source-level dependencies.
            if "stylesheet" in relationship:
                reference = attributes.get("href")
                dependency_type = "stylesheet"

        if not _is_local_reference(reference):
            continue

        dependencies.append({
            "dependency_name": reference.strip(),
            "dependency_type": dependency_type,
            "line_number": _referenced_line(source_code, match.start()),
            "imported_symbols": None,
        })

    for match in TEMPLATE_PATTERN.finditer(source_code):
        reference = match.group("path")

        if not _is_local_reference(reference):
            continue

        dependency_type = (
            "template_extends"
            if match.group("tag").lower() == "extends"
            else "template_include"
        )

        dependencies.append({
            "dependency_name": reference.strip(),
            "dependency_type": dependency_type,
            "line_number": _referenced_line(source_code, match.start()),
            "imported_symbols": None,
        })

    return dependencies


def _extract_stylesheet_dependencies(source_code: str) -> list[dict]:
    """Extract @import references from a CSS file."""

    dependencies = []

    for match in CSS_IMPORT_PATTERN.finditer(source_code):
        reference = match.group("path")

        if not _is_local_reference(reference):
            continue

        dependencies.append({
            "dependency_name": reference.strip(),
            "dependency_type": "css_import",
            "line_number": _referenced_line(source_code, match.start()),
            "imported_symbols": None,
        })

    return dependencies


def extract_dependencies(
    analysis_result: dict,
    source_code: str | None = None,
) -> list[dict]:
    """
    Convert Tree-sitter import results into
    standardized dependency records.

    When the source text is supplied, markup and stylesheet references
    (CSS, JavaScript, templates) are extracted as well.
    """

    dependencies = []
    language = analysis_result.get("language", "").lower()

    for import_info in analysis_result.get("imports", []):
        source = import_info["name"].strip()
        line = import_info["line"]

        dependency_name = None
        imported_symbols = None
        dependency_type = "import"


        # Python
        if language == "python":

            # Example: from fastapi import FastAPI, Depends
            match = re.match(
                r"from\s+([\w.]+)\s+import\s+(.+)",
                source,
                re.DOTALL
            )

            if match:
                dependency_name = match.group(1)
                imported_symbols = match.group(2).strip()

            else:
                # Example: import numpy
                # Example: import pandas as pd
                match = re.match(
                    r"import\s+([\w.]+)(?:\s+as\s+(\w+))?",
                    source
                )

                if match:
                    dependency_name = match.group(1)

                    if match.group(2):
                        imported_symbols = f"as {match.group(2)}"


        # JavaScript and TypeScript
        elif language in ("javascript", "typescript", "tsx"):

            # Extract the module path.
            match = re.search(
                r"\bfrom\s*['\"]([^'\"]+)['\"]",
                source
            )

            # Handle side-effect imports.
            if not match:
                match = re.search(
                    r"\bimport\s*['\"]([^'\"]+)['\"]",
                    source
                )

            if match:
                dependency_name = match.group(1)

                # Extract imported symbols or aliases.
                import_match = re.match(
                    r"import\s+(.+?)\s+from\s*['\"]",
                    source,
                    re.DOTALL
                )

                if import_match:
                    imported_symbols = import_match.group(1).strip()


        # Java, Kotlin and Swift
        elif language in ("java", "kotlin", "swift"):

            match = re.search(
                r"\bimport\s+(?:static\s+)?([\w.*]+)(?:\s+as\s+(\w+))?",
                source
            )

            if match:
                dependency_name = match.group(1)

                if match.group(2):
                    imported_symbols = f"as {match.group(2)}"

                dependency_type = "import"


        # C and C++
        elif language in ("c", "cpp"):

            match = re.search(
                r'#\s*include\s*([<"])([^>"]+)[>"]',
                source
            )

            if match:
                dependency_name = match.group(2)

                if match.group(1) == "<":
                    dependency_type = "system_include"
                else:
                    dependency_type = "local_include"


        # Go
        elif language == "go":

            matches = re.finditer(
                r'"([^"]+)"',
                source
            )

            for match in matches:
                dependency_name = match.group(1)

                # Calculate the actual import line.
                line_number = line + source[:match.start()].count("\n")

                dependencies.append({
                    "dependency_name": dependency_name,
                    "dependency_type": "import",
                    "line_number": line_number,
                    "imported_symbols": None,
                })

            continue


        # Rust
        elif language == "rust":

            match = re.search(
                r"\buse\s+(.+?);",
                source,
                re.DOTALL
            )

            if match:
                import_path = match.group(1).strip()

                # Handle grouped imports.
                if "::{" in import_path:
                    dependency_name, symbols = import_path.split(
                        "::{",
                        1
                    )

                    imported_symbols = symbols.rstrip("}").strip()

                else:
                    dependency_name = import_path

                dependency_type = "use"


        # PHP
        elif language == "php":

            match = re.search(
                r"\buse\s+([\w\\]+)(?:\s+as\s+(\w+))?",
                source
            )

            if match:
                dependency_name = match.group(1)

                if match.group(2):
                    imported_symbols = f"as {match.group(2)}"

                dependency_type = "use"


        # Ruby
        elif language == "ruby":

            match = re.search(
                r"""(require_relative|require)\s*['"]([^'"]+)['"]""",
                source
            )

            if match:
                dependency_type = match.group(1)
                dependency_name = match.group(2)


        if dependency_name:
            dependencies.append({
                "dependency_name": dependency_name,
                "dependency_type": dependency_type,
                "line_number": line,
                "imported_symbols": imported_symbols,
            })

    if source_code:
        if language in MARKUP_LANGUAGES:
            dependencies.extend(
                _extract_markup_dependencies(source_code)
            )

        elif language in STYLESHEET_LANGUAGES:
            dependencies.extend(
                _extract_stylesheet_dependencies(source_code)
            )

    return dependencies
