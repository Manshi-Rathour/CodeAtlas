def test_graph_returns_all_files_as_nodes(
    client,
    register_user,
    project_factory,
    file_factory,
):
    user, headers = register_user("graph-nodes@example.com")
    project = project_factory(user.id, "Graph Nodes Project")

    main = file_factory(project.id, "src/main.py")
    isolated = file_factory(project.id, "src/isolated.py")

    response = client.get(
        f"/api/projects/{project.id}/graph",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["project_id"] == project.id
    assert data["project_name"] == "Graph Nodes Project"
    assert data["total_nodes"] == 2
    assert data["total_edges"] == 0

    nodes_by_id = {node["id"]: node for node in data["nodes"]}

    assert nodes_by_id[main.id]["file_path"] == "src/main.py"
    assert nodes_by_id[main.id]["label"] == "main.py"
    assert nodes_by_id[main.id]["language"] == "Python"
    assert nodes_by_id[isolated.id]["file_path"] == "src/isolated.py"


def test_graph_builds_edges_from_resolved_dependencies(
    client,
    register_user,
    project_factory,
    file_factory,
    dependency_factory,
):
    user, headers = register_user("graph-edges@example.com")
    project = project_factory(user.id, "Graph Edge Project")

    main = file_factory(project.id, "src/main.py")
    helpers = file_factory(project.id, "src/helpers.py")

    dependency = dependency_factory(
        project_id=project.id,
        file_id=main.id,
        dependency_name="helpers",
        dependency_type="import",
        line_number=4,
        resolved_file_id=helpers.id,
    )

    response = client.get(
        f"/api/projects/{project.id}/graph",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_nodes"] == 2
    assert data["total_edges"] == 1

    edge = data["edges"][0]

    assert edge["id"] == dependency.id
    assert edge["source"] == main.id
    assert edge["target"] == helpers.id
    assert edge["dependency"] == "helpers"
    assert edge["type"] == "import"
    assert edge["line_number"] == 4


def test_graph_ignores_external_and_unresolved_dependencies(
    client,
    register_user,
    project_factory,
    file_factory,
    dependency_factory,
):
    user, headers = register_user("graph-external@example.com")
    project = project_factory(user.id, "External Project")

    main = file_factory(project.id, "main.py")

    dependency_factory(
        project_id=project.id,
        file_id=main.id,
        dependency_name="fastapi",
        resolved_file_id=None,
    )

    dependency_factory(
        project_id=project.id,
        file_id=main.id,
        dependency_name="requests",
        resolved_file_id=None,
    )

    response = client.get(
        f"/api/projects/{project.id}/graph",
        headers=headers,
    )

    data = response.json()

    assert data["total_nodes"] == 1
    assert data["total_edges"] == 0
    assert data["edges"] == []


def test_graph_preserves_multiple_legitimate_dependencies(
    client,
    register_user,
    project_factory,
    file_factory,
    dependency_factory,
):
    user, headers = register_user("graph-multiple@example.com")
    project = project_factory(user.id, "Multiple Dependencies")

    main = file_factory(project.id, "main.py")
    utils = file_factory(project.id, "utils.py")

    dependency_factory(
        project_id=project.id,
        file_id=main.id,
        dependency_name="parse",
        line_number=1,
        resolved_file_id=utils.id,
    )

    dependency_factory(
        project_id=project.id,
        file_id=main.id,
        dependency_name="format",
        line_number=2,
        resolved_file_id=utils.id,
    )

    response = client.get(
        f"/api/projects/{project.id}/graph",
        headers=headers,
    )

    data = response.json()

    assert data["total_edges"] == 2

    targets = {edge["target"] for edge in data["edges"]}
    names = {edge["dependency"] for edge in data["edges"]}

    assert targets == {utils.id}
    assert names == {"parse", "format"}


def test_graph_avoids_duplicate_edges(
    client,
    register_user,
    project_factory,
    file_factory,
    dependency_factory,
):
    user, headers = register_user("graph-duplicates@example.com")
    project = project_factory(user.id, "Duplicate Dependencies")

    main = file_factory(project.id, "main.py")
    utils = file_factory(project.id, "utils.py")

    for _ in range(3):
        dependency_factory(
            project_id=project.id,
            file_id=main.id,
            dependency_name="utils",
            dependency_type="import",
            line_number=1,
            resolved_file_id=utils.id,
        )

    response = client.get(
        f"/api/projects/{project.id}/graph",
        headers=headers,
    )

    data = response.json()

    assert data["total_edges"] == 1


def test_graph_ignores_self_imports(
    client,
    register_user,
    project_factory,
    file_factory,
    dependency_factory,
):
    user, headers = register_user("graph-self@example.com")
    project = project_factory(user.id, "Self Import")

    main = file_factory(project.id, "main.py")

    dependency_factory(
        project_id=project.id,
        file_id=main.id,
        dependency_name="main",
        resolved_file_id=main.id,
    )

    response = client.get(
        f"/api/projects/{project.id}/graph",
        headers=headers,
    )

    data = response.json()

    assert data["total_nodes"] == 1
    assert data["total_edges"] == 0


def test_graph_returns_empty_graph_for_project_without_files(
    client,
    register_user,
    project_factory,
):
    user, headers = register_user("graph-empty@example.com")
    project = project_factory(user.id, "Empty Project")

    response = client.get(
        f"/api/projects/{project.id}/graph",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["nodes"] == []
    assert data["edges"] == []
    assert data["total_nodes"] == 0
    assert data["total_edges"] == 0


def test_graph_rejects_other_users(
    client,
    register_user,
    project_factory,
    file_factory,
):
    owner, _ = register_user("graph-owner@example.com")
    _, other_headers = register_user("graph-other@example.com")

    project = project_factory(owner.id, "Private Graph")
    file_factory(project.id, "secret.py")

    response = client.get(
        f"/api/projects/{project.id}/graph",
        headers=other_headers,
    )

    assert response.status_code == 404


def test_graph_requires_authentication(client, register_user, project_factory):
    user, _ = register_user("graph-auth@example.com")
    project = project_factory(user.id, "Auth Graph")

    response = client.get(f"/api/projects/{project.id}/graph")

    assert response.status_code == 401
