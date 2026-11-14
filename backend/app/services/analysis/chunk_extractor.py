def extract_chunks(analysis_result: dict) -> list[dict]:
    """
    Convert HTML, CSS and SQL analysis results
    into standardized code chunks.
    """

    chunks = []

    # Extract HTML elements
    for element in analysis_result.get("html_elements", []):
        chunks.append({
            "name": element["name"],
            "chunk_type": element["chunk_type"],
            "start_line": element["start_line"],
            "end_line": element["end_line"],
            "content": element["content"],
        })

    # Extract CSS rules
    for rule in analysis_result.get("css_rules", []):
        chunks.append({
            "name": rule["name"],
            "chunk_type": rule["chunk_type"],
            "start_line": rule["start_line"],
            "end_line": rule["end_line"],
            "content": rule["content"],
        })

    # Extract SQL statements
    for statement in analysis_result.get("sql_statements", []):
        chunks.append({
            "name": statement["name"],
            "chunk_type": statement["chunk_type"],
            "start_line": statement["line"],
            "end_line": statement["end_line"],
            "content": statement["query"],
        })

    return chunks