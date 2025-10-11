"""Data Update Coordinator for the Emby Stats integration."""
import logging
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import DOMAIN, CONF_USER_ID, CONF_TV_LIBRARY_ID, CONF_MOVIE_LIBRARY_ID
from .emby_api import EmbyApiClient, EmbyApiError

_LOGGER = logging.getLogger(__name__)

class EmbyStatsCoordinator(DataUpdateCoordinator):
    """Coordinator to fetch data from Emby."""

    def __init__(self, hass, client: EmbyApiClient, config_entry):
        self.client = client
        self.user_id = config_entry.data[CONF_USER_ID]
        self.tv_library_id = config_entry.data[CONF_TV_LIBRARY_ID]
        self.movie_library_id = config_entry.data[CONF_MOVIE_LIBRARY_ID]

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=30),
        )

    async def _async_update_data(self):
        """Fetch data from the Emby API."""
        try:
            tv_count = await self.client.get_library_count(self.user_id, self.tv_library_id, "Series")
            movie_count = await self.client.get_library_count(self.user_id, self.movie_library_id, "Movie")
            unwatched_tv = await self.client.get_unwatched_count(self.user_id, self.tv_library_id, "Series")
            unwatched_movie = await self.client.get_unwatched_count(self.user_id, self.movie_library_id, "Movie")
            episode_count = await self.client.get_library_count(self.user_id, self.tv_library_id, "Episode")

            watched_tv = max(tv_count - unwatched_tv, 0)
            watched_movie = max(movie_count - unwatched_movie, 0)

            latest_tv = await self.client.get_latest_items(self.user_id, self.tv_library_id)
            latest_movie = await self.client.get_latest_items(self.user_id, self.movie_library_id)
            last_updated_tvshows = await self.client.get_latest_episode_series(self.user_id, self.tv_library_id)

            return {
                "total_tvshows": tv_count,
                "total_movies": movie_count,
                "unwatched_tvshows": unwatched_tv,
                "unwatched_movies": unwatched_movie,
                "watched_tvshows": watched_tv,
                "watched_movies": watched_movie,
                "total_episodes": episode_count,
                "last_tvshows_title": latest_tv[0]['title'] if latest_tv else "None",
                "last_movies_title": latest_movie[0]['title'] if latest_movie else "None",
                "last_tvshows_data": latest_tv,
                "last_movies_data": latest_movie,
                "last_updated_tvshows_title": last_updated_tvshows[0]['title'] if last_updated_tvshows else "None",
                "last_updated_tvshows_data": last_updated_tvshows,
            }

        except EmbyApiError as err:
            _LOGGER.error("Error fetching Emby data: %s", err)
            raise UpdateFailed(f"Error fetching Emby data: {err}")
