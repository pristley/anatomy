from agent_framework.observability import logger, context


def test_augment_and_format(capsys):
    # set context vars
    context.request_id_var.set("r1")
    context.correlation_id_var.set("c1")

    logger.info({"hello": "world"})
    captured = capsys.readouterr()
    out = captured.out.strip()
    # ensure request_id and correlation_id are present
    assert "request_id" in out and "correlation_id" in out

    # test plain string
    context.request_id_var.set("")
    logger.warning("a message")
    captured = capsys.readouterr()
    assert "a message" in captured.out
