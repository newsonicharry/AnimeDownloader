import os.path
from bs4 import BeautifulSoup
from string import ascii_uppercase as uppercase
import json
from utils import get_page_source


# gets all the identifiers to the different anime series from animepahe
class FindSeries:
    def __init__(self, output):
        self.url = "https://animepahe.ru/anime"
        self.output = output

    # scrapes links from the webpage
    @staticmethod
    def __scrape_links(page):
        soup = BeautifulSoup(page, 'html.parser')
        links = []

        for letter in uppercase:
            for section in soup.find_all(id=letter):
                for anime in section.find_all(class_="col-12 col-md-6"):
                    link = anime.find("a").attrs["href"].replace("/anime/", "")

                    links.append(link)

        return links

    # adds the data to the data.json file
    def scrape_anime(self):
        # allows for it to not override existing data if it already exists
        original_data = {}
        if os.path.exists(self.output):
            with open(self.output, 'r', encoding="utf-8") as infile:
                original_data = json.load(infile)

        page = get_page_source(self.url)
        links = self.__scrape_links(page)

        data = {link: {} for link in links}
        data.update(original_data)

        with open(self.output, "w") as file:
            json.dump(data, file, indent=4)


if __name__ == '__main__':
    scraper = FindSeries("data.json")
    scraper.scrape_anime()
