from types import SimpleNamespace

from app.services.moderation_service import ModerationService


def _fake_response(flagged, categories):
    result = SimpleNamespace(flagged=flagged, categories=SimpleNamespace(**categories))
    return SimpleNamespace(results=[result])


class TestModerationServiceFailOpen:

    def test_check_allows_content_when_no_api_key(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        service = ModerationService()

        safe, reason = service.check("some content")

        assert safe is True
        assert reason == ""

    def test_check_fails_open_when_api_raises(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        service = ModerationService()

        def _raise(input):
            raise RuntimeError("network error")

        monkeypatch.setattr(
            service, "_get_client",
            lambda: SimpleNamespace(moderations=SimpleNamespace(create=_raise)),
        )

        safe, reason = service.check("some content")

        assert safe is True
        assert reason == ""


class TestModerationServiceFlagged:

    def test_check_rejects_flagged_content(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        service = ModerationService()
        fake_client = SimpleNamespace(moderations=SimpleNamespace(
            create=lambda input: _fake_response(True, {"violence": True, "hate": False})
        ))
        monkeypatch.setattr(service, "_get_client", lambda: fake_client)

        safe, reason = service.check("bad content")

        assert safe is False
        assert reason == "violence"

    def test_check_accepts_unflagged_content(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        service = ModerationService()
        fake_client = SimpleNamespace(moderations=SimpleNamespace(
            create=lambda input: _fake_response(False, {"violence": False})
        ))
        monkeypatch.setattr(service, "_get_client", lambda: fake_client)

        safe, reason = service.check("nice content")

        assert safe is True
        assert reason == ""
