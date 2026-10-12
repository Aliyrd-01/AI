/**
 * Делает скриншоты страниц хаба в заданной локали (для демо-видео с озвучкой).
 *
 *   node tools/capture_shots.mjs ru
 *   node tools/capture_shots.mjs en
 *
 * Результат: shots/<lang>_<name>.png (кадры 1600x900)
 */
import { chromium } from "playwright";
import { mkdirSync } from "node:fs";

const BASE = process.env.HUB_URL || "http://localhost:8501";
const LANG = (process.argv[2] || "ru").toLowerCase();
const PAGES = [
  ["", "home"],
  ["/RAG", "rag"],
  ["/n8n", "n8n"],
  ["/Agents", "agents"],
  ["/Benchmarks", "benchmarks"],
  ["/Projects", "projects"],
  ["/Unified_Agent", "unified_agent"],
];

mkdirSync("shots", { recursive: true });

const browser = await chromium.launch({ channel: "chrome" });
const ctx = await browser.newContext({ viewport: { width: 1600, height: 900 } });
const page = await ctx.newPage();

await page.goto(BASE + "/", { waitUntil: "networkidle", timeout: 30000 }).catch(() => {});
await page.waitForTimeout(2500);

if (LANG === "en") {
  try {
    await page.getByText("English", { exact: false }).first().click({ timeout: 5000 });
    await page.waitForTimeout(2000);
  } catch (e) {
    console.warn("lang switch failed:", e.message);
  }
}

for (const [slug, name] of PAGES) {
  try {
    await page.goto(BASE + slug, { waitUntil: "networkidle", timeout: 30000 });
  } catch (e) {
    console.warn("warn:", slug, e.message);
  }
  // Ждём, пока Streamlit закончит выполнение скрипта (исчезнет статус-виджет),
  // иначе кадр получается пустым ("Stop / Deploy").
  await page.waitForTimeout(1200);
  await page
    .waitForFunction(() => !document.querySelector('[data-testid="stStatusWidget"]'), null, { timeout: 25000 })
    .catch(() => {});
  await page.waitForTimeout(800);
  await page.screenshot({ path: `shots/${LANG}_${name}.png` });
  console.log("shot", LANG, name);
}

await browser.close();
console.log("done -> shots/");
