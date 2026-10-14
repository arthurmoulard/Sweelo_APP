import os


class ModerationService:

    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
        return self._client

    def check(self, content: str) -> tuple[bool, str]:
        """Retourne (safe, reason). Fail open si clé absente ou API indisponible."""
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            return True, ""
        try:
            response = self._get_client().moderations.create(input=content)
            result = response.results[0]
            if result.flagged:
                reason = next(
                    (cat for cat, flagged in result.categories.__dict__.items() if flagged),
                    "policy_violation",
                )
                return False, reason
            return True, ""
        except Exception:
            return True, ""
