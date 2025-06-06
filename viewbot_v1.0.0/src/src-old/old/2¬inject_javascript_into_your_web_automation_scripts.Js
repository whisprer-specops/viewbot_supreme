const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ headless: false });
  const page = await browser.newPage();

  await page.evaluateOnNewDocument(() => {
    Object.defineProperty(navigator, 'platform', {
      get: () => 'Win32'
    });
    Object.defineProperty(navigator, 'language', {
      get: () => 'en-US'
    });
    Object.defineProperty(navigator, 'webdriver', {
      get: () => false  // Prevent detection of automated scripts
    });
  });

  await page.goto('http://example.com');
  // Perform automation tasks

  await browser.close();
})();
