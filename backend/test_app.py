import pytest

from backend.app import HTTPException, Intervention, Session, finish, health, intervention, sessions


def test_health_reports_stateful_runtime():
    result = health()
    assert result["status"] == "ok"
    assert result["runtime"] == "mock-stateful"
    assert result["model"] == "mock-stateful-v0.1"
    assert result["modelReady"] is True


def test_intervention_advances_existing_session_and_preserves_request_id():
    session_id = "test-session"
    sessions[session_id] = Session(seed=9)
    response = intervention(Intervention(requestId=17, sessionId=session_id, prompt="test"))
    assert response.requestId == 17
    assert response.sessionId == session_id
    assert response.seed == 9
    assert sessions[session_id].tick == 1
    assert response.previewImage.startswith("data:image/svg+xml,")


def test_finish_reuses_stateful_intervention_path():
    session_id = "finish-session"
    sessions[session_id] = Session(seed=3)
    response = finish(Intervention(requestId=2, sessionId=session_id, prompt="finish", phase="explore"))
    assert response.requestId == 2
    assert sessions[session_id].tick == 1


def test_intervention_honors_multiple_updates_in_mock_runtime():
    session_id = "multi-update-session"
    sessions[session_id] = Session(seed=4)
    response = intervention(Intervention(
        requestId=3,
        sessionId=session_id,
        prompt="multi",
        updatesToAdvance=3,
    ))
    assert sessions[session_id].tick == 3
    assert response.previewImage.startswith("data:image/svg+xml,")


def test_intervention_rejects_unknown_session_instead_of_resetting_state():
    with pytest.raises(HTTPException) as error:
        intervention(Intervention(requestId=99, sessionId="missing-session"))
    assert error.value.status_code == 404
