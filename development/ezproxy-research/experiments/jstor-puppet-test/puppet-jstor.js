const puppeteer = require('puppeteer');
var randomUseragent = require('random-useragent');
var site = process.argv.slice(2)[0];

const chromeOptions = {
  headless: true,
  defaultViewport: null,
  slowMo: 10
};

(async function main() {
  const browser = await puppeteer.launch(chromeOptions);
  const page = await browser.newPage();
  await page.setUserAgent(randomUseragent.getRandom());
  await page.setViewport({
    width: 1280,
    height: 800
  });
  await page.goto(site);
  let bodyHTML = await page.evaluate(() => document.body.innerHTML);
  browser.close();
  console.log(bodyHTML);
  return process.exit(0);
})()
