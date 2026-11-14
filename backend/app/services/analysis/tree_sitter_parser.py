from tree_sitter_language_pack import get_parser


# Supported languages and their Tree-sitter grammar names
SUPPORTED_LANGUAGES = {
    "python": "python",
    "javascript": "javascript",
    "typescript": "typescript",
    "tsx": "tsx",
    "java": "java",
    "cpp": "cpp",
    "c": "c",
    "go": "go",
    "rust": "rust",
    "php": "php",
    "ruby": "ruby",
    "html": "html",
    "css": "css",
    "sql": "sql",
    "swift": "swift",
    "kotlin": "kotlin",
}


# Common syntax node types for different languages

FUNCTION_NODE_TYPES = {
    "function_definition",
    "function_declaration",
    "function_item",
    "function",
    "method_definition",
    "method_declaration",
    "method",
    "arrow_function",
    "function_expression",
    "constructor_declaration",
    "init_declaration",
    "singleton_method",
}

CLASS_NODE_TYPES = {
    "class_definition",
    "class_declaration",
    "class_specifier",
    "struct_item",
    "struct_declaration",
    "interface_declaration",
    "enum_declaration",
    "trait_item",
    "trait_declaration",
    "module_definition",
    "class",
}

IMPORT_NODE_TYPES = {
    "import_statement",
    "import_declaration",
    "import_from_statement",
    "use_declaration",
    "include_directive",
    "preproc_include",
    "extern_crate_declaration",
    "namespace_use_declaration",
    "import_header",
}


def normalize_language(language: str) -> str:
    """Normalize and validate the requested language."""

    language = language.lower().strip()

    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language: {language}")

    return language


def get_language_parser(language: str):
    """Load the Tree-sitter parser for a language."""

    language = normalize_language(language)

    return get_parser(SUPPORTED_LANGUAGES[language])


def get_node_text(node, source_bytes: bytes) -> str:
    """Extract the original source text represented by a node."""

    return source_bytes[node.start_byte:node.end_byte].decode(
        "utf-8",
        errors="replace",
    )



def get_node_name(node, source_bytes: bytes) -> str:
    """Extract the name of a function, class, or method."""

    name_node = node.child_by_field_name("name")

    if name_node is not None:
        return get_node_text(name_node, source_bytes)

    # Handle nested declarators used by C and C++.
    declarator_node = node.child_by_field_name("declarator")

    while declarator_node is not None:
        if declarator_node.type in (
            "identifier",
            "field_identifier",
            "type_identifier",
        ):
            return get_node_text(declarator_node, source_bytes)

        declarator_node = declarator_node.child_by_field_name(
            "declarator"
        )

    # Fallback for other language grammars.
    for child in node.children:
        if child.type in (
            "identifier",
            "type_identifier",
            "field_identifier",
            "simple_identifier",
        ):
            return get_node_text(child, source_bytes)

    return "anonymous"



def parse_source_code(source_code: str, language: str):
    """Parse source code and return its Tree-sitter syntax tree."""

    parser = get_language_parser(language)

    source_bytes = source_code.encode("utf-8")

    return parser.parse(source_bytes)


def analyze_source_code(source_code: str, language: str) -> dict:
    """
    Analyze source code and extract its basic structure.

    Returns:
        language
        functions
        classes
        imports
        has_syntax_errors
    """

    language = normalize_language(language)

    source_bytes = source_code.encode("utf-8")
    tree = parse_source_code(source_code, language)

    functions = []
    methods = []
    classes = []
    imports = []
    html_tags = []
    html_ids = []
    html_classes = []
    html_elements = []
    css_selectors = []
    css_properties = []
    css_rules = []
    sql_statements = []
    sql_tables = []
    sql_columns = []

    def visit_node(node):
        node_type = node.type

        if language == "html":
            if node_type == "element":
                tag_node = None

                for child in node.children:
                    if child.type == "start_tag":
                        for tag_child in child.children:
                            if tag_child.type == "tag_name":
                                tag_node = tag_child
                                break

                    if tag_node is not None:
                        break

                if tag_node is not None:
                    html_elements.append({
                        "name": get_node_text(tag_node, source_bytes),
                        "chunk_type": "html_tag",
                        "start_line": node.start_point.row + 1,
                        "end_line": node.end_point.row + 1,
                        "content": get_node_text(node, source_bytes),
                    })

            if node_type == "tag_name":
                tag_name = get_node_text(node, source_bytes)

                if tag_name not in html_tags:
                    html_tags.append(tag_name)

            elif node_type == "attribute":
                attribute_name = None
                attribute_value = None

                for child in node.children:
                    if child.type == "attribute_name":
                        attribute_name = get_node_text(child, source_bytes)

                    elif child.type == "quoted_attribute_value":
                        for value_child in child.children:
                            if value_child.type == "attribute_value":
                                attribute_value = get_node_text(
                                    value_child,
                                    source_bytes
                                )

                if attribute_name is not None and attribute_value is not None:
                    if attribute_name == "id" and attribute_value not in html_ids:
                        html_ids.append(attribute_value)

                    elif attribute_name == "class":
                        for class_name in attribute_value.split():
                            if class_name not in html_classes:
                                html_classes.append(class_name)

        if language == "css":
            if node_type == "rule_set":
                selectors_node = None

                for child in node.children:
                    if child.type == "selectors":
                        selectors_node = child
                        break

                if selectors_node is not None:
                    selector_name = get_node_text(
                        selectors_node,
                        source_bytes
                    )

                    css_rules.append({
                        "name": selector_name,
                        "chunk_type": "css_selector",
                        "start_line": node.start_point.row + 1,
                        "end_line": node.end_point.row + 1,
                        "content": get_node_text(node, source_bytes),
                    })

            if node_type in ("tag_name", "class_name", "id_name"):
                selector = get_node_text(node, source_bytes)

                if node_type == "class_name":
                    selector = "." + selector
                elif node_type == "id_name":
                    selector = "#" + selector

                if selector not in css_selectors:
                    css_selectors.append(selector)

            elif node_type == "property_name":
                property_name = get_node_text(node, source_bytes)

                if property_name not in css_properties:
                    css_properties.append(property_name)

        if language == "sql":
            # Extract SQL statement types
            if node_type == "statement":
                statement_types = {
                    "create_table",
                    "select",
                    "insert",
                    "update",
                    "delete",
                    "alter_table",
                    "drop_table",
                }

                for child in node.children:
                    if child.type in statement_types:
                        sql_statements.append({
                            "type": child.type,
                            "name": child.type.upper(),
                            "chunk_type": "sql_statement",
                            "line": node.start_point.row + 1,
                            "end_line": node.end_point.row + 1,
                            "query": get_node_text(node, source_bytes).strip(),
                        })
                        break

            # Extract table names
            elif node_type == "object_reference":
                name_node = node.child_by_field_name("name")

                if name_node is not None:
                    table_name = get_node_text(name_node, source_bytes)

                    if table_name not in sql_tables:
                        sql_tables.append(table_name)

            # Extract column names
            elif node_type in ("column_definition", "field"):
                name_node = node.child_by_field_name("name")

                if name_node is not None:
                    column_name = get_node_text(name_node, source_bytes)

                    if column_name not in sql_columns:
                        sql_columns.append(column_name)

            # Extract column names from INSERT column lists
            elif node_type == "column":
                for child in node.children:
                    if child.type == "identifier":
                        column_name = get_node_text(child, source_bytes)

                        if column_name not in sql_columns:
                            sql_columns.append(column_name)

        # Extract functions and methods
        if node_type in FUNCTION_NODE_TYPES:
            function_name = get_node_name(node, source_bytes)

            if function_name != "anonymous":
                function_info = {
                    "name": function_name,
                    "type": node_type,
                    "line": node.start_point.row + 1,
                    "end_line": node.end_point.row + 1,
                    "source_code": get_node_text(node, source_bytes),
                }

                is_method = (
                        (
                                language == "python"
                                and node.parent is not None
                                and node.parent.parent is not None
                                and node.parent.parent.type == "class_definition"
                        )
                        or (
                                language in ("javascript", "typescript", "tsx")
                                and node_type == "method_definition"
                        )
                        or (
                                language == "java"
                                and node_type == "method_declaration"
                                and node.parent is not None
                                and node.parent.type == "class_body"
                        )
                        or (
                                language == "cpp"
                                and node_type == "function_definition"
                                and node.parent is not None
                                and node.parent.type == "field_declaration_list"
                        )
                        or (
                                language == "go"
                                and node_type == "method_declaration"
                        )
                        or (
                                language == "rust"
                                and node_type == "function_item"
                                and node.parent is not None
                                and node.parent.parent is not None
                                and node.parent.parent.type == "impl_item"
                        )
                        or (
                                language == "php"
                                and node_type == "method_declaration"
                        )
                        or (
                                language == "ruby"
                                and node_type == "method"
                                and node.parent is not None
                                and node.parent.parent is not None
                                and node.parent.parent.type == "class"
                        )
                        or (
                                language == "swift"
                                and node_type == "function_declaration"
                                and node.parent is not None
                                and node.parent.type == "class_body"
                        )
                        or (
                                language == "kotlin"
                                and node_type == "function_declaration"
                                and node.parent is not None
                                and node.parent.type == "class_body"
                        )
                )

                if is_method:
                    methods.append(function_info)
                else:
                    functions.append(function_info)

        elif node_type in CLASS_NODE_TYPES:
            class_name = get_node_name(node, source_bytes)

            if class_name != "anonymous":
                classes.append({
                    "name": class_name,
                    "type": node_type,
                    "line": node.start_point.row + 1,
                    "end_line": node.end_point.row + 1,
                    "source_code": get_node_text(node, source_bytes),
                })

        # Special handling for Go structs
        if language == "go" and node_type == "type_declaration":
            for child in node.children:
                if child.type == "type_spec":
                    for type_child in child.children:
                        if type_child.type == "struct_type":
                            name_node = child.child_by_field_name("name")

                            if name_node is not None:
                                struct_name = get_node_text(
                                    name_node,
                                    source_bytes,
                                )

                                classes.append({
                                    "name": struct_name,
                                    "type": "struct",
                                    "line": node.start_point.row + 1,
                                    "end_line": node.end_point.row + 1,
                                    "source_code": get_node_text(node, source_bytes),
                                })

        # Special handling for C structs
        if language == "c" and node_type == "struct_specifier":
            struct_name = node.child_by_field_name("name")

            if struct_name is not None:
                classes.append({
                    "name": get_node_text(struct_name, source_bytes),
                    "type": "struct",
                    "line": node.start_point.row + 1,
                    "end_line": node.end_point.row + 1,
                    "source_code": get_node_text(node, source_bytes),
                })

        # Extract imports
        if node_type in IMPORT_NODE_TYPES and node_type != "source_file":
            imports.append({
                "name": get_node_text(node, source_bytes),
                "line": node.start_point.row + 1,
            })

        # Special handling for Ruby imports
        if language == "ruby" and node_type == "call":
            method_node = node.child_by_field_name("method")

            if method_node is not None:
                method_name = get_node_text(method_node, source_bytes)

                if method_name in ("require", "require_relative"):
                    imports.append({
                        "name": get_node_text(node, source_bytes),
                        "line": node.start_point.row + 1,
                    })

        # Visit child nodes recursively
        for child in node.children:
            visit_node(child)

    visit_node(tree.root_node)

    return {
        "language": language,
        "functions": functions,
        "methods": methods,
        "classes": classes,
        "imports": imports,
        "html_tags": html_tags,
        "html_ids": html_ids,
        "html_classes": html_classes,
        "html_elements": html_elements,
        "css_selectors": css_selectors,
        "css_properties": css_properties,
        "css_rules": css_rules,
        "sql_statements": sql_statements,
        "sql_tables": sql_tables,
        "sql_columns": sql_columns,
        "has_syntax_errors": tree.root_node.has_error,
    }
