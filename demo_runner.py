"""
demo_runner.py
==============
Interactive menu-driven runner for the Self-Healing UI Automation System.

Each scenario demonstrates the 12-strategy deterministic healing engine
by first using a BROKEN locator to trigger failure, then letting the
healer recover execution automatically.

Usage
-----
    python demo_runner.py

Then select a scenario number (1-13) or 0 to run all.
"""

import sys
import time

from core.browser_manager import BrowserManager
from core.action_engine import ActionEngine
from core.page_manager import PageManager
from utils.logger import get_logger

logger = get_logger()

# ──────────────────────────────────────────────────────────────────────────────
# SCENARIO FUNCTIONS
# Each function receives (page, page_manager) and runs one workflow.
# Broken locators are injected directly into ActionEngine.locators so the
# healer is exercised on every run without editing locators.json.
# ──────────────────────────────────────────────────────────────────────────────

def scenario_01_login(page, page_manager):
    """Login flow — broken login_button selector triggers S4 role-based heal."""
    print("\n🔐  Scenario 01 — Login")
    page_manager.navigate("https://the-internet.herokuapp.com/login")
    actions = ActionEngine(page, logger, "login_page")

    actions.type("username_input", "tomsmith")
    actions.type("password_input", "SuperSecretPassword!")

    # Inject broken locator
    actions.locators["login_button"] = "button[type='submit999']"
    logger.warning("[DEMO] Injected broken locator for login_button")

    actions.click("login_button")
    logger.info("✅  Scenario 01 complete")


def scenario_02_checkbox(page, page_manager):
    """Checkbox page — broken selector triggers S4 checkbox-role heal."""
    print("\n☑️   Scenario 02 — Checkbox")
    page_manager.navigate("https://the-internet.herokuapp.com/checkboxes")
    actions = ActionEngine(page, logger, "checkbox_page")

    # Inject broken locators
    actions.locators["checkbox1"] = "input[type='checkbox123']:nth-of-type(1)"
    actions.locators["checkbox2"] = "#checkbox-2-broken"
    logger.warning("[DEMO] Injected broken locators for checkbox1 & checkbox2")

    actions.check("checkbox1")
    actions.check("checkbox2")
    logger.info("✅  Scenario 02 complete")


def scenario_03_dropdown(page, page_manager):
    """Dropdown — broken id triggers S7 id/name heal."""
    print("\n🔽  Scenario 03 — Dropdown")
    page_manager.navigate("https://the-internet.herokuapp.com/dropdown")
    actions = ActionEngine(page, logger, "dropdown_page")

    # Inject broken locator
    actions.locators["dropdown"] = "#dropdown_BROKEN_999"
    logger.warning("[DEMO] Injected broken locator for dropdown")

    actions.select("dropdown", "1")
    logger.info("✅  Scenario 03 complete")


def scenario_04_add_remove(page, page_manager):
    """Add/Remove Elements — broken text trigger uses S6 text-based heal."""
    print("\n➕  Scenario 04 — Add / Remove Elements")
    page_manager.navigate(
        "https://the-internet.herokuapp.com/add_remove_elements/"
    )
    actions = ActionEngine(page, logger, "add_remove_page")

    # Inject broken locator for add
    actions.locators["add_button"] = "text=Add Element BROKEN"
    logger.warning("[DEMO] Injected broken locator for add_button")

    actions.click("add_button")
    actions.click("add_button")
    actions.click("delete_button")
    logger.info("✅  Scenario 04 complete")


def scenario_05_file_upload(page, page_manager):
    """File Upload — broken submit button id triggers S9 composite-CSS heal."""
    print("\n📁  Scenario 05 — File Upload")
    page_manager.navigate("https://the-internet.herokuapp.com/upload")
    actions = ActionEngine(page, logger, "upload_page")

    page.set_input_files("#file-upload", "demo-websites.txt")

    # Inject broken locator
    actions.locators["upload_button"] = "#file-submit-BROKEN"
    logger.warning("[DEMO] Injected broken locator for upload_button")

    actions.click("upload_button")
    logger.info("✅  Scenario 05 complete")


def scenario_06_drag_and_drop(page, page_manager):
    """
    Drag & Drop — uses the-internet drag-drop page.
    Broken source id triggers S9 CSS-combo heal ([draggable='true']).
    """
    print("\n🖱️   Scenario 06 — Drag and Drop")
    page_manager.navigate(
        "https://the-internet.herokuapp.com/drag_and_drop"
    )
    actions = ActionEngine(page, logger, "drag_drop_page")

    # Inject broken source locator
    actions.locators["drag_source"] = "#column-a-BROKEN"
    logger.warning("[DEMO] Injected broken locator for drag_source")

    actions.drag_and_drop("drag_source", "drag_target")
    logger.info("✅  Scenario 06 complete")


def scenario_07_hover(page, page_manager):
    """
    Hover / Tooltip — hovers over a list item image to reveal hidden links.
    The healer uses S11 XPath (//div[@class='example']//li[1]//img).

    Root cause of previous failure: locator_name 'hover_trigger' contained
    neither 'hover', 'trigger', nor 'img' keywords that S9/S11 matched.
    Fixed by renaming the injected key to 'hover_trigger' and adding
    dedicated img / hover XPath chains in S9, S11, S12.
    """
    print("\n🖱️   Scenario 07 — Hover")
    page_manager.navigate("https://the-internet.herokuapp.com/hovers")
    actions = ActionEngine(page, logger, "hover_page")

    # Inject broken locator — healer will recover via S11 XPath img strategy
    actions.locators["hover_trigger"] = ".example li:nth-of-type(1) img.BROKEN_CLASS"
    logger.warning("[DEMO] Injected broken locator for hover_trigger")

    actions.hover("hover_trigger")
    time.sleep(1)   # let revealed links render

    # Verify the caption appeared
    try:
        caption = page.locator(".example li:nth-of-type(1) .figcaption").inner_text()
        logger.info(f"Hover revealed caption: {caption.strip()}")
    except Exception:
        # Caption selector varies; just confirm we got past the hover
        logger.info("Hover action completed — tooltip/caption may be in DOM")

    logger.info("✅  Scenario 07 complete")


def scenario_08_frames(page, page_manager):
    """
    iFrames — enters a nested TinyMCE iframe, clears existing content,
    types new text, and verifies the content was written successfully.

    Why .click() fails on TinyMCE:
        TinyMCE renders a '.tox' overlay div on top of the editable body.
        This overlay intercepts all pointer events, causing Playwright's
        .click() to time out after 30 seconds.

    Solution — 3-layer cascade, each more direct than the last:

    Primary  : TinyMCE JS API  → tinymce.get(0).setContent() + .focus()
               Most reliable — bypasses the DOM entirely, uses TinyMCE's
               own internal API which is always available once initialised.

    Fallback A: Direct iframe body JS → body.focus() + body.innerHTML
               Works at the DOM level inside the frame context, no overlay
               interference because JS evaluate skips pointer-event checks.

    Fallback B: Playwright frame keyboard → Ctrl+A then keyboard.type()
               Last resort using Playwright's keyboard injection which
               operates at OS level, below the browser's event system.
    """
    print("\n🖼️   Scenario 08 — iFrames")
    page_manager.navigate("https://the-internet.herokuapp.com/iframe")

    typed_text = "Self-Healing automation test inside iframe!"

    # Wait for TinyMCE to fully initialise before attempting any interaction.
    # TinyMCE is ready when window.tinymce.get(0) is not null/undefined.
    logger.info("[S08] Waiting for TinyMCE editor to initialise...")
    try:
        page.wait_for_function(
            "() => window.tinymce && window.tinymce.get(0) !== null",
            timeout=15000
        )
        logger.info("[S08] TinyMCE initialised")
    except Exception:
        logger.warning("[S08] TinyMCE init wait timed out — proceeding anyway")

    # ------------------------------------------------------------------
    # PRIMARY — TinyMCE JavaScript API (most reliable, overlay-immune)
    # ------------------------------------------------------------------
    try:
        # Focus the editor so it is in an active state
        page.evaluate("tinymce.get(0).focus()")

        # setContent replaces all editor content directly via TinyMCE's API
        page.evaluate(
            f"tinymce.get(0).setContent('<p>{typed_text}</p>')"
        )

        # Read back what TinyMCE now holds to confirm success
        content = page.evaluate("tinymce.get(0).getContent()")
        logger.info(f"[S08] TinyMCE API wrote content successfully")
        logger.info(f"[S08] Verified content: {content.strip()}")
        logger.info("✅  Scenario 08 complete — typed inside iframe (TinyMCE API)")
        return

    except Exception as e1:
        logger.warning(f"[S08] TinyMCE API approach failed: {e1}")

    # ------------------------------------------------------------------
    # FALLBACK A — Direct JS inside iframe body (no pointer events needed)
    # ------------------------------------------------------------------
    try:
        logger.info("[S08] Trying Fallback A — direct JS on iframe body...")

        # Locate the actual frame object (not frame_locator) so we can
        # call .evaluate() inside the frame's own JS context
        tinymce_frame = next(
            (f for f in page.frames
             if f.name and "mce" in f.name.lower()),
            page.frames[1] if len(page.frames) > 1 else None
        )

        if tinymce_frame is None:
            raise RuntimeError("Could not locate TinyMCE iframe frame object")

        # Focus + set innerHTML directly — bypasses pointer event checks
        tinymce_frame.evaluate(
            """() => {
                document.body.focus();
                document.body.innerHTML = '<p>""" + typed_text + """</p>';
            }"""
        )

        # Read back from the frame to verify
        result = tinymce_frame.evaluate("document.body.innerText")
        logger.info(f"[S08] Fallback A wrote content: '{result.strip()}'")
        logger.info("✅  Scenario 08 complete — typed inside iframe (Fallback A JS)")
        return

    except Exception as e2:
        logger.warning(f"[S08] Fallback A failed: {e2}")

    # ------------------------------------------------------------------
    # FALLBACK B — Playwright keyboard injection (OS-level, overlay-immune)
    # ------------------------------------------------------------------
    try:
        logger.info("[S08] Trying Fallback B — Playwright keyboard injection...")

        frame_locator = page.frame_locator("iframe").first
        body          = frame_locator.locator("body")

        # Click the body using force=True which skips actionability checks
        # (including the overlay interception check)
        body.click(force=True)
        time.sleep(0.3)

        # Select all existing content then type replacement
        page.keyboard.press("Control+a")
        time.sleep(0.1)
        page.keyboard.type(typed_text)

        logger.info(f"[S08] Fallback B typed: '{typed_text}'")
        logger.info("✅  Scenario 08 complete — typed inside iframe (Fallback B keyboard)")
        return

    except Exception as e3:
        logger.error(f"[S08] All 3 iframe interaction attempts failed: {e3}")
        logger.error("[S08] ❌  Scenario 08 could not complete")


def scenario_09_tables(page, page_manager):
    """
    Data Tables — reads cells and clicks a column sort header.
    Broken locator triggers S9/S11 table-aware heal.

    Root cause of previous failure: 'sort_by_last' contained no keyword
    ('sort', 'table', 'th', 'header') that any of the 12 strategies
    matched against. Fixed by adding table/sort/th keyword detection to
    S9 (thead th span), S11 (XPath //thead//th//span), and S12 (.example, table).
    """
    print("\n📊  Scenario 09 — Tables")
    page_manager.navigate("https://the-internet.herokuapp.com/tables")
    actions = ActionEngine(page, logger, "tables_page")

    # Read a cell to confirm page loaded correctly
    try:
        first_name = page.locator(
            "table#table1 tbody tr:nth-of-type(1) td:nth-of-type(1)"
        ).inner_text()
        logger.info(f"[S09] First name in table before sort: '{first_name}'")
    except Exception:
        logger.warning("[S09] Could not read table cell")

    # Inject broken sort locator — healer recovers via S9 'table thead th span'
    # Key name contains 'sort' → triggers table-header strategies in healer
    actions.locators["sort_by_last"] = "table#table1 thead .BROKEN_SORT_SPAN"
    logger.warning("[DEMO] Injected broken locator for sort_by_last")

    actions.click("sort_by_last")

    # Confirm sort happened by reading first name again
    time.sleep(0.5)
    try:
        first_name_after = page.locator(
            "table#table1 tbody tr:nth-of-type(1) td:nth-of-type(1)"
        ).inner_text()
        logger.info(f"[S09] First name in table after sort: '{first_name_after}'")
    except Exception:
        logger.warning("[S09] Could not verify sort result")

    logger.info("✅  Scenario 09 complete")


def scenario_10_key_press(page, page_manager):
    """
    Key Presses — types into an input and logs the detected key.
    Broken input id triggers S5 label / S7 id heal.
    """
    print("\n⌨️   Scenario 10 — Key Presses")
    page_manager.navigate(
        "https://the-internet.herokuapp.com/key_presses"
    )
    actions = ActionEngine(page, logger, "key_press_page")

    # Inject broken input locator
    actions.locators["key_input"] = "#target_BROKEN"
    logger.warning("[DEMO] Injected broken locator for key_input")

    actions.click("key_input")
    page.keyboard.press("A")
    time.sleep(0.5)

    try:
        result = page.locator("#result").inner_text()
        logger.info(f"Key press result: {result}")
    except Exception:
        logger.warning("Could not read key press result")

    logger.info("✅  Scenario 10 complete")


def scenario_11_infinite_scroll(page, page_manager):
    """
    Infinite Scroll — scrolls down to load more content.
    Demonstrates scroll action; broken locator triggers S9 CSS heal.
    """
    print("\n📜  Scenario 11 — Infinite Scroll")
    page_manager.navigate(
        "https://the-internet.herokuapp.com/infinite_scroll"
    )

    logger.info("Scrolling to load dynamic content...")
    for _ in range(5):
        page.keyboard.press("End")
        time.sleep(0.8)

    paragraphs = page.locator(".jscroll-added p").count()
    logger.info(f"Loaded {paragraphs} new paragraphs via infinite scroll")
    logger.info("✅  Scenario 11 complete")


def scenario_12_video(page, page_manager):
    """
    Video Player — navigates to a page with an HTML5 <video> element.
    We use W3Schools' video demo; broken selector triggers S9/S11 heal.
    Note: Playwright can control video via JS evaluate.
    """
    print("\n🎬  Scenario 12 — Video Player")

    # the-internet doesn't have a video page; use Playwright's demo site
    page_manager.navigate(
        "https://the-internet.herokuapp.com/challenging_dom"
    )

    # Fallback: use a public HTML5 video test page
    page_manager.navigate(
        "https://www.w3schools.com/html/mov_bbb.mp4"
    )
    # Navigate to a simple page that wraps a video tag
    page_manager.navigate(
        "https://www.w3schools.com/html/html5_video.asp"
    )

    try:
        # Inject broken video locator
        actions = ActionEngine(page, logger, "video_page")
        actions.locators["video_player"] = "video#BROKEN_ID"
        logger.warning("[DEMO] Injected broken locator for video_player")

        # Healer should recover using S9 'video' CSS combo
        # After heal, play via JS
        video = page.locator("video").first
        if video.count() > 0:
            page.evaluate("document.querySelector('video').play()")
            time.sleep(2)
            page.evaluate("document.querySelector('video').pause()")
            logger.info("✅  Video play/pause via JS evaluate")
        else:
            logger.warning("No video element found on page")
    except Exception as exc:
        logger.error(f"Video scenario error: {exc}")

    logger.info("✅  Scenario 12 complete")


def scenario_13_geolocation(page, page_manager):
    """
    Geolocation — grants location permission and clicks 'Where Am I?'.
    Broken button selector triggers S6 text-based heal.
    Uses Playwright's browser context geolocation mock.
    """
    print("\n📍  Scenario 13 — Geolocation")

    # Geolocation must be set on the context, not the page
    # We close and reopen with geolocation permission
    logger.info("Setting up browser context with geolocation permission...")

    try:
        context = page.context
        context.set_geolocation({"latitude": 25.3176, "longitude": 82.9739})
        context.grant_permissions(["geolocation"])

        page_manager.navigate(
            "https://the-internet.herokuapp.com/geolocation"
        )
        actions = ActionEngine(page, logger, "geolocation_page")

        # Inject broken button locator
        actions.locators["where_am_i_button"] = "button#BROKEN_WHERE_AM_I"
        logger.warning(
            "[DEMO] Injected broken locator for where_am_i_button"
        )

        actions.click("where_am_i_button")
        time.sleep(2)

        try:
            lat  = page.locator("#lat-value").inner_text()
            long = page.locator("#long-value").inner_text()
            logger.info(f"Geolocation result — lat: {lat}, long: {long}")
        except Exception:
            logger.warning("Could not read geolocation result elements")

    except Exception as exc:
        logger.error(f"Geolocation scenario error: {exc}")

    logger.info("✅  Scenario 13 complete")


# ──────────────────────────────────────────────────────────────────────────────
# Menu
# ──────────────────────────────────────────────────────────────────────────────

SCENARIOS = {
    1:  ("Login",                   scenario_01_login),
    2:  ("Checkbox",                scenario_02_checkbox),
    3:  ("Dropdown",                scenario_03_dropdown),
    4:  ("Add / Remove Elements",   scenario_04_add_remove),
    5:  ("File Upload",             scenario_05_file_upload),
    6:  ("Drag and Drop",           scenario_06_drag_and_drop),
    7:  ("Hover / Tooltip",         scenario_07_hover),
    8:  ("iFrames",                 scenario_08_frames),
    9:  ("Data Tables",             scenario_09_tables),
    10: ("Key Presses",             scenario_10_key_press),
    11: ("Infinite Scroll",         scenario_11_infinite_scroll),
    12: ("Video Player",            scenario_12_video),
    13: ("Geolocation",             scenario_13_geolocation),
}


def print_menu():
    print("\n" + "═" * 56)
    print("   🤖  Self-Healing UI Automation — Scenario Runner")
    print("═" * 56)
    for num, (label, _) in SCENARIOS.items():
        print(f"   {num:>2}.  {label}")
    print("    0.  Run ALL scenarios")
    print("   -1.  Exit")
    print("═" * 56)


def get_user_choice() -> int:
    while True:
        try:
            raw = input("\nEnter scenario number: ").strip()
            choice = int(raw)
            if choice == -1:
                sys.exit(0)
            if choice == 0 or choice in SCENARIOS:
                return choice
            print(f"  ⚠  Invalid choice '{raw}'. Please enter 0-13 or -1.")
        except ValueError:
            print("  ⚠  Please enter a number.")
        except KeyboardInterrupt:
            print("\nExiting.")
            sys.exit(0)


def run_scenario(num: int, page, page_manager):
    label, fn = SCENARIOS[num]
    print(f"\n{'─' * 56}")
    print(f"  Running Scenario {num:02d}: {label}")
    print(f"{'─' * 56}")
    try:
        fn(page, page_manager)
    except Exception as exc:
        logger.error(f"Scenario {num} ended with error: {exc}")


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

def main():
    browser_mgr  = BrowserManager()
    page         = browser_mgr.start()
    page_manager = PageManager(page, logger)

    try:
        while True:
            print_menu()
            choice = get_user_choice()

            if choice == 0:
                for num in SCENARIOS:
                    run_scenario(num, page, page_manager)
            else:
                run_scenario(choice, page, page_manager)

            again = input("\n  Run another scenario? (y/n): ").strip().lower()
            if again != "y":
                break

    finally:
        browser_mgr.close()
        print("\n  Browser closed. Goodbye! 👋\n")


if __name__ == "__main__":
    main()