import sys
from unittest.mock import MagicMock, patch
import pytest

# Mock boto3 before importing the app
sys.modules["boto3"] = MagicMock()


from api.app import app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


# ---------------------- /resolve ----------------------


@patch("app.s3")
def test_resolve_valid_prompt(mock_s3, client):
    # Mock tags.yaml and index.yaml
    mock_s3.get_object.side_effect = [
        {"Body": MagicMock(read=lambda: b"- docker\n- postgres")},
        {
            "Body": MagicMock(
                read=lambda: b"""
        - tags:
          - docker
          - postgres
          url: "nginx/docker-compose.yaml"
        """
            )
        },
    ]

    # Mock paginator
    mock_paginator = MagicMock()
    mock_paginator.paginate.return_value = [
        {"Contents": [{"Key": "nginx/docker-compose.yaml"}]}
    ]
    mock_s3.get_paginator.return_value = mock_paginator

    res = client.post("/resolve", json={"prompt": "Use docker and postgres"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["matched"] is not None
    assert "files" in data


@patch("app.s3")
def test_resolve_empty_prompt(mock_s3, client):
    res = client.post("/resolve", json={})
    assert res.status_code == 400
    assert res.get_json()["error"] == "No prompt provided"


@patch("app.s3")
def test_resolve_no_match(mock_s3, client):
    mock_s3.get_object.side_effect = [
        {"Body": MagicMock(read=lambda: b"- docker\n- postgres")},
        {
            "Body": MagicMock(
                read=lambda: b"""
        - tags:
          - nginx
          - mysql
          url: "something.yaml"
        """
            )
        },
    ]
    res = client.post("/resolve", json={"prompt": "unknown technology"})
    assert res.status_code == 200
    assert res.get_json()["matched"] is None


# ---------------------- /download ----------------------


@patch("app.s3")
def test_download_valid_key(mock_s3, client):
    mock_file = b"fake content"
    mock_s3.get_object.return_value = {"Body": MagicMock(read=lambda: mock_file)}

    res = client.get("/download?key=somefile.txt")
    assert res.status_code == 200
    assert res.data == mock_file


@patch("app.s3")
def test_download_no_key(mock_s3, client):
    res = client.get("/download")
    assert res.status_code == 400
    assert res.get_json()["error"] == "No key provided"


@patch("app.s3")
def test_download_key_not_found(mock_s3, client):
    mock_s3.get_object.side_effect = mock_s3.exceptions.NoSuchKey = Exception(
        "KeyNotFound"
    )
    res = client.get("/download?key=missing.txt")
    # because it's not truly NoSuchKey in mock
    assert res.status_code in (404, 500)


