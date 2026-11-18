from app.services.ai.ollama_service import ollama_service


def prepare_architecture_summary(architecture: dict) -> str:
    """Prepare exact architecture facts from database records."""

    lines = []

    lines.append(f"PROJECT: {architecture['project_name']}")
    lines.append(f"TOTAL FILES: {architecture['total_files']}")
    lines.append(f"TOTAL SYMBOLS: {architecture['total_symbols']}")
    lines.append(
        f"TOTAL DEPENDENCIES: "
        f"{architecture.get('total_dependencies', 0)}"
    )
    lines.append(
        f"TOTAL INTERNAL DEPENDENCIES: "
        f"{architecture['total_internal_dependencies']}"
    )

    modules = architecture.get("modules", [])

    lines.append("\nPROGRAMMING LANGUAGES:")

    languages = architecture.get("languages", [])

    if languages:
        for language in languages:
            lines.append(
                f"- {language['language']}: "
                f"{language['file_count']} file(s)"
            )
    else:
        lines.append("- No programming languages were classified.")

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
You are CodeAtlas AI, a senior software architect who explains
existing codebases to developers who are new to the project.

STRICT RULES:

1. Use only the supplied architecture information.
2. Do not reproduce complete file lists or symbol lists.
3. Do not invent files, modules, technologies, relationships or
   behaviour.
4. Do not assume functionality based only on filenames. Describe
   apparent or possible purposes with clear caution.
5. Separate observed facts from reasonable inferences. Say when the
   evidence is limited.
6. Do not claim that the project was executed or tested.
7. Do not repeat exact statistics; the interface shows those
   separately from Python-derived data.
8. Focus on responsibilities, boundaries, coupling, entry points,
   data and configuration, and how a developer should navigate the
   codebase.
9. Be concise but specific. Reference actual directories, files and
   modules as evidence.
10. If the project uses multiple languages or is a sample/test
    project, explain the apparent role of each part without assuming
    it is a production system.
"""

    prompt = f"""
Explain the overall architecture of this project for a developer
who is about to work with it for the first time.

Use the following information only as reference data:

{architecture_summary}

Write a concise explanation under these headings:

# System Overview
Explain what the project appears to be and the main architectural
idea that holds it together.

# Module and Directory Roles
Explain the responsibility of the main modules and directories,
which files matter most, and how those areas relate to each other.

# Entry Points and Application Flow
Describe the apparent entry points and how execution or data moves
between the parts, based only on the supplied symbols and resolved
dependencies.

# Internal Dependency Patterns
Interpret the resolved relationships: important hubs, leaf modules,
cross-module links, and coupling. If the dependency data is sparse,
say so instead of inventing links.

# Language and Technology Roles
Explain the significance of the languages and technologies present,
especially if the project contains multiple languages.

# Reading Guide
Suggest the order in which a developer should explore the project
and what to understand before making changes.

Do not repeat the complete inventory or exact counts. Do not include
code snippets or fenced code blocks.
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
