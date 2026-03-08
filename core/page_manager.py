from config.settings import BASE_URL


class PageManager:

    def __init__(self, page, logger):
        self.page = page
        self.logger = logger

    def open_home(self):
        self.navigate(BASE_URL)

    def navigate(self, url):

        try:

            self.logger.info(f"Navigating to {url}")

            self.page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=60000
            )

        except Exception as e:

            self.logger.error(f"Navigation failed for {url}")
            raise e