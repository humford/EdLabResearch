const puppeteer = require('puppeteer');
var randomUseragent = require('random-useragent');

const chromeOptions = {
  headless:false,
  slowMo: 0
};

(async function main() {
  const screenshot = 'nytimes.png';
  const browser = await puppeteer.launch(chromeOptions);
  const page = await browser.newPage();
  await page.setUserAgent(randomUseragent.getRandom());
  await page.setViewport({
    width: 1280,
    height: 800
  });
  await page.goto('https://nytimes.com/');
  // await page.type('#username', "annewilliams515@yahoo.com");
  // await page.type('#password', "gdtrf8nyt");
  // await page.click('button[type=submit]');
  // await page.waitForNavigation({ timeout: 0 })
  // await page.goto('https://www.nytimes.com/2019/06/06/magazine/mike-gravel-teens-twitter-presidential-campaign.html');
  await page.evaluate(() => {
      window.scrollBy(0, window.innerHeight);
    });
  await page.waitFor(3000);
  await page.screenshot({
    path: screenshot,
    fullpage: true
  });
  browser.close()
  console.log('See screenshot: ' + screenshot)
})()
