import time

from bs4 import BeautifulSoup

import utils


# credit to Hernan4444
# https://github.com/Hernan4444/MyAnimeList-Database/blob/master/All%20Scrapping%20process.ipynb
# slightly modified, though im very thankful I didn't have to make it
# this is intended to scrape all the data from myanimelist about a certain series
class MalScraping:

    def __init__(self, mal_url, driver):
        self.mal_url = mal_url
        self.driver = driver
        self.KEYS = ['Name', 'Score', 'English name', 'Japanese name', 'Type', 'Episodes',
                     'Aired', 'Premiered', 'Producers', 'Licensors', 'Studios', 'Source', 'Duration', 'Rating',
                     'Ranked', 'Popularity', 'Members', 'Favorites', 'Synopsis', "Status"]

    @staticmethod
    def __get_synopsis(info):
        return info.find('p', {'itemprop': 'description'}).text.strip().replace("\n", "")

    @staticmethod
    def __get_name(info):
        return info.find("h1", {"class": "title-name h1_bold_none"}).text.strip()

    @staticmethod
    def __get_english_name(info):
        span = info.find_all("span", {"class": "dark_text"})
        return span.parent.text.strip()

    @staticmethod
    def __get_table(a_soup):
        return a_soup.find("div", {"class": "spaceit_pad po-r js-statistics-info di-ib"})

    @staticmethod
    def __get_score(stats):
        score = stats.find("span", {"itemprop": "ratingValue"})
        if score is None:
            return "Unknown"
        return score.text.strip()

    @staticmethod
    def __get_genre(sum_info):
        text = ", ".join(
            [x.text.strip() for x in sum_info.find_all("span", {"itemprop": "genre"})]
        )
        return text

    @staticmethod
    def __get_description(sum_info):
        return sum_info.find("td", {"class": "borderClass", "width": "225"})

    @staticmethod
    def __get_all_stats(soup):
        return soup.find("div", {"id": "horiznav_nav"}).parent.find_all(
            "div", {"class": "spaceit_pad"}
        )

    def __get_page(self):
        self.driver.get(self.mal_url)

        while True:
            if "captcha-container" in self.driver.page_source:
                time.sleep(1)
            else:
                break

    def get_info_anime(self):

        self.__get_page()

        # self.driver.get(self.mal_url)
        anime_info = self.driver.page_source

        soup = BeautifulSoup(anime_info, "html.parser")

        anime_info = {key: "Unknown" for key in self.KEYS}

        # if the data failed to load then just set everything as "Unknown"
        try:

            stats = self.__get_table(soup)
            description = self.__get_description(soup)

            anime_info["Name"] = self.__get_name(soup)
            anime_info["Score"] = self.__get_score(stats)
            anime_info["Synopsis"] = self.__get_synopsis(soup)

        except Exception as e:
            # print("error")
            return {key: "Unknown" for key in self.KEYS}

        # anime_info["MAL_ID"] = anime_id

        for d in description.find_all("span", {"class": "dark_text"}):
            information = [x.strip().replace(" ", " ") for x in d.parent.text.split(":")]
            category, value = information[0], ":".join(information[1:])
            value.replace("\t", "")

            if category in ["Broadcast", "Synonyms", "Score", "Demographic"]:
                continue

            if category in ["Ranked"]:
                value = value.split("\n")[0]
            if category in ["Producers", "Licensors", "Studios"]:
                value = ", ".join([x.strip() for x in value.split(",")])
            if category in ["Ranked", "Popularity"]:
                value = value.replace("#", "")
            if category in ["Members", "Favorites"]:
                value = value.replace(",", "")
            if category in ["Themes", "Genres"]:
                value = value.replace("         ", "")
                value = value.split(",")

                for i, theme in enumerate(value):
                    value[i] = theme[:len(theme) // 2]

            # if category in ["Aired"]:

            if category in ["English", "Japanese"]:
                category += " name"

            anime_info[category] = value

        for key, value in anime_info.items():
            if str(value) in ["?", "None found, add some", "None", "N/A", "Not available"]:
                anime_info[key] = "Unknown"

        return anime_info


if __name__ == '__main__':

    anime = MalScraping("chainsaw.html")
    info = anime.get_info_anime()

    for key, value in info.items():
        print(f"{key}: {value}")

    # print(anime.get_info_anime())
