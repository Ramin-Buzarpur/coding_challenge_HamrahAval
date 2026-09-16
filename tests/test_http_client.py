from app.config import ClientConfig
from app.http_client import HttpClient


def test_http_client_creation():

    config = ClientConfig(
        hosts=["node1.example.com"]
    )

    client = HttpClient(config)

    assert client.config.timeout == 5.0