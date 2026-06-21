import httpx
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from .main import app
from .dependencies import users

client = TestClient(app)

auth_user = list(users)[0]
auth = httpx.BasicAuth(username=auth_user, password=users[auth_user]["password"])


def test_read_main():
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307


# def test_hlr_get_id_sub():
#    # TODO: This
#    response = client.get("/hlr/subscriber/id/1")


def test_auth():
    """Test basic auth works for endpoint in each router"""
    response = client.get("/bsc/param/some_config_key", auth=httpx.BasicAuth(username="WRONG", password="WRONG"))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    response = client.get("/msc/active", auth=httpx.BasicAuth(username="WRONG", password="WRONG"))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    response = client.post("/hlr/subscriber/create", auth=httpx.BasicAuth(username="WRONG", password="WRONG"))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_bsc_get_params_fail():
    # TODO: This
    """Test that a valid parameter returns 200 and the expected data structure."""
    response = client.get("/bsc/param/some_config_key", auth=auth)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"data": {}}


def test_msc_get_params_success():
    response = client.get("/msc/active", auth=auth)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"data": {}}


# def test_hlr_create_success():
#     # TODO: This
#     response = client.post("/hlr/subscriber/create", data={
#         "imsi": "234990000000001",
#         "msisdn": "901",
#         "cs": True,
#         "ps": True,
#     }, auth=auth)

#     assert response.status_code == status.HTTP_200_OK
#     assert response.json() == {"data": {}}
