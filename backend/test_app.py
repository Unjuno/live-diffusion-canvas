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


def test_noise_brush_is_only_visible_when_active_with_a_mask():
    session_id = "noise-session"
    sessions[session_id] = Session(seed=5)
    active = intervention(Intervention(
        requestId=1,
        sessionId=session_id,
        noiseBrushActive=True,
        activeNoiseMask="[[20,30],[25,35]]",
    ))
    released = intervention(Intervention(
        requestId=2,
        sessionId=session_id,
        noiseBrushActive=False,
        activeNoiseMask="[[20,30],[25,35]]",
    ))
    assert "f06b5d" in active.previewImage
    assert "f06b5d" not in released.previewImage


def test_guide_and_imported_image_are_inspectable_in_mock_preview():
    session_id = "guide-session"
    sessions[session_id] = Session(seed=6)
    response = intervention(Intervention(
        requestId=3,
        sessionId=session_id,
        guideComposite="data:image/svg+xml,guide",
    ))
    assert "20c997" in response.previewImage
    assert "GUIDE ACTIVE" in response.previewImage


def test_intervention_rejects_out_of_range_runtime_settings():
    with pytest.raises(ValueError):
        Intervention(requestId=4, sessionId="boundary", guideInfluence=1.1)
    with pytest.raises(ValueError):
        Intervention(requestId=5, sessionId="boundary", updatesToAdvance=0)
    with pytest.raises(ValueError):
        Intervention(requestId=51, sessionId="boundary", explorationRewindFrames=0)
    with pytest.raises(ValueError):
        Intervention(requestId=52, sessionId="boundary", explorationNoiseSteps=9)


def test_finish_advances_the_requested_number_of_mock_updates():
    session_id = "finish-multi-session"
    sessions[session_id] = Session(seed=7)
    response = intervention(Intervention(
        requestId=6,
        sessionId=session_id,
        phase="finish",
        updatesToAdvance=3,
    ))
    assert response.requestId == 6
    assert sessions[session_id].tick == 3
