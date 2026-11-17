def extract_chunks(analysis_result: dict) -> list[dict]:
    """
    Convert extracted functions, methods, classes,
    HTML, CSS and SQL structures into standardized code chunks.
    """

    chunks = []

    # Extract functions
    for function in analysis_result.get("functions", []):
        chunks.append({
            "name": function["name"],
            "chunk_type": "function",
            "start_line": function["line"],
            "end_line": function["end_line"],
            "content": function["source_code"],
        })

    # Extract methods
    for method in analysis_result.get("methods", []):
        chunks.append({
            "name": method["name"],
            "chunk_type": "method",
            "start_line": method["line"],
            "end_line": method["end_line"],
            "content": method["source_code"],
        })

    # Extract classes
    for class_info in analysis_result.get("classes", []):
        chunks.append({
            "name": class_info["name"],
            "chunk_type": "class",
            "start_line": class_info["line"],
            "end_line": class_info["end_line"],
            "content": class_info["source_code"],
        })

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