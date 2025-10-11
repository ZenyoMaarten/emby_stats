"""Klasse voor interactie met de Emby API."""
import aiohttp
import logging

_LOGGER = logging.getLogger(__name__)

class EmbyApiError(Exception):
    """Basisuitzondering voor Emby API-fouten."""
    pass

class EmbyApiClient:
    """Klasse voor interactie met de Emby API."""

    def __init__(self, host: str, api_key: str):
        """Initialiseer de API-client."""
        self._base_url = host.rstrip('/')
        self._headers = {
            "X-MediaBrowser-Token": api_key,
            "X-Emby-Client": "HomeAssistant",
            "X-Emby-Device-Name": "HA-Stats-Integration",
            "X-Emby-Device-Id": "ha_emby_stats_unique_id",
        }

    async def _async_get(self, path: str, params: dict = None) -> dict:
        """Voert een algemene GET-aanvraag uit."""
        url = f"{self._base_url}/emby/{path}"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self._headers, params=params, timeout=10) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    elif resp.status in (401, 403):
                        raise EmbyApiError("Onjuiste API-sleutel of geen toegang.")
                    else:
                        raise EmbyApiError(f"API Fout: Status {resp.status} bij {url}")
            except aiohttp.ClientError as err:
                raise EmbyApiError(f"Netwerkfout bij verbinding met {self._base_url}: {err}")

    async def test_connection(self) -> bool:
        """Controleert of de server bereikbaar is."""
        await self._async_get("System/Info")
        return True

    async def get_users(self) -> dict[str, str]:
        """Haalt alle gebruikers op (Naam -> ID mapping)."""
        data = await self._async_get("Users")
        return {user['Name']: user['Id'] for user in data if 'Name' in user and 'Id' in user}

    async def get_libraries(self) -> dict[str, str]:
        """Haalt alle bibliotheken op (Naam -> ID mapping)."""
        data = await self._async_get("Library/MediaFolders")
        libraries = data.get('Items', [])
        return {lib['Name']: lib['Id'] for lib in libraries if 'Name' in lib and 'Id' in lib}

    async def get_library_count(self, user_id: str, library_id: str, item_type: str) -> int:
        """Haalt het aantal items van een bepaald type op."""
        path = f"Users/{user_id}/Items"
        params = {
            "ParentId": library_id,
            "Recursive": "true",
            "Limit": "1",
            "Fields": "TotalRecordCount",
            "IncludeItemTypes": item_type,
        }
        data = await self._async_get(path, params)
        return data.get('TotalRecordCount', 0)

    async def get_unwatched_count(self, user_id: str, library_id: str, item_type: str) -> int:
        """Haalt het aantal ongespeelde items van een bepaald type op."""
        path = f"Users/{user_id}/Items"
        params = {
            "ParentId": library_id,
            "Recursive": "true",
            "Limit": "1",
            "Fields": "TotalRecordCount",
            "IncludeItemTypes": item_type,
            "IsPlayed": "false",
        }
        data = await self._async_get(path, params)
        return data.get('TotalRecordCount', 0)

    async def get_latest_items(self, user_id: str, library_id: str, limit: int = 10) -> list[dict]:
        """Haalt een lijst van recent toegevoegde films/series op."""
        path = f"Users/{user_id}/Items"
        params = {
            "ParentId": library_id,
            "Recursive": "true",
            "Limit": str(limit),
            "SortBy": "DateCreated",
            "SortOrder": "Descending",
            "IncludeItemTypes": "Series,Movie",
            "Fields": "DateCreated,OriginalTitle,ImageTags",
        }
        data = await self._async_get(path, params)
        latest_items = []

        if data and data.get('Items'):
            token = self._headers.get('X-MediaBrowser-Token')
            for item in data['Items']:
                item_id = item.get('Id')
                image_tag = item.get('ImageTags', {}).get('Primary')
                image_url = f"{self._base_url}/emby/Items/{item_id}/Images/Primary?api_key={token}&tag={image_tag}&quality=90" if image_tag else None

                latest_items.append({
                    "title": item.get('Name', item.get('OriginalTitle', 'Onbekend')),
                    "date_added": item.get('DateCreated'),
                    "image_url": image_url,
                    "image_url_original": image_url,
                    "id": item_id,
                })
        return latest_items

    async def get_latest_episode_series(self, user_id: str, library_id: str, limit: int = 10) -> list[dict]:
        """Haalt series op met hun laatst toegevoegde aflevering."""
        path = f"Users/{user_id}/Items"
        params = {
            "ParentId": library_id,
            "Recursive": "true",
            "Limit": str(limit * 5),  # extra pool voor unieke series
            "SortBy": "DateCreated",
            "SortOrder": "Descending",
            "IncludeItemTypes": "Episode",
            "Fields": "DateCreated,SeriesName,SeriesId,ImageTags",
        }
        data = await self._async_get(path, params)
        series_dict = {}
        token = self._headers.get('X-MediaBrowser-Token')

        if data and data.get("Items"):
            for ep in data["Items"]:
                series_name = ep.get("SeriesName")
                series_id = ep.get("SeriesId")
                if not series_name or not series_id:
                    continue
                if series_id not in series_dict:
                    image_tag = ep.get("ImageTags", {}).get("Primary") or ep.get("SeriesPrimaryImageTag")
                    image_url = f"{self._base_url}/emby/Items/{series_id}/Images/Primary?api_key={token}&tag={image_tag}&quality=90" if image_tag else None
                    series_dict[series_id] = {
                        "title": series_name,
                        "date_added": ep.get("DateCreated"),
                        "image_url": image_url,
                        "image_url_original": image_url,
                        "id": series_id,
                    }
        # Sorteer op datum toegevoegd en return maximaal 'limit' series
        return sorted(series_dict.values(), key=lambda x: x["date_added"] or "", reverse=True)[:limit]
