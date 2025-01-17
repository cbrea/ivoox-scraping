from colorama import Fore

from src.audio import Audio
from src.config import Config
from src.web_scraper import WebScraper


class DownloadPodcast:

    def __init__(self, podcast_name, episode_name, latest_episode, all_episodes, max_episodes=0):
        self.podcast_name = podcast_name.lower()
        self.episode_search_name = episode_name
        self.latest_episode = latest_episode
        self.all_episodes = all_episodes
        self.episode_name = None
        self.config = Config()
        self.podcast_url = self.get_podcast_url
        self.web_scraping = WebScraper(headless=True)
        self.audio = Audio()
        self.current_episode_index = 1
        self.max_episodes = max_episodes
        self.episode_count = 0

    @property
    def get_podcast_url(self):
        return self.config.get_podcast_url(self.podcast_name)

    def download_episode(self):
        self.web_scraping.start_connection(self.podcast_url)
        if self.all_episodes:
            self.web_scraping.driver.implicitly_wait(2)
            episode_element_in_podcast_page = ''
            current_initial_page = self.get_podcast_url
            current_page_index = 1
            exit_flag = False

            while not exit_flag:
                while episode_element_in_podcast_page is not None:
                    if self.episode_count >= self.max_episodes:
                        print('Maximum number of episodes reached')
                        exit_flag = True
                        break
                    episode_element_in_podcast_page = self.get_next_episode()
                    if episode_element_in_podcast_page is not None:
                        self.download_episode_element(episode_element_in_podcast_page)
                        self.episode_count += 1
                    # go back to initial podcast page
                    self.web_scraping.start_connection(current_initial_page)
                if exit_flag:
                    break
                print('No more episodes found in this page, trying to move to next page')
                if not self.go_to_next_page():
                    print('No more pages found in this podcast')
                    break
                current_page_index += 1
                self.current_episode_index = 1
                episode_element_in_podcast_page = ''
                print(f'Now at page {current_page_index}')
                current_initial_page = self.web_scraping.driver.current_url

        elif self.latest_episode:
            episode_element_in_podcast_page = self.get_last_episode()
            self.download_episode_element(episode_element_in_podcast_page)
        else:
            episode_element_in_podcast_page = self.search_episode()
            self.download_episode_element(episode_element_in_podcast_page)

        self.web_scraping.close_connection()

    def download_episode_element(self, episode_element_in_podcast_page):
        self.web_scraping.click_element(episode_element_in_podcast_page)
        chapter_page = self.web_scraping.find_element_by_id('dlink')
        self.web_scraping.click_element(chapter_page)
        self._get_audio_url()

    def get_last_episode(self):
        xpath_paths = [
            '//*[@id="main"]/div/div[4]/div/div/div[1]/div/div/div[1]/div[4]/p[1]/a',
           '//*[@id="main"]/div/div[3]/div/div/div[1]/div/div/div[1]/div[4]/p[1]/a'
        ]
        episode_element_in_podcast_page = None
        for xpath in xpath_paths:
            try:
                episode_element_in_podcast_page = self.web_scraping.find_element_by_xpath(xpath)
                break
            except Exception:
                print('XPath for the last episode did not match, trying a different one')
        if episode_element_in_podcast_page is None:
            raise Exception('Could not find the last episode of the podcast: {}'.format(self.podcast_name))
        self._save_chapter_name(episode_element_in_podcast_page)

        return episode_element_in_podcast_page

    def search_episode(self):
        page_count = 0
        while True:
            print('Searching episode...')
            try:
                episode_element_in_podcast_page = self.web_scraping.find_element_by_partial_text(
                    self.episode_search_name
                )
            except:
                if page_count < 10:
                    print('Searching episode...')
                    page_count += 1
                    next_page = self.web_scraping.find_element_by_xpath(
                        '//*[@id="main"]/div/div[4]/div/nav/ul/li[12]/a'
                    )
                    self.web_scraping.click_element(next_page)
                else:
                    raise Exception('No found podcast with title: {}'.format(self.episode_search_name))
            else:
                break
        self._save_chapter_name(episode_element_in_podcast_page)

        return episode_element_in_podcast_page

    def get_next_episode(self):
        episode_element_in_podcast_page = None
        xpath_paths = [
            f'//*[@id="main"]/div/div[4]/div/div/div[{self.current_episode_index}]/div/div/div[1]/div[4]/p[1]/a',
           f'//*[@id="main"]/div/div[3]/div/div/div[{self.current_episode_index}]/div/div/div[1]/div[4]/p[1]/a'
        ]
        for xpath in xpath_paths:
            try:
                episode_element_in_podcast_page = self.web_scraping.find_element_by_xpath(xpath)
                break
            except Exception:
                print('XPath for next episode did not match, trying a different one')
        if episode_element_in_podcast_page is None and self.current_episode_index < 30:
            # sometimes they include a div block with advertisement, so we need to skip it
            self.current_episode_index += 1
            return self.get_next_episode()
        print(f'Episode {self.current_episode_index} found!')
        self._save_chapter_name(episode_element_in_podcast_page)
        self.current_episode_index += 1
        return episode_element_in_podcast_page

    def go_to_next_page(self):
        next_page = None
        xpath_paths = [
            '//*[@id="main"]/div/div[4]/div/nav/ul/li[12]/a',
            '//*[@id="main"]/div/div[3]/div/nav/ul/li[12]/a'
        ]
        for xpath in xpath_paths:
            try:
                next_page = self.web_scraping.find_element_by_xpath(xpath)
                break
            except Exception:
                print('XPath for next page did not match, trying a different one')
        if next_page is None:
            print('Next element not found')
            return None
        self.web_scraping.click_element(next_page)
        return next_page

    def _save_chapter_name(self, podcast_page):
        self.episode_name = podcast_page.get_attribute('title')
        print(Fore.GREEN, 'Podcast found! ', Fore.BLUE, self.episode_name)

    def _get_audio_url(self):
        episode_audio_page = self.web_scraping.driver.current_url
        self.audio.download_episode_audio(episode_audio_page, self.episode_name)
