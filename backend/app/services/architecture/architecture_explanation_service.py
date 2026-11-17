from collections import Counter

from app.services.ai.ollama_service import ollama_service


def prepare_architecture_summary(architecture: dict) -> str:
    """Prepare exact architecture facts from database records."""

    lines = []

    lines.append(f"PROJECT: {architecture['project_name']}")
    lines.append(f"TOTAL FILES: {architecture['total_files']}")
    lines.append(f"TOTAL SYMBOLS: {architecture['total_symbols']}")
    lines.append(
        f"TOTAL INTERNAL DEPENDENCIES: "
        f"{architecture['total_internal_dependencies']}"
    )

    modules = architecture.get("modules", [])

    language_counts = Counter()

    for module in modules:
        language_counts.update(module.get("languages", []))

    lines.append("\nPROGRAMMING LANGUAGES:")

    for language, count in sorted(language_counts.items()):
        lines.append(f"- {language}: {count} module occurrence(s)")

    lines.append("\nPROJECT MODULES:")

    for index, module in enumerate(modules, start=1):
        lines.append(f"\nMODULE {index}: {module['name']}")
        lines.append(f"File count: {module['file_count']}")
        lines.append(
            f"Languages: {', '.join(module.get('languages', [])) or 'None classified'}"
        )

        lines.append("Files:")

        for file_path in module.get("files", []):
            lines.append(f"- {file_path}")

        symbols = module.get("symbols", [])

        lines.append(f"Detected symbols: {len(symbols)}")

        for symbol in symbols:
            lines.append(
                f"- {symbol['type']}: {symbol['name']} "
                f"(File: {symbol['file_path']}, "
                f"Lines: {symbol['start_line']}-{symbol['end_line']})"
            )

    relationships = architecture.get("file_relationships", [])

    lines.append("\nINTERNAL FILE RELATIONSHIPS:")
    lines.append(f"Total relationships: {len(relationships)}")

    for relationship in relationships:
        lines.append(
            f"- {relationship['source']} -> {relationship['target']} "
            f"(Dependency: {relationship['dependency']}, "
            f"Type: {relationship['type']}, "
            f"Line: {relationship['line_number']})"
        )

    module_relationships = architecture.get(
        "module_relationships", []
    )

    lines.append("\nMODULE RELATIONSHIPS:")
    lines.append(f"Total relationships: {len(module_relationships)}")

    for relationship in module_relationships:
        lines.append(
            f"- {relationship['source']} -> {relationship['target']} "
            f"(Dependencies: {relationship['dependency_count']})"
        )

    return "\n".join(lines)


async def generate_architecture_explanation(
    architecture: dict,
) -> str:
    """Combine exact Python-generated facts with a short AI explanation."""

    architecture_summary = prepare_architecture_summary(architecture)

    system_prompt = """
You are CodeAtlas AI, a beginner-friendly software architecture analyst.

Your task is to explain the overall organization of a software project.

STRICT RULES:

1. Use only the supplied architecture information.
2. Do not reproduce complete file lists or symbol lists.
3. Do not invent files, modules, technologies or relationships.
4. Do not assume functionality based only on filenames.
5. Explain uncertain purposes as possibilities.
6. Do not claim that the project was executed or tested.
7. Keep the explanation concise and beginner-friendly.
8. Focus on the overall project organization and observed structure.
9. If information is insufficient, clearly say so.

Explain:
- The general organization of the project.
- How its directories appear to be organized.
- The significance of its multiple programming languages, if applicable.
- Any patterns visible in the supplied internal dependencies.

Do not generate exact statistics or detailed file inventories.
Python will provide those separately.
"""

    prompt = f"""
Explain the overall architecture of this project.

Use the following information only as reference data:

{architecture_summary}

Write a concise explanation under these headings:

# Overall Architecture

# Directory Organization

# Technology Overview

# Dependency Overview

Do not repeat the complete inventory.
"""

    answer = await ollama_service.generate_response(
        prompt=prompt,
        system_prompt=system_prompt,
    )

    if not answer:
        raise RuntimeError(
            "AI could not generate the architecture explanation."
        )

    return answer
