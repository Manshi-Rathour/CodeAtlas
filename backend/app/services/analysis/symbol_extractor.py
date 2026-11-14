
def extract_symbols(analysis_result: dict) -> list[dict]:
    """
    Convert Tree-sitter analysis results into
    a standardized list of code symbols.
    """

    symbols = []

    # Extract functions
    for function in analysis_result.get("functions", []):
        symbols.append({
            "name": function["name"],
            "symbol_type": "function",
            "start_line": function["line"],
            "end_line": function["end_line"],
            "source_code": function["source_code"],
        })

    # Extract methods
    for method in analysis_result.get("methods", []):
        symbols.append({
            "name": method["name"],
            "symbol_type": "method",
            "start_line": method["line"],
            "end_line": method["end_line"],
            "source_code": method["source_code"],
        })

    # Extract classes and structs
    for class_info in analysis_result.get("classes", []):
        symbols.append({
            "name": class_info["name"],
            "symbol_type": "class",
            "start_line": class_info["line"],
            "end_line": class_info["end_line"],
            "source_code": class_info["source_code"],
        })

    return symbols
