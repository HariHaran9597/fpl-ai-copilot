import logging
import time
from functools import lru_cache
import httpx
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class FPLAPIError(Exception):
    """Custom exception when FPL API crashes or rate limits."""
    pass

class FPLClient:
    BASE_URL = "https://fantasy.premierleague.com/api"

    def __init__(self, timeout: int = 15, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries

    def _get(self, endpoint: str) -> Any:
        url = f"{self.BASE_URL}/{endpoint}"
        for attempt in range(self.max_retries):
            try:
                headers = {"User-Agent": "Mozilla/5.0"}
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.get(url, headers=headers)
                    response.raise_for_status()
                    return response.json()
            except httpx.HTTPError as e:
                logger.warning(f"Attempt {attempt+1}/{self.max_retries} failed for {url}: {e}")
                if attempt == self.max_retries - 1:
                    raise FPLAPIError(f"Failed to fetch data from FPL API: {e}")
                time.sleep(2 ** attempt)
        return {}

    @lru_cache(maxsize=1)
    def get_bootstrap_static(self) -> Dict[str, Any]:
        return self._get("bootstrap-static/")

    @lru_cache(maxsize=1)
    def get_fixtures(self) -> List[Dict[str, Any]]:
        return self._get("fixtures/")

    @lru_cache(maxsize=1000)
    def get_element_summary(self, element_id: int) -> Dict[str, Any]:
        return self._get(f"element-summary/{element_id}/")

    def get_manager_info(self, team_id: int) -> Dict[str, Any]:
        return self._get(f"entry/{team_id}/")

    def get_manager_picks(self, team_id: int, event_id: int) -> Dict[str, Any]:
        return self._get(f"entry/{team_id}/event/{event_id}/picks/")

    def get_manager_transfers(self, team_id: int) -> List[Dict[str, Any]]:
        return self._get(f"entry/{team_id}/transfers/")

    def get_manager_history(self, team_id: int) -> Dict[str, Any]:
        """Fetches manager's GW-by-GW history and chips used."""
        return self._get(f"entry/{team_id}/history/")
