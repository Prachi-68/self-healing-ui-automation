import os
from datetime import datetime

def capture_screenshot(page):

    os.makedirs("reports", exist_ok=True)

    filename = f"reports/error_{datetime.now().timestamp()}.png"

    page.screenshot(path=filename)

    return filename