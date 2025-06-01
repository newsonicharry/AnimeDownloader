import argparse
import json
import os
import time
import requests
import undetected_chromedriver as uc
from browsermobproxy import Server
from selenium.webdriver.common.options import PageLoadStrategy
from tqdm import tqdm
from yaspin import yaspin
import utils
from classes.AnimeDownload import AnimeDownload
from classes.FindSeries import FindSeries
from classes.ScrapeInfo import AnimeInfoScraping
from classes.UpdateSeries import UpdateSeries


def has_basic_data(data):
    for key, value in data.items():
        if key == "mal_info":
            return True

    return False


def has_mal_info(data):
    for key, value in data.items():

        if key == "mal_info":

            if "Popularity" in data["mal_info"] and "Status" in data["mal_info"]:

                if data["mal_info"]["Popularity"] != "Unknown":
                    return True

    return False


def download_img(url, path):
    if os.path.exists(path):
        return

    img = requests.get(url)

    with open(path, 'wb') as f:
        f.write(img.content)
        f.close()


if __name__ == '__main__':

    # allows for command line arguments, can't be run outside of a console
    parser = argparse.ArgumentParser(description="a mass anime downloader")

    parser.add_argument("video_path", help="folder location for the directory to be built")
    parser.add_argument("json_path", help="path where the data.json file to be built")
    parser.add_argument("temp_path",
                        help="path for the temp folder to be be made (used for temporary storage of episodes)")

    parser.add_argument("--start", action="store_true", help="starts collecting series information")
    parser.add_argument("--update_all", action="store_true",
                        help="updates all incomplete series and episode information")

    parser.add_argument("--download_series", type=str, help="identifier of the series to be downloaded")
    parser.add_argument("--download_top_popularity", type=int,
                        help="downloads series based on their popularity from most popular to the specified number")
    parser.add_argument("--episode_limit", type=int,
                        help="max amount of episodes that will be downloaded from a series (the default is 40)")
    parser.add_argument("--sequential_download_limit", type=int,
                        help="max concurrent episodes that will be downloaded at once (the default is 25)")

    args = parser.parse_args()

    # loads undetected selenium in order to get webpage data
    with yaspin(text="Loading Browser..."):
        server = Server("C:/browsermob-proxy-2.1.4/bin/browsermob-proxy.bat")
        server.start()
        proxy = server.create_proxy()

        chrome_options = uc.ChromeOptions()
        chrome_options.add_argument('--proxy-server={0}'.format(proxy.proxy))
        chrome_options.add_argument(
            "--disable-extensions-except=C:/Users/Harry/PycharmProjects/FinalAnimeDownlaoder/adblock/simpleadblock")
        # ad blocker to avoid ads getting in the way of the automation and decrease loading times
        chrome_options.add_argument(
            f"--load-extension=C:/Users/Harry/PycharmProjects/FinalAnimeDownlaoder/adblock/simpleadblock")
        chrome_options.add_argument('--ignore-certificate-errors')  # the proxy gives certificate errors
        chrome_options.add_argument("--start-maximized")

        chrome_options.page_load_strategy = PageLoadStrategy.eager

        driver = uc.Chrome(
            headless=False,
            use_subprocess=True,
            options=chrome_options
        )

        # allows time for the extension to load
        time.sleep(15)

    json_path = args.json_path + "/data.json"
    videos_path = args.video_path + "/videos"
    temp_path = args.temp_path + "/temp"

    if not os.path.exists(temp_path):
        os.makedirs(temp_path)

    # arguments from the command line
    if args.update_all:
        UpdateSeries(driver, json_path, update_all_episodes=True)

    if args.download_top_popularity is not None:
        print("Downloading top series...")
        AnimeDownload(driver, proxy, json_path, videos_path, temp_path,
                      max_sequential_download=args.sequential_download_limit or 25,
                      max_episode_limit=args.episode_limit or 40,
                      get_top_series=args.download_top_popularity)

    if args.download_series is not None:
        print("Downloading series...")
        AnimeDownload(driver, proxy, json_path, videos_path, temp_path,
                      max_sequential_download=args.sequential_download_limit or 25,
                      max_episode_limit=args.episode_limit or 40,
                      identifier=args.download_series)

    if args.start:

        while True:
            # sometimes a webpage wont properly load and causes an error, though its pretty rare, so restart it
            try:
                # goes to animepahe and get the identifiers to all anime series
                with yaspin(text="Fetching all series..."):
                    findSeries = FindSeries(json_path)
                    findSeries.scrape_anime()

                print("Fetching series data...")

                with open(json_path, 'r') as f:
                    data = json.load(f)
                    f.close()
                # tqdm to show the loading bar
                for key, value in tqdm(data.items()):
                    # if there is no data inside the identifier
                    if not has_basic_data(value):
                        animeInfoScraping = AnimeInfoScraping(key, json_path, driver)
                        animeInfoScraping.create_json()

                        if animeInfoScraping.mal_url == "":
                            continue

                        utils.update_mal_info(json_path, animeInfoScraping.mal_url, driver, key)
                    elif not has_mal_info(value):
                        # if there is data in the identifier but the myanimelist data failed to load
                        if value["mal_info"]["mal_url"] != "":
                            utils.update_mal_info(json_path, value["mal_info"]["mal_url"], driver, key)

                break

            except Exception as e:
                print("An exception has occurred, restarting the driver...")
                print(e)

        # creates the file directory to store all the episodes and posters
        with yaspin(text="Building file directory..."):
            with open(json_path, 'r') as infile:
                data = json.load(infile)
                infile.close()

                for k, v in data.items():
                    path = f"{videos_path}/videos/{k}/episodes"

                    if not os.path.exists(path):
                        os.makedirs(path)

        print("Downloading posters...")
        # downloads the posters (so the anime series thumbnail)
        with open(json_path, 'r') as infile:
            data = json.load(infile)
            infile.close()

            for k, v in tqdm(data.items()):
                if "img_url" in v:
                    download_img(v["img_url"], f"{videos_path}/{k}/poster.jpg")

    driver.quit()
