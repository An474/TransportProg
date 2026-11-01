const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

const EDGE_PATH = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const OUT_DIR = path.join(__dirname, 'manual_assets');

if (!fs.existsSync(OUT_DIR)) {
  fs.mkdirSync(OUT_DIR, { recursive: true });
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function run() {
  console.log("Launching Edge headless...");
  const browser = await puppeteer.launch({
    executablePath: EDGE_PATH,
    headless: "new",
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1440,900']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900, deviceScaleFactor: 1.5 });

  console.log("1. Capturing Login screen...");
  await page.goto('http://localhost:8000/login', { waitUntil: 'networkidle0' });
  await sleep(800);
  await page.screenshot({ path: path.join(OUT_DIR, '01_login.png') });

  console.log("2. Logging in as dispatcher...");
  await page.type('input[placeholder="Введите логин"]', 'dispatcher');
  await page.type('input[placeholder="Введите пароль"]', 'disp123');
  await page.click('button[type="submit"]');
  await page.waitForSelector('.ant-layout-sider', { timeout: 8000 });
  await sleep(1500);

  console.log("Successfully logged in! Current URL:", page.url());

  // Helper to wait and screenshot
  async function snap(url, filename, delay = 1500) {
    console.log(`Capturing ${filename} (${url})...`);
    await page.goto(`http://localhost:8000${url}`, { waitUntil: 'networkidle0' });
    await sleep(delay);
    await page.screenshot({ path: path.join(OUT_DIR, filename) });
  }

  await snap('/', '02_dashboard.png', 1500);
  await snap('/vehicles', '03_vehicles.png', 1500);
  await snap('/assignments', '04_assignments.png', 1500);
  await snap('/waybills', '05_waybills.png', 1500);
  await snap('/fines', '06_fines.png', 1500);
  await snap('/maintenance', '07_maintenance.png', 1500);
  await snap('/fuel', '08_fuel.png', 1500);

  // Switch to admin for backups
  console.log("Switching to admin for backups...");
  await page.evaluate(() => localStorage.clear());
  await page.goto('http://localhost:8000/login', { waitUntil: 'networkidle0' });
  await sleep(800);
  await page.type('input[placeholder="Введите логин"]', 'admin');
  await page.type('input[placeholder="Введите пароль"]', 'admin123');
  await page.click('button[type="submit"]');
  await page.waitForSelector('.ant-layout-sider', { timeout: 8000 });
  await sleep(1500);

  await snap('/backups', '09_backups.png', 1500);

  await browser.close();
  console.log("ALL SCREENSHOTS CAPTURED CLEANLY!");
}

run().catch(err => {
  console.error("Error in capture:", err);
  process.exit(1);
});
