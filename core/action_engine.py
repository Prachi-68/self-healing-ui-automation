import json
from utils.screenshot import capture_screenshot
from healing.dom_capture import capture_dom
from healing.deterministic_healer import DeterministicHealer


class ActionEngine:

    def __init__(self, page, logger, page_name):

        self.page = page
        self.logger = logger
        self.page_name = page_name
        self.healer = DeterministicHealer(page, logger)

        # Load locators
        with open("locators/locators.json") as f:
            all_locators = json.load(f)

        # Select locators for this page
        self.locators = all_locators[page_name]


    def type(self, locator_name, value):

        locator = self.locators[locator_name]

        try:

            self.logger.info(f"Typing into {locator_name}")

            self.page.locator(locator).fill(value)

        except Exception:

            self.logger.error("Locator failed while typing")

            capture_screenshot(self.page)

            dom = capture_dom(self.page)

            healed = self.healer.heal(locator_name)

            if not healed:
                raise Exception("Healing failed")


    def click(self, locator_name):

        locator = self.locators[locator_name]

        try:

            self.logger.info(f"Clicking {locator_name}")

            self.page.locator(locator).first.click()

        except Exception:

            self.logger.error("Locator failed")

            capture_screenshot(self.page)

            dom = capture_dom(self.page)

            healed = self.healer.heal(locator_name)

            if not healed:
                raise Exception("Healing failed")