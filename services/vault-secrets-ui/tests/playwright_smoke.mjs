import assert from "node:assert/strict";
import { chromium } from "playwright";

const baseUrl = process.argv[2] || "http://127.0.0.1:10000";

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();

try {
  await page.goto(baseUrl, { waitUntil: "networkidle" });
  await page.waitForSelector("#target-service");

  assert.equal(await page.title(), "VAULT_OS // KEY CONSOLE");
  assert.equal(await page.locator("#target-service").isVisible(), true);

  await page.selectOption("#target-service", "common-mcp");
  await page.waitForFunction(() => {
    const labels = [...document.querySelectorAll("#service-fields label")].map((node) => node.textContent || "");
    return labels.some((label) => label.includes("Notion API Key"));
  });

  const notionField = page.locator('input[data-field-name="NOTION_API_KEY"]');
  await notionField.waitFor();
  assert.equal(await notionField.isVisible(), true);

  await page.click('button[onclick="toggleLang()"]');
  await page.waitForFunction(() => {
    const targetLabels = [...document.querySelectorAll("[data-translate='target']")].map((node) => node.textContent || "");
    return targetLabels.some((label) => label.includes("Cilova Sluzba"));
  });

  await page.click('button[onclick="toggleAdvanced()"]');
  await page.waitForSelector("#advanced-panel:not(.hidden)");
  assert.equal(await page.locator("#secret-editor").isVisible(), true);

  await page.click('button[onclick="toggleTheme()"]');
  const themeLabel = await page.locator("#theme-label").textContent();
  assert.ok(themeLabel && themeLabel.length > 0);
} finally {
  await browser.close();
}
