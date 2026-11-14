import pytest

from app.services.analysis.tree_sitter_parser import (
    SUPPORTED_LANGUAGES,
    analyze_source_code,
)


def test_all_supported_languages_can_be_parsed():
    """Every supported language should load and parse without crashing."""

    assert len(SUPPORTED_LANGUAGES) == 16

    for language in SUPPORTED_LANGUAGES:
        result = analyze_source_code("", language)

        assert result["language"] == language
        assert result["has_syntax_errors"] is False


def test_python_function_and_class_extraction():
    code = """
class User:
    def login(self):
        return True

def calculate_total(a, b):
    return a + b
"""

    result = analyze_source_code(code, "python")

    assert "User" in [item["name"] for item in result["classes"]]
    assert "login" in [item["name"] for item in result["methods"]]
    assert "calculate_total" in [
        item["name"] for item in result["functions"]
    ]
    assert result["has_syntax_errors"] is False


def test_javascript_function_and_method_extraction():
    code = """
class User {
    login() {
        return true;
    }
}

function calculateTotal(a, b) {
    return a + b;
}
"""

    result = analyze_source_code(code, "javascript")

    assert "User" in [item["name"] for item in result["classes"]]
    assert "login" in [item["name"] for item in result["methods"]]
    assert "calculateTotal" in [
        item["name"] for item in result["functions"]
    ]
    assert result["has_syntax_errors"] is False


def test_html_extraction():
    code = """
<html>
    <body>
        <div id="container" class="main content">
            <h1>Hello</h1>
        </div>
    </body>
</html>
"""

    result = analyze_source_code(code, "html")

    assert "html" in result["html_tags"]
    assert "div" in result["html_tags"]
    assert "container" in result["html_ids"]
    assert "main" in result["html_classes"]
    assert result["has_syntax_errors"] is False


def test_css_extraction():
    code = """
body {
    margin: 0;
}

.container {
    padding: 10px;
}

#header {
    color: blue;
}
"""

    result = analyze_source_code(code, "css")

    assert "body" in result["css_selectors"]
    assert ".container" in result["css_selectors"]
    assert "#header" in result["css_selectors"]
    assert "margin" in result["css_properties"]
    assert "padding" in result["css_properties"]
    assert "color" in result["css_properties"]
    assert result["has_syntax_errors"] is False


def test_sql_extraction():
    code = """
CREATE TABLE users (
    id INT,
    name VARCHAR(100)
);

SELECT id, name FROM users;

INSERT INTO users (id, name)
VALUES (1, 'Manshi');
"""

    result = analyze_source_code(code, "sql")

    statement_types = [
        item["type"] for item in result["sql_statements"]
    ]

    assert "create_table" in statement_types
    assert "select" in statement_types
    assert "insert" in statement_types
    assert "users" in result["sql_tables"]
    assert "id" in result["sql_columns"]
    assert "name" in result["sql_columns"]
    assert result["has_syntax_errors"] is False


@pytest.mark.parametrize(
    "language",
    list(SUPPORTED_LANGUAGES.keys()),
)
def test_parser_returns_expected_result_structure(language):
    """Every language should return the same basic result structure."""

    result = analyze_source_code("", language)

    expected_keys = {
        "language",
        "functions",
        "methods",
        "classes",
        "imports",
        "html_tags",
        "html_ids",
        "html_classes",
        "css_selectors",
        "css_properties",
        "sql_statements",
        "sql_tables",
        "sql_columns",
        "has_syntax_errors",
    }

    assert expected_keys.issubset(result.keys())

    assert isinstance(result["functions"], list)
    assert isinstance(result["methods"], list)
    assert isinstance(result["classes"], list)
    assert isinstance(result["imports"], list)
