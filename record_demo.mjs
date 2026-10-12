/**
 * Записывает обзор портфолио-хаба в видеофайл.
 *
 * Требования:
 *   - хаб запущен (start.cmd → http://localhost:8501)
 *   - Playwright:  npm i --no-save playwright
 *
 * Запуск:
 *   node tools/record_demo.mjs
 *   # или с другим адресом:
 *   set HUB_URL=http://localhost:7860 && node tools/record_demo.mjs
 *
 * Результат: docs/hub-demo.webm (затем можно сжать в mp4 через ffmpeg).
 */
import { chromium } from "playwright";
import { mkdirSync } from "node:fs";

const BASE = process.env.HUB_URL || "http://localhost:8501";
const OUT = "docs";
const PAGES = ["", "/RAG", "/n8n", "/Agents", "/Benchmarks", "/Projects", "/Unified_Agent"];
const DWELL_MS = 3500;

mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch({ channel: "chrome" });
const ctx = await browser.newContext({
  viewport: { width: 1440, height: 900 },
  recordVideo: { dir: OUT, size: { width: 1440, height: 900 } },
});
const page = await ctx.newPage();

for (const slug of PAGES) {
  const url = BASE + slug;
  try {
    await page.goto(url, { waitUntil: "networkidle", timeout: 30000 });
  } catch (e) {
    console.warn("warn:", url, e.message);
  }
  await page.waitForTimeout(DWELL_MS);
  console.log("captured", url);
}

await ctx.close();
await browser.close();
console.log("Done. Video is in", OUT + "/ (playwright-*.webm)");
