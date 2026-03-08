from core.browser_manager import BrowserManager
from core.page_manager import PageManager
from core.action_engine import ActionEngine
from utils.logger import get_logger

logger = get_logger()

browser = BrowserManager()

page = browser.start()

page_manager = PageManager(page)

actions = ActionEngine(page, logger)

page_manager.open_home()

actions.type("username_input", "tomsmith")

actions.type("password_input", "SuperSecretPassword!")

actions.click("login_button")

browser.close()