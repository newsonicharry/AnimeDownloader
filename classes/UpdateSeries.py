import json
import time

import utils


class UpdateSeries:
    def __init__(self, driver, json_path: str, update_all_episodes: bool = False, identifier: str = ""):
        self.driver = driver
        self.update_all_episodes = update_all_episodes
        self.json_path = json_path
        self.identifier = identifier

        if update_all_episodes:
            self._update_all_episodes()
        if self.identifier != "":
            episode_data = self._get_series_episodes_data(self.identifier)
            self._update_json_episodes(self.identifier, episode_data)

    # gets episode data from series that are currently still airing
    def _update_all_episodes(self) -> None:
        with open(self.json_path, "r") as f:
            all_data = json.load(f)

        for identifier, series_data in all_data.items():

            if "Status" not in series_data["mal_info"]:
                continue

            status = series_data["mal_info"]["Status"]

            if status == "Currently Airing":
                episode_data = self._get_series_episodes_data(identifier)
                self._update_json_episodes(identifier, episode_data)
                # updates the status if the series is now finished
                utils.update_mal_info(self.json_path, series_data["mal_info"]["mal_url"], self.driver, identifier)

    # find all the episode data of a series
    def _get_series_episodes_data(self, identifier: str) -> dict:
        # converts the json of the episode data into a usable dictionary
        def _get_episode_page_data(page_data: dict) -> dict:
            episodes_data = {}

            for episode in page_data['data']:
                episode_session = episode['session']
                episode_num = episode['episode']

                episodes_data[episode_num] = episode_session

            return episodes_data
        # get the webpage of where the data is loaded and parses it into a dict
        def _get_response() -> dict:
            return json.loads(self.driver.page_source.replace(
                '<html><head><meta name="color-scheme" content="light dark"><meta charset="utf-8"></head><body><pre>',
                '').replace('</pre><div class="json-formatter-container"></div></body></html>', ''))

        starting_url = f"https://animepahe.ru/api?m=release&id={identifier}&sort=episode_asc&page=1"
        self._change_page(starting_url)

        response = _get_response()
        # the number of the last page where data is stored (episode data may be stored on multiple pages)
        last_page = response['last_page']

        all_episode_data = {}
        # if there is no data within it (very rare that this will happen)
        if 'data' not in response:
            return all_episode_data

        all_episode_data.update(_get_episode_page_data(response))

        # loops through all the different pages of episode data and adds it to all_episode_data
        for page_num in range(2, last_page + 1):
            url = f"https://animepahe.ru/api?m=release&id={identifier}&sort=episode_asc&page={page_num}"
            self._change_page(url)

            response = _get_response()

            all_episode_data.update(_get_episode_page_data(response))

        return all_episode_data

    # takes in episode data and updates the old episode data with the new episode data
    def _update_json_episodes(self, identifier: str, episodes: dict) -> None:
        with open(self.json_path, "r") as f:
            all_data = json.load(f)

        episode_list = all_data[identifier]["episode_list"]
        episode_list.update(episodes)

        all_data[identifier]["episode_list"] = episode_list

        with open(self.json_path, "w") as f:
            json.dump(all_data, f)

    # allows for undetected selenium to change pages without accidentally getting the data from the temporary ddos page
    def _change_page(self, url: str) -> None:
        self.driver.set_page_load_timeout(30)
        self.driver.get(url)
        while "DDoS-Guard" in self.driver.page_source:
            time.sleep(1)
