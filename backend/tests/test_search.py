from app.services.search.search_service import search_code_chunks


def _build_search_project(
    register_user,
    project_factory,
    file_factory,
    chunk_factory,
    email,
):
    user, _ = register_user(email)
    project = project_factory(user.id, "Search Project")

    auth_file = file_factory(
        project.id,
        "src/services/auth.py",
        language="Python",
    )
    utils_file = file_factory(
        project.id,
        "src/utils/format.py",
        language="Python",
    )

    chunk_factory(
        auth_file.id,
        name="login",
        chunk_type="function",
        content=(
            "def login(username, password):\n"
            "    token = verify_password(password)\n"
            "    return token\n"
        ),
        start_line=1,
        end_line=3,
    )

    chunk_factory(
        utils_file.id,
        name="format_currency",
        chunk_type="function",
        content=(
            "def format_currency(value):\n"
            "    return f'${value:.2f}'\n"
        ),
        start_line=10,
        end_line=11,
    )

    return user, project


def test_search_matches_function_names(
    register_user,
    project_factory,
    file_factory,
    chunk_factory,
    db_session,
):
    _, project = _build_search_project(
        register_user,
        project_factory,
        file_factory,
        chunk_factory,
        "search-name@example.com",
    )

    results = search_code_chunks(
        db=db_session,
        project_id=project.id,
        question="Where is the login function?",
    )

    assert results
    assert results[0]["name"] == "login"
    assert results[0]["file_path"] == "src/services/auth.py"


def test_search_matches_file_paths(
    register_user,
    project_factory,
    file_factory,
    chunk_factory,
    db_session,
):
    _, project = _build_search_project(
        register_user,
        project_factory,
        file_factory,
        chunk_factory,
        "search-path@example.com",
    )

    results = search_code_chunks(
        db=db_session,
        project_id=project.id,
        question="What is inside src/utils?",
    )

    assert results
    assert results[0]["file_path"] == "src/utils/format.py"


def test_search_matches_code_content(
    register_user,
    project_factory,
    file_factory,
    chunk_factory,
    db_session,
):
    _, project = _build_search_project(
        register_user,
        project_factory,
        file_factory,
        chunk_factory,
        "search-content@example.com",
    )

    results = search_code_chunks(
        db=db_session,
        project_id=project.id,
        question="Where is verify_password used?",
    )

    assert results
    assert results[0]["name"] == "login"
    assert "verify_password" in results[0]["content"]


def test_search_expands_related_concepts(
    register_user,
    project_factory,
    file_factory,
    chunk_factory,
    db_session,
):
    _, project = _build_search_project(
        register_user,
        project_factory,
        file_factory,
        chunk_factory,
        "search-related@example.com",
    )

    results = search_code_chunks(
        db=db_session,
        project_id=project.id,
        question="How is authentication implemented?",
    )

    assert results
    assert results[0]["name"] == "login"


def test_search_ignores_common_stop_words(
    register_user,
    project_factory,
    file_factory,
    chunk_factory,
    db_session,
):
    _, project = _build_search_project(
        register_user,
        project_factory,
        file_factory,
        chunk_factory,
        "search-stopwords@example.com",
    )

    results = search_code_chunks(
        db=db_session,
        project_id=project.id,
        question="What is this and how does it work?",
    )

    assert results == []


def test_search_filters_unrelated_common_word_matches(
    register_user,
    project_factory,
    file_factory,
    chunk_factory,
    db_session,
):
    user, _ = register_user("search-relevance@example.com")
    project = project_factory(user.id, "Search Relevance Project")

    sql_file = file_factory(project.id, "sql/queries.sql")
    message_file = file_factory(
        project.id,
        "javascript/src/message.js",
    )
    home_file = file_factory(project.id, "python/app.py")

    chunk_factory(
        sql_file.id,
        name="SELECT",
        chunk_type="sql_statement",
        content="SELECT id, name\nFROM users\nWHERE id > 0;\n",
        start_line=1,
        end_line=3,
    )
    chunk_factory(
        sql_file.id,
        name="INSERT",
        chunk_type="sql_statement",
        content="INSERT INTO users (id, name)\nVALUES (1, 'CodeAtlas');\n",
        start_line=5,
        end_line=6,
    )
    chunk_factory(
        message_file.id,
        name="getMessage",
        content="function getMessage() {\n  return 'hello';\n}\n",
        start_line=1,
        end_line=3,
    )
    chunk_factory(
        home_file.id,
        name="home",
        content="def home():\n    return 'welcome home'\n",
        start_line=7,
        end_line=8,
    )

    results = search_code_chunks(
        db=db_session,
        project_id=project.id,
        question="tell me the sql queries present in this project",
    )

    assert results
    assert {result["file_path"] for result in results} == {
        "sql/queries.sql"
    }
    assert {result["name"] for result in results} == {
        "SELECT",
        "INSERT",
    }


def test_search_ignores_generic_code_words(
    register_user,
    project_factory,
    file_factory,
    chunk_factory,
    db_session,
):
    _, project = _build_search_project(
        register_user,
        project_factory,
        file_factory,
        chunk_factory,
        "search-generic-words@example.com",
    )

    # "function" alone must not match every function in the project.
    results = search_code_chunks(
        db=db_session,
        project_id=project.id,
        question="Where is the signup function?",
    )

    assert results == []


def test_search_is_limited_to_the_requested_project(
    register_user,
    project_factory,
    file_factory,
    chunk_factory,
    db_session,
):
    user, _ = register_user("search-isolation@example.com")

    first_project = project_factory(user.id, "Search Project One")
    first_file = file_factory(
        first_project.id,
        "first/secret_handler.py",
    )
    chunk_factory(
        first_file.id,
        name="secret_handler",
        content="def secret_handler():\n    pass\n",
    )

    second_project = project_factory(user.id, "Search Project Two")
    second_file = file_factory(
        second_project.id,
        "second/public_handler.py",
    )
    chunk_factory(
        second_file.id,
        name="public_handler",
        content="def public_handler():\n    pass\n",
    )

    results = search_code_chunks(
        db=db_session,
        project_id=second_project.id,
        question="handler",
    )

    assert results
    assert {result["file_path"] for result in results} == {
        "second/public_handler.py"
    }
    assert all(
        result["name"] != "secret_handler"
        for result in results
    )


def test_search_respects_limit(
    register_user,
    project_factory,
    file_factory,
    chunk_factory,
    db_session,
):
    user, _ = register_user("search-limit@example.com")
    project = project_factory(user.id, "Search Limit Project")
    source = file_factory(project.id, "main.py")

    for index in range(5):
        chunk_factory(
            source.id,
            name=f"handler_{index}",
            content=f"def handler_{index}():\n    return {index}\n",
            start_line=index * 10 + 1,
            end_line=index * 10 + 2,
        )

    results = search_code_chunks(
        db=db_session,
        project_id=project.id,
        question="handler",
        limit=3,
    )

    assert len(results) == 3


def test_search_returns_empty_for_blank_question(
    register_user,
    project_factory,
    file_factory,
    chunk_factory,
    db_session,
):
    _, project = _build_search_project(
        register_user,
        project_factory,
        file_factory,
        chunk_factory,
        "search-blank@example.com",
    )

    results = search_code_chunks(
        db=db_session,
        project_id=project.id,
        question="   ?   ",
    )

    assert results == []
