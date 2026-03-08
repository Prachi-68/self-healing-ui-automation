# from core.browser_manager import BrowserManager
# from core.action_engine import ActionEngine
# from core.page_manager import PageManager
# from utils.logger import get_logger

# logger = get_logger()

# browser = BrowserManager()
# page = browser.start()

# page_manager = PageManager(page, logger)

# # LOGIN
# page_manager.navigate("https://the-internet.herokuapp.com/login")

# actions = ActionEngine(page, logger, "login_page")

# actions.type("username_input", "tomsmith")
# actions.type("password_input", "SuperSecretPassword!")
# actions.click("login_button")


# # CHECKBOX
# page_manager.navigate("https://the-internet.herokuapp.com/checkboxes")

# actions = ActionEngine(page, logger, "checkbox_page")

# actions.click("checkbox1")
# actions.click("checkbox2")


# # DROPDOWN
# page_manager.navigate("https://the-internet.herokuapp.com/dropdown")

# page.select_option("#dropdown", "1")


# browser.close()

from core.browser_manager import BrowserManager
from core.action_engine import ActionEngine
from core.page_manager import PageManager
from utils.logger import get_logger

logger = get_logger()

browser = BrowserManager()
page = browser.start()

page_manager = PageManager(page, logger)

# LOGIN
page_manager.navigate("https://the-internet.herokuapp.com/login")

actions = ActionEngine(page, logger, "login_page")

actions.type("username_input", "tomsmith")
actions.type("password_input", "SuperSecretPassword!")
actions.click("login_button")


# CHECKBOX
page_manager.navigate("https://the-internet.herokuapp.com/checkboxes")

actions = ActionEngine(page, logger, "checkbox_page")

actions.click("checkbox1")
actions.click("checkbox2")


# DROPDOWN
page_manager.navigate("https://the-internet.herokuapp.com/dropdown")

page.select_option("#dropdown", "1")


# ADD / REMOVE ELEMENTS
page_manager.navigate("https://the-internet.herokuapp.com/add_remove_elements/")

actions = ActionEngine(page, logger, "add_remove_page")

actions.click("add_button")
actions.click("add_button")
actions.click("delete_button")


# FILE UPLOAD
page_manager.navigate("https://the-internet.herokuapp.com/upload")

actions = ActionEngine(page, logger, "upload_page")

page.set_input_files("#file-upload", "demo-websites.txt")

actions.click("upload_button")


browser.close()