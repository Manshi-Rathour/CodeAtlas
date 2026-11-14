import re


def extract_dependencies(analysis_result: dict) -> list[dict]:
    """
    Convert Tree-sitter import results into
    standardized dependency records.
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

    return dependencies
