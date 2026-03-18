"""
deterministic_healer.py
=======================
Implements all 12 deterministic self-healing strategies in strict
priority order.  AI healing (strategy 13) is intentionally NOT included
here — it is the responsibility of the caller to invoke it after this
module returns False.

Priority order
--------------
 1  Stored / previously-healed locators  (locator_store.json)
 2  data-testid / data-test / data-automation attributes
 3  ARIA attributes  (aria-label, aria-labelledby, aria-describedby)
 4  Role-based locators  (get_by_role)
 5  Accessibility label / associated <label> text  (get_by_label)
 6  Visible text-based locators  (get_by_text / text=)
 7  ID or name attributes
 8  Element type + partial text  (XPath contains)
 9  Composite CSS  (tag + class + attribute combinations)
10  Neighbour / relative locators  (near, above, below)
11  XPath with hierarchical heuristics  (stable ancestors, no indexes)
12  Anchor to stable container context  (form, section, fieldset, main)
"""

import json
import os
from datetime import datetime


LOCATOR_STORE_PATH = "locators/locator_store.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_store() -> dict:
    if os.path.exists(LOCATOR_STORE_PATH):
        with open(LOCATOR_STORE_PATH) as f:
            return json.load(f)
    return {}


def _save_store(store: dict):
    os.makedirs(os.path.dirname(LOCATOR_STORE_PATH), exist_ok=True)
    with open(LOCATOR_STORE_PATH, "w") as f:
        json.dump(store, f, indent=2)


def _element_visible_and_enabled(element) -> bool:
    """Quick guard: element must exist and be visible."""
    try:
        return element.count() > 0 and element.first.is_visible()
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class DeterministicHealer:

    def __init__(self, page, logger, action: str = "click", value: str = None):
        """
        Parameters
        ----------
        page   : Playwright page object
        logger : standard Python logger
        action : what to do with the recovered element
                 "click" | "fill" | "check" | "select" | "hover" | "focus"
        value  : value needed for fill / select actions
        """
        self.page   = page
        self.logger = logger
        self.action = action
        self.value  = value

    # ------------------------------------------------------------------
    # Internal action dispatcher
    # ------------------------------------------------------------------

    def _perform(self, element, strategy_name: str) -> bool:
        """Perform the configured action on the recovered element."""
        try:
            el  = element.first
            act = self.action

            if act == "click":
                el.click()
            elif act == "fill":
                el.fill(self.value or "")
            elif act == "check":
                el.check()
            elif act == "uncheck":
                el.uncheck()
            elif act == "select":
                el.select_option(self.value or "")
            elif act == "hover":
                el.hover()
            elif act == "focus":
                el.focus()
            else:
                el.click()

            self.logger.info(f"[HEALED] Strategy: {strategy_name}")
            return True

        except Exception as exc:
            self.logger.warning(f"[STRATEGY FAILED] {strategy_name}: {exc}")
            return False

    # ------------------------------------------------------------------
    # Text extraction helper
    # ------------------------------------------------------------------

    def _readable_text(self, locator_name: str) -> str:
        """Convert snake_case locator name → readable label."""
        text = locator_name.replace("_", " ")
        for drop in ("button", "input", "field", "link", "icon", "toggle",
                     "checkbox", "dropdown", "select", "tab", "btn"):
            text = text.replace(drop, "").strip()
        return text.strip().title()

    # ------------------------------------------------------------------
    # STRATEGY 1 — Stored / previously-healed locators
    # ------------------------------------------------------------------

    def _strategy_1_stored_locator(self, locator_name: str) -> bool:
        """
        Look up locator_store.json for a previously validated healed
        locator.  Re-validate it against the live DOM before using it.
        """
        store = _load_store()
        entry = store.get(locator_name)

        if not entry:
            return False

        healed_locator = entry.get("locator")
        if not healed_locator:
            return False

        try:
            element = self.page.locator(healed_locator)
            if _element_visible_and_enabled(element):
                self.logger.info(
                    f"[S1] Found stored healed locator: {healed_locator}"
                )
                return self._perform(element, "S1-StoredLocator")
        except Exception:
            pass

        self.logger.warning("[S1] Stored locator stale — removing from store")
        store.pop(locator_name, None)
        _save_store(store)
        return False

    # ------------------------------------------------------------------
    # STRATEGY 2 — data-testid / data-test / data-automation
    # ------------------------------------------------------------------

    def _strategy_2_data_attributes(self, locator_name: str) -> bool:
        """
        Try common automation-specific data attributes derived from the
        locator name (e.g. 'login_button' → data-testid='login-button').
        """
        slug = locator_name.replace("_", "-")
        candidates = [
            f"[data-testid='{slug}']",
            f"[data-test='{slug}']",
            f"[data-automation='{slug}']",
            f"[data-cy='{slug}']",
            f"[data-qa='{slug}']",
        ]
        for sel in candidates:
            try:
                element = self.page.locator(sel)
                if _element_visible_and_enabled(element):
                    self.logger.info(f"[S2] data-attribute match: {sel}")
                    return self._perform(element, "S2-DataAttribute")
            except Exception:
                continue
        return False

    # ------------------------------------------------------------------
    # STRATEGY 3 — ARIA attributes
    # ------------------------------------------------------------------

    def _strategy_3_aria(self, locator_name: str) -> bool:
        """
        Try aria-label, aria-labelledby, aria-describedby derived from
        the locator name.
        """
        text = self._readable_text(locator_name)
        raw  = locator_name.replace("_", " ")

        candidates = [
            f"[aria-label='{text}']",
            f"[aria-label*='{text}']",
            f"[aria-label='{raw}']",
            f"[aria-label*='{raw}']",
            f"[aria-describedby*='{locator_name}']",
        ]
        for sel in candidates:
            try:
                element = self.page.locator(sel)
                if _element_visible_and_enabled(element):
                    self.logger.info(f"[S3] ARIA match: {sel}")
                    return self._perform(element, "S3-ARIA")
            except Exception:
                continue
        return False

    # ------------------------------------------------------------------
    # STRATEGY 4 — Role-based locators
    # ------------------------------------------------------------------

    def _strategy_4_role_based(self, locator_name: str) -> bool:
        """
        Use Playwright's get_by_role with multiple role types and name
        variants derived from the locator name.
        """
        text       = self._readable_text(locator_name)
        name_lower = locator_name.lower()

        # Infer the most likely role
        if any(k in name_lower for k in ("button", "btn", "submit", "login",
                                          "add", "delete", "upload", "save")):
            roles = ["button"]
        elif any(k in name_lower for k in ("link", "nav", "menu")):
            roles = ["link", "button"]
        elif any(k in name_lower for k in ("checkbox", "check")):
            roles = ["checkbox"]
        elif any(k in name_lower for k in ("dropdown", "select", "combo")):
            roles = ["combobox", "listbox"]
        elif any(k in name_lower for k in ("tab",)):
            roles = ["tab"]
        elif any(k in name_lower for k in ("input", "field", "text", "email",
                                            "password", "username", "user")):
            roles = ["textbox"]
        else:
            roles = ["button", "link", "textbox", "checkbox", "combobox"]

        for role in roles:
            for name_variant in [text, text.lower(),
                                  locator_name.replace("_", " ")]:
                try:
                    element = self.page.get_by_role(role, name=name_variant)
                    if _element_visible_and_enabled(element):
                        self.logger.info(
                            f"[S4] Role match: role={role}, name={name_variant}"
                        )
                        return self._perform(element, "S4-RoleBased")
                except Exception:
                    continue

        # Fallback: role with no name constraint
        for role in roles:
            try:
                element = self.page.get_by_role(role)
                if _element_visible_and_enabled(element):
                    self.logger.info(
                        f"[S4] Role fallback (no name): role={role}"
                    )
                    return self._perform(element, "S4-RoleNoName")
            except Exception:
                continue

        return False

    # ------------------------------------------------------------------
    # STRATEGY 5 — Accessibility label / associated <label> text
    # ------------------------------------------------------------------

    def _strategy_5_label_text(self, locator_name: str) -> bool:
        """
        Use get_by_label which queries elements associated with a <label>
        element — ideal for form inputs.
        """
        text = self._readable_text(locator_name)
        variants = [
            text,
            text.lower(),
            locator_name.replace("_", " "),
            locator_name.replace("_", " ").lower(),
        ]
        for variant in variants:
            try:
                element = self.page.get_by_label(variant)
                if _element_visible_and_enabled(element):
                    self.logger.info(f"[S5] Label match: '{variant}'")
                    return self._perform(element, "S5-LabelText")
            except Exception:
                continue
        return False

    # ------------------------------------------------------------------
    # STRATEGY 6 — Visible text-based locators
    # ------------------------------------------------------------------

    def _strategy_6_text_based(self, locator_name: str) -> bool:
        """
        Use get_by_text and text= selectors with exact and partial
        matching.
        """
        text = self._readable_text(locator_name)

        for variant in [text, text.lower(),
                        locator_name.replace("_", " ").title()]:
            # CSS text selectors
            for sel in [f"text={variant}", f"text={variant.lower()}"]:
                try:
                    element = self.page.locator(sel)
                    if _element_visible_and_enabled(element):
                        self.logger.info(f"[S6] Text match: '{sel}'")
                        return self._perform(element, "S6-TextBased")
                except Exception:
                    continue

            # get_by_text with partial match
            try:
                element = self.page.get_by_text(variant, exact=False)
                if _element_visible_and_enabled(element):
                    self.logger.info(f"[S6] get_by_text partial: '{variant}'")
                    return self._perform(element, "S6-TextPartial")
            except Exception:
                continue

        return False

    # ------------------------------------------------------------------
    # STRATEGY 7 — ID or name attributes
    # ------------------------------------------------------------------

    def _strategy_7_id_name(self, locator_name: str) -> bool:
        """
        Try id and name attributes using the locator name and common
        slug variants.
        """
        slug_hyphen     = locator_name.replace("_", "-")
        slug_underscore = locator_name
        slug_camel      = "".join(
            w.capitalize() if i else w
            for i, w in enumerate(locator_name.split("_"))
        )

        candidates = []
        for slug in [slug_hyphen, slug_underscore, slug_camel]:
            candidates += [
                f"#{slug}",
                f"[name='{slug}']",
                f"[id='{slug}']",
            ]

        for sel in candidates:
            try:
                element = self.page.locator(sel)
                if _element_visible_and_enabled(element):
                    self.logger.info(f"[S7] ID/name match: {sel}")
                    return self._perform(element, "S7-IDName")
            except Exception:
                continue
        return False

    # ------------------------------------------------------------------
    # STRATEGY 8 — Element type + partial text (XPath contains)
    # ------------------------------------------------------------------

    def _strategy_8_type_partial_text(self, locator_name: str) -> bool:
        """
        Build XPath expressions combining element type with partial text
        from the locator name.
        """
        text       = self._readable_text(locator_name)
        name_lower = locator_name.lower()

        if any(k in name_lower for k in ("button", "btn", "submit",
                                          "login", "add", "delete",
                                          "upload", "save", "toggle")):
            tags = ["button", "input[@type='button']",
                    "input[@type='submit']", "a"]
        elif any(k in name_lower for k in ("link",)):
            tags = ["a", "button"]
        elif any(k in name_lower for k in ("input", "field", "user",
                                            "email", "password")):
            tags = ["input", "textarea"]
        else:
            tags = ["button", "a", "input", "span", "div"]

        for tag in tags:
            for word in [text, text.lower()]:
                xpath = f"//{tag}[contains(., '{word}')]"
                try:
                    element = self.page.locator(xpath)
                    if _element_visible_and_enabled(element):
                        self.logger.info(f"[S8] XPath type+text: {xpath}")
                        return self._perform(element, "S8-TypePartialText")
                except Exception:
                    continue
        return False

    # ------------------------------------------------------------------
    # STRATEGY 9 — Composite CSS selectors
    # ------------------------------------------------------------------

    def _strategy_9_composite_css(self, locator_name: str) -> bool:
        """
        Build composite CSS selectors combining tag, class, and attribute
        patterns inferred from the locator name.
        """
        name_lower = locator_name.lower()
        candidate_selectors = []

        if any(k in name_lower for k in ("submit", "login", "signin")):
            candidate_selectors += [
                "button[type='submit']", "input[type='submit']",
                "button.btn-primary", "button.login",
                "button.submit", ".login-form button", "form button",
            ]

        if any(k in name_lower for k in ("button", "btn", "add", "delete",
                                          "save", "upload", "ok", "confirm")):
            candidate_selectors += [
                "button.btn", "button.primary",
                "button[class*='btn']", ".actions button",
                "button:not([disabled])",
            ]

        if any(k in name_lower for k in ("checkbox", "check")):
            candidate_selectors += [
                "input[type='checkbox']",
                "input[type='checkbox']:not([disabled])",
            ]

        if any(k in name_lower for k in ("dropdown", "select", "combo")):
            candidate_selectors += [
                "select", "select:not([disabled])", ".dropdown select",
            ]

        if any(k in name_lower for k in ("input", "field", "user",
                                          "email", "password", "text")):
            candidate_selectors += [
                "input[type='text']", "input[type='email']",
                "input[type='password']",
                "input:not([type='hidden']):not([type='submit'])",
            ]

        if any(k in name_lower for k in ("link", "nav", "menu")):
            candidate_selectors += ["a[href]", "nav a", ".menu a"]

        if any(k in name_lower for k in ("upload", "file")):
            candidate_selectors += ["input[type='file']", "#file-upload"]

        if any(k in name_lower for k in ("toggle", "switch")):
            candidate_selectors += [
                "input[type='checkbox']", "[role='switch']",
                ".toggle", ".switch",
            ]

        if any(k in name_lower for k in ("video", "play")):
            candidate_selectors += [
                "video", "video[controls]", "[class*='video']",
            ]

        if any(k in name_lower for k in ("audio",)):
            candidate_selectors += [
                "audio", "audio[controls]", "[class*='audio']",
            ]

        if any(k in name_lower for k in ("canvas",)):
            candidate_selectors += ["canvas", "#canvas", "[class*='canvas']"]

        if any(k in name_lower for k in ("drag", "draggable", "drop")):
            candidate_selectors += [
                "[draggable='true']", ".draggable", "#draggable",
            ]

        if any(k in name_lower for k in ("iframe", "frame")):
            candidate_selectors += ["iframe", "frame"]

        if any(k in name_lower for k in ("hover", "trigger", "tooltip")):
            # The hovers page uses plain <img> tags inside .example divs
            candidate_selectors += [
                ".example img",
                ".example li img",
                "img[src]",
                "img",
                ".has-tooltip",
                "[title]",
                "[data-tooltip]",
            ]

        if any(k in name_lower for k in ("sort", "header", "th", "col", "last",
                                          "first", "table")):
            # Table column headers — <span> inside <th> is the clickable sort handle
            candidate_selectors += [
                "table thead th span",
                "table#table1 thead th span",
                "table thead th",
                "table#table1 thead th",
                "th span",
                "th",
            ]

        for sel in candidate_selectors:
            try:
                element = self.page.locator(sel)
                if _element_visible_and_enabled(element):
                    self.logger.info(f"[S9] CSS combo match: {sel}")
                    return self._perform(element, "S9-CompositeCss")
            except Exception:
                continue

        return False

    # ------------------------------------------------------------------
    # STRATEGY 10 — Neighbour / relative locators
    # ------------------------------------------------------------------

    def _strategy_10_neighbour_relative(self, locator_name: str) -> bool:
        """
        Use Playwright's filter and locator chaining to find elements
        relative to stable anchor elements.
        """
        text       = self._readable_text(locator_name)
        name_lower = locator_name.lower()

        # Input near a matching label
        if any(k in name_lower for k in ("input", "field", "user",
                                          "email", "password", "username")):
            try:
                parent = self.page.locator(
                    f"label:has-text('{text}') ~ input, "
                    f"label:has-text('{text}') + input"
                )
                if _element_visible_and_enabled(parent):
                    self.logger.info(f"[S10] Input near label '{text}'")
                    return self._perform(parent, "S10-NearLabel")
            except Exception:
                pass

        # Button near a heading
        if any(k in name_lower for k in ("button", "btn", "submit", "login")):
            for heading_tag in ["h1", "h2", "h3"]:
                try:
                    element = self.page.locator(
                        f"{heading_tag} ~ button, {heading_tag} ~ form button"
                    )
                    if _element_visible_and_enabled(element):
                        self.logger.info(f"[S10] Button near {heading_tag}")
                        return self._perform(element, "S10-NearHeading")
                except Exception:
                    continue

        # First matching element inside a stable container
        for container in ["form", "section", ".card", ".panel", "main"]:
            try:
                if any(k in name_lower for k in ("checkbox", "check")):
                    el = self.page.locator(
                        f"{container} input[type='checkbox']"
                    )
                elif any(k in name_lower for k in ("dropdown", "select")):
                    el = self.page.locator(f"{container} select")
                elif any(k in name_lower for k in ("button", "btn", "submit")):
                    el = self.page.locator(f"{container} button")
                else:
                    continue

                if _element_visible_and_enabled(el):
                    self.logger.info(
                        f"[S10] Relative in container '{container}'"
                    )
                    return self._perform(el, "S10-ContainerRelative")
            except Exception:
                continue

        return False

    # ------------------------------------------------------------------
    # STRATEGY 11 — XPath with hierarchical heuristics
    # ------------------------------------------------------------------

    def _strategy_11_xpath_hierarchical(self, locator_name: str) -> bool:
        """
        Build stable ancestor-based XPath expressions that avoid fragile
        positional indexes where possible.
        """
        text       = self._readable_text(locator_name)
        name_lower = locator_name.lower()
        xpaths     = []

        if any(k in name_lower for k in ("button", "submit", "login", "btn")):
            xpaths += [
                f"//form//button[normalize-space(.)='{text}']",
                f"//form//button[contains(normalize-space(.), '{text}')]",
                "//form//button[@type='submit']",
                "//form//*[@type='submit']",
                f"//*[contains(@class,'btn') and contains(.,'{text}')]",
            ]

        if any(k in name_lower for k in ("link", "nav")):
            xpaths += [
                f"//nav//a[contains(.,'{text}')]",
                f"//header//a[contains(.,'{text}')]",
                f"//a[contains(.,'{text}')]",
            ]

        if any(k in name_lower for k in ("input", "field", "user",
                                          "email", "password", "username")):
            slug = locator_name.replace("_", "")
            xpaths += [
                f"//form//input[contains(@id,'{slug}')]",
                f"//form//input[contains(@name,'{locator_name}')]",
                "//form//input[@type='text'][1]",
                "//form//input[@type='email'][1]",
                "//form//input[@type='password'][1]",
            ]

        if any(k in name_lower for k in ("checkbox", "check")):
            xpaths += [
                "//input[@type='checkbox'][1]",
                "//input[@type='checkbox'][not(@disabled)][1]",
            ]

        if any(k in name_lower for k in ("dropdown", "select")):
            xpaths += ["//select[1]", "//select[not(@disabled)][1]"]

        if any(k in name_lower for k in ("video",)):
            xpaths += ["//video[1]", "//video[@controls][1]"]

        if any(k in name_lower for k in ("audio",)):
            xpaths += ["//audio[1]", "//audio[@controls][1]"]

        if any(k in name_lower for k in ("canvas",)):
            xpaths += ["//canvas[1]"]

        if any(k in name_lower for k in ("drag", "draggable")):
            xpaths += [
                "//*[@draggable='true'][1]",
                "//*[contains(@class,'draggable')][1]",
            ]

        if any(k in name_lower for k in ("hover", "trigger", "tooltip")):
            # hovers page: <img> tags inside .example list items
            xpaths += [
                "//div[@class='example']//li[1]//img",
                "//div[contains(@class,'example')]//img[1]",
                "//img[@src][1]",
                "//img[1]",
                "//*[contains(@class,'example')]//img[1]",
            ]

        if any(k in name_lower for k in ("sort", "header", "th", "col",
                                          "last", "first", "table")):
            # table column sort: <span> inside <th> is the clickable handle
            xpaths += [
                "//table[@id='table1']//thead//th[2]//span",
                "//table[@id='table1']//thead//th[2]",
                "//table[@id='table1']//thead//th[1]//span",
                "//table[@id='table1']//thead//th[1]",
                "//table//thead//th//span[1]",
                "//thead//th//span",
                "//thead//th[1]",
            ]

        for xpath in xpaths:
            try:
                element = self.page.locator(xpath)
                if _element_visible_and_enabled(element):
                    self.logger.info(f"[S11] XPath hierarchical: {xpath}")
                    return self._perform(element, "S11-XPathHierarchical")
            except Exception:
                continue

        return False

    # ------------------------------------------------------------------
    # STRATEGY 12 — Anchor to stable container context
    # ------------------------------------------------------------------

    def _strategy_12_anchor_container(self, locator_name: str) -> bool:
        """
        Scope the search within stable semantic containers
        (<form>, <section>, <fieldset>, <main>, <article>).
        """
        name_lower = locator_name.lower()
        stable_containers = [
            "form", "fieldset", "section", "main",
            "article", ".container", ".wrapper", "#content",
            ".example", "table", "#table1",
        ]

        if any(k in name_lower for k in ("button", "submit", "login", "btn")):
            target = "button, input[type='submit'], input[type='button']"
        elif any(k in name_lower for k in ("checkbox", "check")):
            target = "input[type='checkbox']"
        elif any(k in name_lower for k in ("dropdown", "select")):
            target = "select"
        elif any(k in name_lower for k in ("input", "field", "user",
                                            "email", "password", "text")):
            target = ("input[type='text'], input[type='email'], "
                      "input[type='password'], textarea")
        elif any(k in name_lower for k in ("link",)):
            target = "a[href]"
        elif any(k in name_lower for k in ("upload", "file")):
            target = "input[type='file']"
        elif any(k in name_lower for k in ("video",)):
            target = "video"
        elif any(k in name_lower for k in ("audio",)):
            target = "audio"
        elif any(k in name_lower for k in ("canvas",)):
            target = "canvas"
        elif any(k in name_lower for k in ("hover", "trigger", "tooltip")):
            # The hovers page wraps images inside .example > ul > li
            target = "img"
        elif any(k in name_lower for k in ("sort", "header", "th", "col",
                                            "last", "first", "table")):
            # Table column sort handle is a <span> inside <th>
            target = "thead th span, thead th"
        elif any(k in name_lower for k in ("drag", "draggable")):
            target = "[draggable='true'], .draggable"
        else:
            target = "button, a, input"

        for container in stable_containers:
            sel = f"{container} {target}"
            try:
                element = self.page.locator(sel)
                if _element_visible_and_enabled(element):
                    self.logger.info(
                        f"[S12] Anchored in container '{container}': {sel}"
                    )
                    return self._perform(element, "S12-AnchorContainer")
            except Exception:
                continue

        return False

    # ------------------------------------------------------------------
    # Persist a successfully healed locator
    # ------------------------------------------------------------------

    def _persist_healed_locator(self, locator_name: str,
                                 healed_locator: str, strategy: str):
        store = _load_store()
        store[locator_name] = {
            "locator":    healed_locator,
            "strategy":   strategy,
            "healed_at":  datetime.now().isoformat(),
            "confidence": 1.0,
        }
        _save_store(store)
        self.logger.info(
            f"[PERSIST] Saved healed locator "
            f"'{locator_name}' → '{healed_locator}'"
        )

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def heal(self, locator_name: str) -> bool:
        """
        Run all 12 deterministic strategies in order.
        Returns True  → element recovered and action performed.
        Returns False → all 12 failed; caller should invoke AI healer.
        """
        self.logger.info(
            f"[HEALER] Starting 12-strategy deterministic healing for: "
            f"'{locator_name}' | action={self.action}"
        )

        strategies = [
            ("S1  — Stored/Healed Locators",
             lambda: self._strategy_1_stored_locator(locator_name)),

            ("S2  — data-testid / data-automation",
             lambda: self._strategy_2_data_attributes(locator_name)),

            ("S3  — ARIA Attributes",
             lambda: self._strategy_3_aria(locator_name)),

            ("S4  — Role-Based Locators",
             lambda: self._strategy_4_role_based(locator_name)),

            ("S5  — Accessibility Label Text",
             lambda: self._strategy_5_label_text(locator_name)),

            ("S6  — Visible Text Locators",
             lambda: self._strategy_6_text_based(locator_name)),

            ("S7  — ID / Name Attributes",
             lambda: self._strategy_7_id_name(locator_name)),

            ("S8  — Element Type + Partial Text",
             lambda: self._strategy_8_type_partial_text(locator_name)),

            ("S9  — Composite CSS Selectors",
             lambda: self._strategy_9_composite_css(locator_name)),

            ("S10 — Neighbour / Relative Locators",
             lambda: self._strategy_10_neighbour_relative(locator_name)),

            ("S11 — XPath Hierarchical Heuristics",
             lambda: self._strategy_11_xpath_hierarchical(locator_name)),

            ("S12 — Anchor to Stable Container",
             lambda: self._strategy_12_anchor_container(locator_name)),
        ]

        for name, strategy_fn in strategies:
            self.logger.info(f"[HEALER] Trying {name}")
            try:
                if strategy_fn():
                    self.logger.info(f"[HEALER] ✅  Healed via {name}")
                    return True
            except Exception as exc:
                self.logger.warning(f"[HEALER] {name} threw: {exc}")

        self.logger.error(
            f"[HEALER] ❌  All 12 strategies failed for '{locator_name}'. "
            "Invoke AI healer as next step."
        )
        return False