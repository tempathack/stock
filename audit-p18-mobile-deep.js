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

  // --- DASHBOARD: deep nav inspection ---
  const page = await context.newPage();
  const consoleMessages = [];
  page.on('console', msg => consoleMessages.push({ type: msg.type(), text: msg.text() }));
  page.on('pageerror', err => consoleMessages.push({ type: 'pageerror', text: err.message }));

  await page.goto('http://localhost:5173/', { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(2000);

  const navInfo = await page.evaluate(function() {
    // Find nav element
    var navEl = document.querySelector('nav, header, [class*="nav"], [class*="Nav"], [class*="header"], [class*="Header"]');
    var navHTML = navEl ? navEl.outerHTML.substring(0, 800) : null;

    // Find all button/link elements in nav area
    var allNavLinks = [];
    var links = document.querySelectorAll('nav a, nav button, header a, header button, [class*="nav"] a, [class*="nav"] button, [class*="Nav"] a, [class*="Nav"] button');
    links.forEach(function(l) {
      allNavLinks.push({ tag: l.tagName, class: l.className.substring(0,100), text: l.textContent.trim().substring(0,50) });
    });

    // Check for any elements that suggest sidebar/hamburger
    var allButtons = document.querySelectorAll('button');
    var buttonList = [];
    allButtons.forEach(function(b) {
      buttonList.push({ class: b.className.substring(0,80), aria: b.getAttribute('aria-label'), text: b.textContent.trim().substring(0,30) });
    });

    // Check horizontal overflow for individual elements
    var overflowElements = [];
    var all = document.querySelectorAll('*');
    for (var i = 0; i < all.length; i++) {
      var el = all[i];
      if (el.scrollWidth > 390) {
        overflowElements.push({ tag: el.tagName, class: el.className.toString().substring(0,80), scrollWidth: el.scrollWidth });
        if (overflowElements.length >= 10) break;
      }
    }

    return {
      navHTML: navHTML,
      navLinks: allNavLinks.slice(0, 15),
      buttons: buttonList.slice(0, 10),
      overflowElements: overflowElements,
    };
  });

  console.log('=== DASHBOARD NAV HTML (first 800 chars) ===');
  console.log(navInfo.navHTML);
  console.log('=== NAV LINKS ===');
  console.log(JSON.stringify(navInfo.navLinks, null, 2));
  console.log('=== BUTTONS ===');
  console.log(JSON.stringify(navInfo.buttons, null, 2));
  console.log('=== OVERFLOW ELEMENTS ===');
  console.log(JSON.stringify(navInfo.overflowElements, null, 2));

  // --- FORECASTS: check table overflow ---
  const page2 = await context.newPage();
  const forecastsConsole = [];
  page2.on('console', msg => forecastsConsole.push({ type: msg.type(), text: msg.text() }));
  page2.on('pageerror', err => forecastsConsole.push({ type: 'pageerror', text: err.message }));
  await page2.goto('http://localhost:5173/forecasts', { waitUntil: 'networkidle', timeout: 30000 });
  await page2.waitForTimeout(2000);

  const forecastsInfo = await page2.evaluate(function() {
    var table = document.querySelector('table, [class*="table"], [class*="Table"], [role="grid"], [role="table"]');
    var tableOverflow = table ? { scrollWidth: table.scrollWidth, clientWidth: table.clientWidth, class: table.className.toString().substring(0,80) } : null;

    var overflowEls = [];
    var all = document.querySelectorAll('*');
    for (var i = 0; i < all.length; i++) {
      var el = all[i];
      if (el.scrollWidth > 390 + 5) {  // 5px tolerance
        overflowEls.push({ tag: el.tagName, class: el.className.toString().substring(0,80), scrollWidth: el.scrollWidth });
        if (overflowEls.length >= 10) break;
      }
    }

    // Check nav on this page too
    var navEl = document.querySelector('nav, header');
    var navTruncated = navEl ? navEl.textContent.trim().substring(0, 200) : null;

    return {
      tableInfo: tableOverflow,
      overflowElements: overflowEls,
      navText: navTruncated,
    };
  });
  console.log('=== FORECASTS TABLE ===');
  console.log(JSON.stringify(forecastsInfo, null, 2));
  console.log('=== FORECASTS CONSOLE ERRORS ===');
  forecastsConsole.filter(function(m) { return m.type === 'error' || m.type === 'pageerror'; }).forEach(function(m) {
    console.log(' ', m.text.substring(0, 200));
  });

  // --- MODELS: check table overflow ---
  const page3 = await context.newPage();
  const modelsConsole = [];
  page3.on('console', msg => modelsConsole.push({ type: msg.type(), text: msg.text() }));
  page3.on('pageerror', err => modelsConsole.push({ type: 'pageerror', text: err.message }));
  await page3.goto('http://localhost:5173/models', { waitUntil: 'networkidle', timeout: 30000 });
  await page3.waitForTimeout(2000);

  const modelsInfo = await page3.evaluate(function() {
    var overflowEls = [];
    var all = document.querySelectorAll('*');
    for (var i = 0; i < all.length; i++) {
      var el = all[i];
      if (el.scrollWidth > 390 + 5) {
        overflowEls.push({ tag: el.tagName, class: el.className.toString().substring(0,80), scrollWidth: el.scrollWidth });
        if (overflowEls.length >= 10) break;
      }
    }
    return { overflowElements: overflowEls };
  });
  console.log('=== MODELS OVERFLOW ===');
  console.log(JSON.stringify(modelsInfo.overflowElements, null, 2));
  console.log('=== MODELS CONSOLE ERRORS ===');
  modelsConsole.filter(function(m) { return m.type === 'error' || m.type === 'pageerror'; }).forEach(function(m) {
    console.log(' ', m.text.substring(0, 200));
  });

  // --- DRIFT ---
  const page4 = await context.newPage();
  const driftConsole = [];
  page4.on('console', msg => driftConsole.push({ type: msg.type(), text: msg.text() }));
  page4.on('pageerror', err => driftConsole.push({ type: 'pageerror', text: err.message }));
  await page4.goto('http://localhost:5173/drift', { waitUntil: 'networkidle', timeout: 30000 });
  await page4.waitForTimeout(2000);

  const driftInfo = await page4.evaluate(function() {
    var overflowEls = [];
    var all = document.querySelectorAll('*');
    for (var i = 0; i < all.length; i++) {
      var el = all[i];
      if (el.scrollWidth > 390 + 5) {
        overflowEls.push({ tag: el.tagName, class: el.className.toString().substring(0,80), scrollWidth: el.scrollWidth });
        if (overflowEls.length >= 10) break;
      }
    }
    return { overflowElements: overflowEls };
  });
  console.log('=== DRIFT OVERFLOW ===');
  console.log(JSON.stringify(driftInfo.overflowElements, null, 2));
  console.log('=== DRIFT CONSOLE ERRORS ===');
  driftConsole.filter(function(m) { return m.type === 'error' || m.type === 'pageerror'; }).forEach(function(m) {
    console.log(' ', m.text.substring(0, 200));
  });

  // Dashboard console messages summary
  console.log('=== DASHBOARD ALL CONSOLE ===');
  consoleMessages.filter(function(m) { return m.type === 'error' || m.type === 'pageerror'; }).forEach(function(m) {
    console.log(' ', m.text.substring(0, 200));
  });
  console.log('Dashboard console error count:', consoleMessages.filter(function(m) { return m.type === 'error' || m.type === 'pageerror'; }).length);

  await browser.close();
  console.log('[DONE]');
})().catch(function(e) { console.error('[FATAL]', e.message); process.exit(1); });
