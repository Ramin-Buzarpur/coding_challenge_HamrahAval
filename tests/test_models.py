from app.models import NodeResult, OperationStatus


def test_node_result_creation():
    result = NodeResult(
        host="node1.example.com",
        status=OperationStatus.SUCCESS
    )

    assert result.host == "node1.example.com"
    assert result.status == OperationStatus.SUCCESS