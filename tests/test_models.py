from app.models import NodeResult, OperationStatus


def test_node_result_creation():

    result = NodeResult(
        host="node1",
        status=OperationStatus.SUCCESS
    )

    assert result.host == "node1"
    assert result.status == OperationStatus.SUCCESS