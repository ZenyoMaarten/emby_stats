from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN
from .coordinator import EmbyStatsCoordinator
from pathlib import Path
import aiohttp
import shutil
import logging

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES = {
    "total_tvshows": {"name": "Total TV Shows", "icon": "mdi:television-classic", "unit": "items"},
    "total_movies": {"name": "Total Movies", "icon": "mdi:movie", "unit": "items"},
    "unwatched_tvshows": {"name": "Unwatched TV Shows", "icon": "mdi:eye-off", "unit": "items"},
    "unwatched_movies": {"name": "Unwatched Movies", "icon": "mdi:eye-off", "unit": "items"},
    "watched_tvshows": {"name": "Watched TV Shows", "icon": "mdi:eye", "unit": "items"},
    "watched_movies": {"name": "Watched Movies", "icon": "mdi:eye", "unit": "items"},
    "total_episodes": {"name": "Total Episodes", "icon": "mdi:file-video", "unit": "items"},
    "last_tvshows_title": {"name": "Last TV Shows", "icon": "mdi:new-box"},
    "last_movies_title": {"name": "Last Movies", "icon": "mdi:new-box"},
    "last_updated_tvshows_title": {"name": "Last Updated TV Shows", "icon": "mdi:update"},
}

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    coordinator: EmbyStatsCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    username = coordinator.user_id.lower().replace(" ", "_")
    entities = []

    for key, data in SENSOR_TYPES.items():
        full_name = f"emby_stats_{username}_{key}"
        name = data["name"]
        icon = data["icon"]
        unit = data.get("unit")
        if "last_" in key:
            if key == "last_updated_tvshows_title":
                entities.append(LatestUpdatedSeriesSensor(coordinator, key, full_name, name, icon))
            else:
                entities.append(LatestItemSensor(coordinator, key, full_name, name, icon))
        else:
            entities.append(EmbyLibraryCountSensor(coordinator, key, full_name, name, icon, unit))

    async_add_entities(entities)


class EmbyLibraryCountSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: EmbyStatsCoordinator, key: str, entity_id: str, name: str, icon: str, unit: str):
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{key}"
        self._attr_icon = icon
        self._unit = unit
        if unit == "items":
            self._attr_state_class = SensorStateClass.MEASUREMENT
        else:
            self._attr_state_class = None

    @property
    def native_value(self):
        return self.coordinator.data.get(self._key)

    @property
    def unit_of_measurement(self):
        return self._unit


class LatestItemSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: EmbyStatsCoordinator, key: str, entity_id: str, name: str, icon: str):
        super().__init__(coordinator)
        self._key = key
        self._data_key = self._key.replace('_title', '_data')
        self._attr_name = name
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{key}"
        self._attr_icon = icon
        self._poster_folder = Path(coordinator.hass.config.path("www/emby_posters"))
        self._poster_folder.mkdir(parents=True, exist_ok=True)
        empty_jpg = self._poster_folder / "empty.jpg"
        if not empty_jpg.exists():
            src = Path(__file__).parent / "empty.png"
            if src.exists():
                shutil.copy(src, empty_jpg)

    @property
    def native_value(self):
        return self.coordinator.data.get(self._key)

    @property
    def extra_state_attributes(self):
        data_list = self.coordinator.data.get(self._data_key)
        if not data_list:
            return {"status": "No recent items found"}

        for item in data_list[:10]:
            local_path = self._poster_folder / f"{item['id']}.jpg"
            if item.get("image_url_original"):
                item["image_url"] = f"/local/emby_posters/{item['id']}.jpg"
                if not local_path.exists():
                    self.coordinator.hass.async_create_task(self._download_image(item["image_url_original"], local_path))
            else:
                item["image_url"] = f"/local/emby_posters/empty.jpg"

        latest_titles_list = [f"**{i+1}.** {item['title']} ({item['date_added'][:10]})" for i, item in enumerate(data_list[:10])]
        return {
            "Top 10 Recently Added": "\n".join(latest_titles_list),
            "Most Recent Item ID": data_list[0].get('id'),
            "Most Recent Added Date": data_list[0].get('date_added'),
            "Item List (JSON)": data_list,
        }

    @property
    def entity_picture(self):
        data_list = self.coordinator.data.get(self._data_key)
        if data_list and data_list[0].get("image_url"):
            return data_list[0]["image_url"]
        return "/local/emby_posters/empty.jpg"

    async def _download_image(self, url, local_path: Path):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        with open(local_path, "wb") as f:
                            f.write(await resp.read())
        except Exception as e:
            _LOGGER.error("Error downloading poster %s: %s", url, e)


class LatestUpdatedSeriesSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: EmbyStatsCoordinator, key: str, entity_id: str, name: str, icon: str):
        super().__init__(coordinator)
        self._key = key
        self._data_key = self._key.replace('_title', '_data')
        self._attr_name = name
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{key}"
        self._attr_icon = icon
        self._poster_folder = Path(coordinator.hass.config.path("www/emby_posters"))
        self._poster_folder.mkdir(parents=True, exist_ok=True)
        empty_jpg = self._poster_folder / "empty.jpg"
        if not empty_jpg.exists():
            src = Path(__file__).parent / "empty.png"
            if src.exists():
                shutil.copy(src, empty_jpg)

    @property
    def native_value(self):
        data_list = self.coordinator.data.get(self._data_key)
        return data_list[0]['title'] if data_list else "None"

    @property
    def extra_state_attributes(self):
        data_list = self.coordinator.data.get(self._data_key)
        if not data_list:
            return {"status": "No recently updated series found"}

        # Maak dict op basis van unieke series (SeriesId)
        seen_series = set()
        unique_series = []
        for item in data_list:
            if item['id'] not in seen_series:
                seen_series.add(item['id'])
                unique_series.append(item)
            if len(unique_series) >= 10:
                break

        for item in unique_series:
            local_path = self._poster_folder / f"{item['id']}.jpg"
            if item.get("image_url_original"):
                item["image_url"] = f"/local/emby_posters/{item['id']}.jpg"
                if not local_path.exists():
                    self.coordinator.hass.async_create_task(self._download_image(item["image_url_original"], local_path))
            else:
                item["image_url"] = f"/local/emby_posters/empty.jpg"

        return {
            "Top 10 Latest Updated Series": [f"**{i+1}.** {s['title']} ({s['date_added'][:10]})" for i, s in enumerate(unique_series)],
            "Item List (JSON)": unique_series,
        }

    @property
    def entity_picture(self):
        data_list = self.coordinator.data.get(self._data_key)
        if data_list and data_list[0].get("image_url"):
            return data_list[0]["image_url"]
        return "/local/emby_posters/empty.jpg"

    async def _download_image(self, url, local_path: Path):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        with open(local_path, "wb") as f:
                            f.write(await resp.read())
        except Exception as e:
            _LOGGER.error("Error downloading poster %s: %s", url, e)
