import json
import os
import shutil
import time
import subprocess
from multiprocessing import Pool
from tqdm import tqdm


# the code that actually downloads the episodes
class AnimeDownload:
    def __init__(self, driver, proxy, json_path: str, videos_path: str, temp_path: str, max_sequential_download: int = 20,
                 identifier: str = "", session: str = "", get_top_series=0, max_episode_limit=0):
        self.driver = driver
        self.proxy = proxy
        self.json_path = json_path
        self.max_sequential_download = max_sequential_download
        self.videos_path = videos_path
        self.temp_path = temp_path

        self.identifier = identifier
        self.session = session
        self.top = get_top_series
        self.max_episode_limit = max_episode_limit

        if get_top_series != 0:
            self._download_top_series()
        elif identifier != "":
            self._download_series()

    # same as _download_top_series but is used for just a single series instead
    def _download_series(self) -> None:
        download_info = []

        with open(self.json_path, 'r') as json_file:
            data = json.load(json_file)

        for episode_num, session in data[self.identifier]["episode_list"].items():

            if int(episode_num) > self.max_episode_limit:
                continue

            path = f"{self.videos_path}/{self.identifier}/episodes/{episode_num}.mp4"
            if os.path.exists(path):
                continue

            page_url = f"https://animepahe.ru/play/{self.identifier}/{session}"
            self._change_page(page_url)

            m3u8 = self._get_m3u8()

            download_info.append((m3u8, self.identifier, episode_num, self.videos_path))

            if self.max_sequential_download == len(download_info):
                with Pool(processes=len(download_info)) as pool:
                    pool.map(AnimeDownload._download_m3u8, download_info)

                download_info = []

        with Pool(processes=len(download_info)) as pool:
            pool.map(AnimeDownload._download_m3u8, download_info)

    # compiles the top series and then downloads them
    def _download_top_series(self) -> None:
        top_series = self._compile_top_series()
        download_info = []

        for series in tqdm(top_series):
            identifier = series

            with open(self.json_path, 'r') as json_file:
                data = json.load(json_file)

            for episode_num, session in data[identifier]["episode_list"].items():
                #  ignores episodes that are more then the max amount to be downloaded from a single series
                if int(episode_num) > self.max_episode_limit:
                    continue
                # skips it if its already been downloaed
                path = f"{self.videos_path}/{identifier}/episodes/{episode_num}.mp4"
                if os.path.exists(path):
                    continue

                page_url = f"https://animepahe.ru/play/{identifier}/{session}"
                self._change_page(page_url)

                m3u8 = self._get_m3u8()

                # the info that the multiprocessing will use to download it
                download_info.append((m3u8, identifier, episode_num, self.videos_path, self.temp_path))

                # multiprocess the downloads on multiple cores if we've met the sequential download limit
                if self.max_sequential_download == len(download_info):
                    with Pool(processes=len(download_info)) as pool:
                        pool.map(AnimeDownload._download_m3u8, download_info)

                    download_info = []
        # used to download the rest of the episodes that are less then the sequential download limit
        # and there are no other episodes left
        with Pool(processes=len(download_info)) as pool:
            pool.map(AnimeDownload._download_m3u8, download_info)

    # gets top series based on their ranked popularity
    # (so the first item would have the identifier of the most popular series)
    def _compile_top_series(self) -> list:
        with open(self.json_path, "r") as f:
            data = json.load(f)

        all_popularity = []
        all_identifier = []

        for key, value in data.items():
            # skips series without a popularity value
            is_loaded = "mal_info" in value and "Popularity" in value["mal_info"]

            if not is_loaded:
                continue

            has_mal_data = value["mal_info"]["Popularity"] != "Unknown"

            if not has_mal_data:
                continue

            # makes sure the series actually has episodes to download
            if len(value["episode_list"].items()) == 0:
                continue

            popularity = int(value["mal_info"]["Popularity"])

            all_popularity.append(popularity)
            all_identifier.append(key)

        # sorts the identifiers based on the order that the popularity positions are in
        ranked_popularity = [x for _, x in sorted(zip(all_popularity, all_identifier))]
        ranked_popularity = ranked_popularity[:self.top]

        return ranked_popularity

    def _change_page(self, url) -> None:
        self.proxy.new_har(url)
        self.driver.get(url)

        while "DDoS-Guard" in self.driver.page_source:
            time.sleep(1)
        # clicks on the video player so that it loads the m3u8
        self.driver.execute_script("""
                const iframe = document.querySelector("iframe");
                const rect = iframe.getBoundingClientRect();
                const clickX = rect.left + rect.width / 2;
                const clickY = rect.top + rect.height / 2;
                const clickEvent = new MouseEvent('click', {
                    bubbles: true,
                    cancelable: true,
                    view: window,
                    clientX: clickX,
                    clientY: clickY
                });
                document.elementFromPoint(clickX, clickY).dispatchEvent(clickEvent);
            """)

    # waits till the m3u8 is found in the proxy to which it will get it
    def _get_m3u8(self) -> str:
        while True:
            if ".m3u8" in str(self.proxy.har):
                break
            time.sleep(.1)

        data = self.proxy.har
        m3u8 = ""

        for entry in data["log"]["entries"]:
            if ".m3u8" in str(entry):
                m3u8 = entry["request"]["url"]

        return m3u8

    # used ffmpeg to download the episode to the temp folder based on the m3u8
    @staticmethod
    def _download_m3u8(cmd) -> None:
        m3u8, identifier, episode_num, videos_path, temp_path = cmd

        temp_path = f"{temp_path}/{identifier}_{episode_num}.mp4"
        new_path = f"{videos_path}/{identifier}/episodes/{episode_num}.mp4"

        command = [
            'ffmpeg',
            '-i', m3u8,
            '-c', 'copy',
            '-loglevel', 'quiet',
            temp_path
        ]

        subprocess.run(command, check=True)

        shutil.move(temp_path, new_path)
