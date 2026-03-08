class DeterministicHealer:

    def __init__(self, page, logger):
        self.page = page
        self.logger = logger


    def extract_text(self, locator_name):

        text = locator_name.replace("_", " ")
        text = text.replace("button", "").strip()

        return text.title()


    def try_role_based(self, text):

        try:

            element = self.page.get_by_role("button", name=text)

            if element.count() > 0:

                self.logger.info("Recovered using role-based locator")

                element.first.click()

                return True

        except:
            pass

        return False


    def try_text_based(self, text):

        try:

            element = self.page.locator(f"text={text}")

            if element.count() > 0:

                self.logger.info("Recovered using text locator")

                element.first.click()

                return True

        except:
            pass

        return False


    def try_button_type(self):

        try:

            element = self.page.locator("button[type='submit']")

            if element.count() > 0:

                self.logger.info("Recovered using button type locator")

                element.first.click()

                return True

        except:
            pass

        return False


    def try_aria(self, text):

        try:

            element = self.page.locator(f"[aria-label='{text}']")

            if element.count() > 0:

                self.logger.info("Recovered using aria locator")

                element.first.click()

                return True

        except:
            pass

        return False
    
    def try_checkbox(self):

        try:

            element = self.page.get_by_role("checkbox")

            if element.count() > 0:

                self.logger.info("Recovered using checkbox role locator")

                element.first.check()

                return True

        except:
            pass

        return False

    def try_dropdown(self):

        try:

            element = self.page.get_by_role("combobox")

            if element.count() > 0:

                self.logger.info("Recovered using dropdown role locator")

                element.first.select_option(index=1)

                return True

        except:
            pass

        return False

    def heal(self, locator_name):

        self.logger.info("Running deterministic healing strategies")

        text = self.extract_text(locator_name)

        strategies = [
            lambda: self.try_role_based(text),
            lambda: self.try_text_based(text),
            self.try_button_type,
            lambda: self.try_aria(text),
            self.try_checkbox,
            self.try_dropdown
        ]

        for strategy in strategies:

            healed = strategy()

            if healed:
                return True

        return False