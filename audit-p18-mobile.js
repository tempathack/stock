const { chromium } = require('/home/tempa/n8n/node_modules/playwright');

(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: '/home/tempa/.cache/ms-playwright/chromium_headless_shell-1217/chrome-headless-shell-linux64/chrome-headless-shell',
  });
  const context = await browser.newContext({
    viewport: { width: 390, height: 844 },
    userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    isMobile: true,
    hasTouch: true,
    deviceScaleFactor: 3,
  });

  const consoleMessages = [];
  const errors = [];

  // --- DASHBOARD ---
  console.log('[INFO] Navigating to dashboard...');
  const page = await context.newPage();
  page.on('console', msg => consoleMessages.push({ page: 'dashboard', type: msg.type(), text: msg.text() }));
  page.on('pageerror', err => errors.push({ page: 'dashboard', text: err.message }));

  await page.goto('http://localhost:5173/', { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(2000);
  await page.screenshot({ path: '/home/tempa/Desktop/priv-project/audit-p18-mobile-dashboard.png', fullPage: false });
  console.log('[INFO] Dashboard screenshot taken');

  const dashInfo = await page.evaluate(function() {
    var hamburger = document.querySelector('[aria-label*="menu"], button[class*="hamburger"], button[class*="menu-toggle"], [class*="MenuButton"], [class*="HamburgerButton"]');
    var bottomNav = document.querySelector('[class*="bottom-nav"], [class*="bottomNav"], [class*="BottomNav"]');
    var sidebar = document.querySelector('[class*="sidebar"], [class*="Sidebar"], [class*="drawer"], [class*="Drawer"]');
    return {
      scrollWidth: document.body.scrollWidth,
      clientWidth: document.body.clientWidth,
      hasOverflow: document.body.scrollWidth > document.body.clientWidth,
      hamburgerFound: !!hamburger,
      hamburgerClass: hamburger ? hamburger.className : null,
      bottomNavFound: !!bottomNav,
      bottomNavClass: bottomNav ? bottomNav.className : null,
      sidebarFound: !!sidebar,
      sidebarClass: sidebar ? sidebar.className : null,
      title: document.title,
    };
  });
  console.log('[DASHBOARD] info:', JSON.stringify(dashInfo, null, 2));

  // Scroll down to market list / treemap
  await page.evaluate(function() { window.scrollBy(0, 600); });
  await page.waitForTimeout(1000);
  await page.screenshot({ path: '/home/tempa/Desktop/priv-project/audit-p18-mobile-market-list.png', fullPage: false });
  console.log('[INFO] Market list screenshot taken');

  const marketEl = await page.evaluate(function() {
    var el = document.querySelector('[class*="MobileMarket"], [class*="mobileMarket"], [class*="treemap"], [class*="Treemap"], [class*="MarketList"]');
    return el ? el.className : null;
  });
  console.log('[DASHBOARD] MobileMarketList/treemap element:', marketEl);

  // --- FORECASTS ---
  console.log('[INFO] Navigating to forecasts...');
  const page2 = await context.newPage();
  page2.on('console', msg => consoleMessages.push({ page: 'forecasts', type: msg.type(), text: msg.text() }));
  page2.on('pageerror', err => errors.push({ page: 'forecasts', text: err.message }));
  await page2.goto('http://localhost:5173/forecasts', { waitUntil: 'networkidle', timeout: 30000 });
  await page2.waitForTimeout(2000);
  await page2.screenshot({ path: '/home/tempa/Desktop/priv-project/audit-p18-mobile-forecasts.png', fullPage: false });
  const fInfo = await page2.evaluate(function() {
    return {
      scrollWidth: document.body.scrollWidth,
      clientWidth: document.body.clientWidth,
      hasOverflow: document.body.scrollWidth > document.body.clientWidth,
    };
  });
  console.log('[FORECASTS] info:', JSON.stringify(fInfo));

  // --- MODELS ---
  console.log('[INFO] Navigating to models...');
  const page3 = await context.newPage();
  page3.on('console', msg => consoleMessages.push({ page: 'models', type: msg.type(), text: msg.text() }));
  page3.on('pageerror', err => errors.push({ page: 'models', text: err.message }));
  await page3.goto('http://localhost:5173/models', { waitUntil: 'networkidle', timeout: 30000 });
  await page3.waitForTimeout(2000);
  await page3.screenshot({ path: '/home/tempa/Desktop/priv-project/audit-p18-mobile-models.png', fullPage: false });
  const mInfo = await page3.evaluate(function() {
    return {
      scrollWidth: document.body.scrollWidth,
      clientWidth: document.body.clientWidth,
      hasOverflow: document.body.scrollWidth > document.body.clientWidth,
    };
  });
  console.log('[MODELS] info:', JSON.stringify(mInfo));

  // --- DRIFT ---
  console.log('[INFO] Navigating to drift...');
  const page4 = await context.newPage();
  page4.on('console', msg => consoleMessages.push({ page: 'drift', type: msg.type(), text: msg.text() }));
  page4.on('pageerror', err => errors.push({ page: 'drift', text: err.message }));
  await page4.goto('http://localhost:5173/drift', { waitUntil: 'networkidle', timeout: 30000 });
  await page4.waitForTimeout(2000);
  await page4.screenshot({ path: '/home/tempa/Desktop/priv-project/audit-p18-mobile-drift.png', fullPage: false });
  const dInfo = await page4.evaluate(function() {
    return {
      scrollWidth: document.body.scrollWidth,
      clientWidth: document.body.clientWidth,
      hasOverflow: document.body.scrollWidth > document.body.clientWidth,
    };
  });
  console.log('[DRIFT] info:', JSON.stringify(dInfo));

  // Summary of errors
  console.log('[ERRORS] page errors:', JSON.stringify(errors));
  var errConsole = consoleMessages.filter(function(m) { return m.type === 'error'; });
  console.log('[CONSOLE ERRORS] count:', errConsole.length);
  errConsole.forEach(function(m) {
    console.log('  [' + m.page + '] ' + m.text.substring(0, 200));
  });

  await browser.close();
  console.log('[DONE]');
})().catch(function(e) { console.error('[FATAL]', e.message); process.exit(1); });
