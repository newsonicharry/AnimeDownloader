import time
import json
from bs4 import BeautifulSoup


class AnimeInfoScraping:
    def __init__(self, identifier: str, json_path: str, driver):
        self.identifier = identifier
        self.json_path = json_path
        self.driver = driver
        self.mal_url = ""

    @staticmethod
    def _get_img_url(soup: BeautifulSoup):
        return soup.find(class_="anime-poster").find("img").attrs["src"]

    @staticmethod
    def _get_mal_url(soup: BeautifulSoup):
        mal_link = ""

        external_links = soup.find(class_="external-links")

        if external_links is None:
            return mal_link

        for link in external_links.find_all('a'):
            if link.has_attr("href") and "myanimelist.net" in link.get('href'):
                mal_link = "https://" + link.get('href')[2:]

        return mal_link

    @staticmethod
    def _get_relations(soup: BeautifulSoup) -> dict:
        relations_data = {}

        relations = soup.find(class_="tab-content anime-relation row")
        if relations is not None:
            for relation in soup.find_all(class_="col-12 col-sm-6"):
                relationship = relation.find("h4").text
                relation_link = relation.find(class_="col-9 px-1").find("a").get('href').replace("/anime/", "")

                relations_data[relationship] = relation_link

        return relations_data

    @staticmethod
    def _get_recommendations(soup: BeautifulSoup) -> list:
        recommendations_data = []

        recommendations = soup.find(class_="tab-content anime-recommendation row")
        if recommendations is not None:
            for recommendation in soup.find_all(class_="col-12 col-sm-6 mb-3"):
                recommendation_link = recommendation.find(class_="col-9 px-1").find("a").get('href').replace("/anime/",
                                                                                                             "")
                recommendations_data.append(recommendation_link)

        return recommendations_data

    def _change_page(self, url: str) -> None:
        self.driver.set_page_load_timeout(30)
        self.driver.get(url)
        while "DDoS-Guard" in self.driver.page_source:
            time.sleep(1)

    def create_json(self) -> None:
        url = 'https://www.animepahe.ru/anime/' + self.identifier

        self._change_page(url)
        page = self.driver.page_source

        soup = BeautifulSoup(page, 'html.parser')

        img_url = self._get_img_url(soup)
        mal_link = self._get_mal_url(soup)
        self.mal_url = mal_link

        relations_data = self._get_relations(soup)
        recommendations_data = self._get_recommendations(soup)
        episode_info = self.get_episode_info()

        with open(f"{self.json_path}", 'r') as infile:
            data = json.load(infile)

            data[self.identifier] = {"episode_list": episode_info,
                                     "mal_info": {"mal_url": mal_link},
                                     "relations": relations_data,
                                     "recommendations": recommendations_data,
                                     "img_url": img_url}

            json.dump(data, open(f"{self.json_path}", 'w'))

    def get_episode_info(self) -> dict:
        starting_url = f"https://animepahe.ru/api?m=release&id={self.identifier}&sort=episode_asc&page=1"
        self._change_page(starting_url)

        response = json.loads(self.driver.page_source.replace(
            '<html><head><meta name="color-scheme" content="light dark"><meta charset="utf-8"></head><body><pre>',
            '').replace('</pre><div class="json-formatter-container"></div></body></html>', ''))

        last_page = response['last_page']

        all_episode_data = {}

        if 'data' not in response:
            return all_episode_data

        for episode in response['data']:
            episode_session = episode['session']
            episode_num = episode['episode']

            all_episode_data[episode_num] = episode_session

        for page_num in range(2, last_page + 1):
            url = f"https://animepahe.ru/api?m=release&id={self.identifier}&sort=episode_asc&page={page_num}"
            self._change_page(url)

            response = json.loads(self.driver.page_source.replace(
                '<html><head><meta name="color-scheme" content="light dark"><meta charset="utf-8"></head><body><pre>',
                '').replace('</pre><div class="json-formatter-container"></div></body></html>', ''))

            for episode in response['data']:
                episode_session = episode['session']
                episode_num = episode['episode']

                all_episode_data[episode_num] = episode_session

        return all_episode_data


if __name__ == '__main__':
    pass
    # with open("deathnote.jpg", "wb") as file:
    #     file.write(requests.get("https://i.animepahe.ru/posters/248e981d9d0020d19fa759c4dcd79fcb3fa135dcb64350402a1e6fc22186f513.jpg").content)
    # AnimeInfoScraping('a50c159e-da7d-aad4-479a-1f9aa2a582b9', 'data.json').create_json()
