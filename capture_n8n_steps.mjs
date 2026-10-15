/**
 * Делает детерминированные кадры по n8n-воркфлоу ПО ПЛАНУ (n8n_video_plan.json).
 * Запись видео НЕ используется — это скриншоты, поэтому кадров «загрузка страницы»
 * нет: каждый кадр снимается только после полной отрисовки холста и нод.
 *
 *   node capture_n8n_steps.mjs support_demo
 *
 * Требует: запущенный n8n (http://localhost:5678) и построенный план.
 * Результат: docs/n8n_shots/<key>_<i>.png
 */
import { chromium } from "playwright";
import { readFileSync, mkdirSync } from "node:fs";

const PLAN = JSON.parse(readFileSync("n8n_video_plan.json", "utf8"));
const key = process.argv[2];
if (!key || !PLAN[key]) {
  console.error("usage: node capture_n8n_steps.mjs <key>");
  process.exit(1);
}
const spec = PLAN[key];
const SHOT = "docs/n8n_shots";
mkdirSync(SHOT, { recursive: true });

const browser = await chromium.launch({ channel: "chrome", headless: true });

// Авторизация без записи, чтобы не светить логин/почту
const authCtx = await browser.newContext();
const authPage = await authCtx.newPage();
await authPage.goto("http://localhost:5678/signin", { waitUntil: "domcontentloaded", timeout: 20000 });
await authPage.waitForTimeout(1500);
await authPage.locator("#emailOrLdapLoginId").fill("user@example.com");
await authPage.locator("#password").fill("YOUR_N8N_PASSWORD");
await authPage.keyboard.press("Enter");
await authPage.waitForURL("**/home/**", { timeout: 20000 });
const storage = await authCtx.storageState();
await authCtx.close();

// Контекст для кадров — скрываем профиль/почту/аватар
const ctx = await browser.newContext({
  storageState: storage,
  viewport: { width: 1600, height: 900 },
});
await ctx.addInitScript(() => {
  const s = document.createElement("style");
  s.innerHTML = `[data-test-id="user-menu"], [class*="userProfile"], [class*="userMenu"],
                 [class*="avatar"], [class*="Avatar"], [data-test-id="sidebar-menu"] { display: none !important; }`;
  document.head.appendChild(s);
});
const page = await ctx.newPage();

await page.goto(`http://localhost:5678/workflow/${spec.workflow_id}`, { waitUntil: "domcontentloaded", timeout: 30000 });
// Ждём РЕАЛЬНУЮ отрисовку холста и нод (только после этого снимаем кадры)
await page.waitForSelector(".vue-flow__node", { timeout: 40000 });
await page.waitForTimeout(2500);

const fit = async () => {
  try { await page.locator('button:has-text("Fit")').first().click({ timeout: 3000 }); } catch (e) {}
  await page.waitForTimeout(700);
};

for (let i = 0; i < spec.steps.length; i++) {
  const st = spec.steps[i];
  const out = `${SHOT}/${key}_${String(i).padStart(2, "0")}.png`;
  if (st.node) {
    await fit();
    const node = page.locator(".vue-flow__node", { hasText: st.node }).first();
    try {
      await node.dblclick({ timeout: 6000 });
      await page.waitForTimeout(1200);
      console.log(`step ${i}: node "${st.node}" panel open`);
    } catch (e) {
      console.log(`step ${i}: node "${st.node}" not found`);
    }
  } else {
    await fit();
    console.log(`step ${i}: overview`);
  }
  await page.waitForTimeout(400);
  await page.screenshot({ path: out });
  // закрыть панель параметров перед следующим шагом
  await page.keyboard.press("Escape").catch(() => {});
  await page.waitForTimeout(400);
}

await ctx.close();
await browser.close();
console.log("captured:", key);
