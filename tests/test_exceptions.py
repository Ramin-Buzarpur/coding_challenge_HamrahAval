from app.exceptions import APIRequestException


def test_custom_exception():

    error = APIRequestException("failed")

    assert str(error) == "failed"