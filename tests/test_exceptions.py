from app.exceptions import APIRequestException


def test_api_request_exception():

    error = APIRequestException(
        "request failed"
    )

    assert str(error) == "request failed"