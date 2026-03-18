"""
action_engine.py
================
Wraps every Playwright interaction with automatic self-healing.
When a locator fails the engine hands control to DeterministicHealer
(12 strategies).  If healing also fails it raises, leaving room for
the caller to invoke an AI healer as strategy 13.
"""

import json
from utils.screenshot import capture_screenshot
from healing.dom_capture import capture_dom
from healing.deterministic_healer import DeterministicHealer


class ActionEngine:

    def __init__(self, page, logger, page_name: str):
        self.page      = page
        self.logger    = logger
        self.page_name = page_name

        # Load locators
        with open("locators/locators.json") as f:
            all_locators = json.load(f)

        self.locators = all_locators[page_name]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_locator(self, locator_name: str) -> str:
        locator = self.locators.get(locator_name)
        if not locator:
            raise KeyError(
                f"Locator '{locator_name}' not found in page "
                f"'{self.page_name}'"
            )
        return locator

    def _make_healer(self, action: str, value: str = None) -> DeterministicHealer:
        return DeterministicHealer(
            self.page, self.logger, action=action, value=value
        )

    def _on_failure(self, locator_name: str, action: str,
                    value: str = None) -> bool:
        self.logger.error(
            f"Primary locator failed for '{locator_name}'. "
            "Capturing screenshot + DOM, starting healer..."
        )
        capture_screenshot(self.page)
        capture_dom(self.page)

        healer = self._make_healer(action, value)
        healed = healer.heal(locator_name)

        if not healed:
            raise RuntimeError(
                f"All 12 deterministic strategies failed for "
                f"'{locator_name}'. Consider invoking AI healer."
            )
        return True

    # ------------------------------------------------------------------
    # Public actions
    # ------------------------------------------------------------------

    def click(self, locator_name: str):
        locator = self._get_locator(locator_name)
        try:
            self.logger.info(f"[ACTION] click → {locator_name}")
            self.page.locator(locator).first.click()
        except Exception:
            self._on_failure(locator_name, "click")

    def type(self, locator_name: str, value: str):
        locator = self._get_locator(locator_name)
        try:
            self.logger.info(f"[ACTION] fill '{value}' → {locator_name}")
            self.page.locator(locator).fill(value)
        except Exception:
            self._on_failure(locator_name, "fill", value)

    def check(self, locator_name: str):
        locator = self._get_locator(locator_name)
        try:
            self.logger.info(f"[ACTION] check → {locator_name}")
            self.page.locator(locator).first.check()
        except Exception:
            self._on_failure(locator_name, "check")

    def uncheck(self, locator_name: str):
        locator = self._get_locator(locator_name)
        try:
            self.logger.info(f"[ACTION] uncheck → {locator_name}")
            self.page.locator(locator).first.uncheck()
        except Exception:
            self._on_failure(locator_name, "uncheck")

    def select(self, locator_name: str, value: str):
        locator = self._get_locator(locator_name)
        try:
            self.logger.info(
                f"[ACTION] select '{value}' → {locator_name}"
            )
            self.page.locator(locator).select_option(value)
        except Exception:
            self._on_failure(locator_name, "select", value)

    def hover(self, locator_name: str):
        locator = self._get_locator(locator_name)
        try:
            self.logger.info(f"[ACTION] hover → {locator_name}")
            self.page.locator(locator).first.hover()
        except Exception:
            self._on_failure(locator_name, "hover")

    def focus(self, locator_name: str):
        locator = self._get_locator(locator_name)
        try:
            self.logger.info(f"[ACTION] focus → {locator_name}")
            self.page.locator(locator).first.focus()
        except Exception:
            self._on_failure(locator_name, "focus")

    def set_file(self, locator_name: str, file_path: str):
        """For file-upload inputs."""
        locator = self._get_locator(locator_name)
        try:
            self.logger.info(
                f"[ACTION] set_input_files '{file_path}' → {locator_name}"
            )
            self.page.locator(locator).set_input_files(file_path)
        except Exception:
            self.logger.error(
                f"File upload locator failed for '{locator_name}'."
            )
            capture_screenshot(self.page)
            healer = self._make_healer("click")
            healed = healer.heal(locator_name)
            if not healed:
                raise RuntimeError(
                    f"Healing failed for file input '{locator_name}'"
                )

    def drag_and_drop(self, source_name: str, target_name: str):
        """Drag source element onto target element."""
        src_locator = self._get_locator(source_name)
        tgt_locator = self._get_locator(target_name)
        try:
            self.logger.info(
                f"[ACTION] drag '{source_name}' → '{target_name}'"
            )
            self.page.locator(src_locator).drag_to(
                self.page.locator(tgt_locator)
            )
        except Exception:
            self.logger.error("Drag-and-drop failed — attempting heal on source")
            capture_screenshot(self.page)
            healer = self._make_healer("click")
            healer.heal(source_name)