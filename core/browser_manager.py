from playwright.sync_api import sync_playwright
from config.settings import HEADLESS

class BrowserManager:

    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None

    def start(self):

        self.playwright = sync_playwright().start()

        self.browser = self.playwright.chromium.launch(
            headless=HEADLESS
        )

        self.page = self.browser.new_page()

        return self.page

    def close(self):

        self.browser.close()
        self.playwright.stop()