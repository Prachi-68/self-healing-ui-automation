class FailureDetector:

    def __init__(self, logger):
        self.logger = logger

    def handle_failure(self, locator):

        self.logger.error(f"Locator failed: {locator}")