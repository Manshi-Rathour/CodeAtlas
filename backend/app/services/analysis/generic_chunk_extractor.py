
def extract_generic_chunks(
    source_code: str,
    chunk_size: int = 80,
    overlap: int = 10,
) -> list[dict]:
    """
    Split source code into overlapping text chunks.

    This fallback is used when a language does not
    have a supported Tree-sitter parser.
    """

    lines = source_code.splitlines()

    if not lines:
        return []

    chunks = []
    start = 0

    while start < len(lines):
        end = min(start + chunk_size, len(lines))

        content = "\n".join(lines[start:end])

        if content.strip():
            chunks.append({
                "name": f"Code section starting at line {start + 1}",
                "chunk_type": "generic",
                "start_line": start + 1,
                "end_line": end,
                "content": content,
            })

        if end == len(lines):
            break

        start = end - overlap

    return chunks
