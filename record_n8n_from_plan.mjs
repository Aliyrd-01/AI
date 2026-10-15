/**
 * Записывает видео прохода по одному n8n-воркфлоу по плану (n8n_video_plan.json).
 * Для каждого шага: клик по реальной ноде (открывает панель параметров) и ожидание
 * длительности её озвучки — так видео синхронно с голосом. Шаги без ноды = общий план.
 *
 *   node record_n8n_from_plan.mjs support_demo
 *
 * Перед запуском: n8n на http://localhost:5678, план построен (python n8n_video_plan.py).
 * Результат: hub/assets/n8n/<key>_raw.webm
 */
import { chromium } from "playwright";
import { readFileSync, mkdirSync, renameSync } from "node:fs";

const PLAN = JSON.parse(readFileSync("n8n_video_plan.json", "utf8"));
const key = process.argv[2];
if (!key || !PLAN[key]) {
  console.error("usage: node record_n8n_from_plan.mjs <key>. keys:", Object.keys(PLAN).join(", "));
  process.exit(1);
}
const spec = PLAN[key];
const OUT = "hub/assets/n8n";
mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch({ channel: "chrome", headless: true });

// 1) Авторизация БЕЗ записи, чтобы логин/почта не попали в видео.
const authCtx = await browser.newContext();
const authPage = await authCtx.newPage();
await authPage.goto("http://localhost:5678/signin", { waitUntil: "domcontentloaded", timeout: 20000 });
await authPage.waitForTimeout(1500);
await authPage.locator("#emailOrLdapLoginId").fill("user@example.com");
await authPage.locator("#password").fill("YOUR_N8N_PASSWORD");
await authPage.keyboard.press("Enter");
await authPage.waitForURL("**/home/**", { timeout: 20000 });
await authPage.waitForTimeout(1000);
const storage = await authCtx.storageState();
await authCtx.close();

// 2) Контекст записи — уже авторизован, видео начинается со холста воркфлоу.
const ctx = await browser.newContext({
  storageState: storage,
  recordVideo: { dir: OUT, size: { width: 1280, height: 720 } },
  viewport: { width: 1280, height: 720 },
});
const page = await ctx.newPage();

// Скрываем профиль/почту/аватар во всём приложении
await page.addInitScript(() => {
  const s = document.createElement("style");
  s.innerHTML = `[data-test-id="user-menu"], [class*="userProfile"], [class*="userMenu"],
                 [class*="avatar"], [class*="Avatar"] { display: none !important; visibility: hidden !important; }`;
  document.head.appendChild(s);
});

// Открываем воркфлоу
await page.goto(`http://localhost:5678/workflow/${spec.workflow_id}`, { waitUntil: "domcontentloaded", timeout: 30000 });
await page.waitForTimeout(6000);
// Ждём появления холста и нод
await page.waitForSelector(".vue-flow__node", { timeout: 30000 }).catch(() => {});
await page.waitForTimeout(1500);

const fit = async () => {
  try { await page.locator('button:has-text("Fit")').first().click({ timeout: 3000 }); } catch (e) {}
  await page.waitForTimeout(500);
};

await fit();

for (let i = 0; i < spec.steps.length; i++) {
  const st = spec.steps[i];
  const ms = Math.round(st.duration * 1000);
  if (st.node) {
    const node = page.locator(".vue-flow__node", { hasText: st.node }).first();
    try {
      await node.dblclick({ timeout: 5000 });
      console.log(`step ${i}: opened node "${st.node}" for ${st.duration}s`);
    } catch (e) {
      console.log(`step ${i}: node "${st.node}" not found (${e.message.split("\n")[0]})`);
    }
    await page.waitForTimeout(ms);
    await page.keyboard.press("Escape").catch(() => {});
    await page.waitForTimeout(500);
  } else {
    await fit();
    console.log(`step ${i}: overview for ${st.duration}s`);
    await page.waitForTimeout(ms);
  }
}

const video = page.video();
await page.close();
await ctx.close();
await browser.close();
if (video) {
  const src = await video.path();
  const dst = `${OUT}/${key}_raw.webm`;
  try { renameSync(src, dst); console.log("RAW_VIDEO:", dst); }
  catch (e) { console.log("RAW_VIDEO:", src); }
}
