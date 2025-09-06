import httpx

def test_mock_server_reset_endpoint():
    response = httpx.post("http://127.0.0.1:8089/reset", timeout=5.0)
    assert response.status_code == 200
    assert response.json().get("status") == "reset"
