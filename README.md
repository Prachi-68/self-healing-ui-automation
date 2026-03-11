# AI Self-Healing UI Automation

AI Self-Healing UI Automation is a Playwright-based automation framework that can automatically recover from UI locator failures using deterministic strategies and AI-assisted healing.

## 🚀 Features

- Automated UI workflows (login, navigation, toggle actions)
- Multi-layer locator fallback strategy
- DOM capture on locator failure
- AI-powered locator healing
- Safe retry and validation of healed locators
- Persistent storage of validated locators
- Structured logging and debugging support

## 🛠 Tech Stack

- **Python**
- **Playwright**
- **OpenAI API**
- **JSON-based Locator Repository**

## ⚙️ How It Works

1. Execute UI workflow using predefined locators.
2. If a locator fails, deterministic fallback strategies are applied.
3. If all deterministic strategies fail:
   - Capture the current DOM
   - Send context to the AI model
4. AI suggests a new locator.
5. The system validates the locator and retries the action.
6. If successful, the locator is stored for future runs.

The system prioritizes deterministic strategies and invokes AI **only as a last resort** to ensure stability and reduce unnecessary AI calls.

## 📌 Example Workflow

The automation system can perform tasks such as:

- Open a website
- Log in with credentials
- Navigate to **Settings**
- Click **Notifications**
- Toggle a configuration setting

## 🎯 Project Goal

The goal of this project is to build a **resilient UI automation framework** that can automatically adapt to UI changes, reducing maintenance effort and improving automation reliability.
