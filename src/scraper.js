import { launch } from 'puppeteer';
import { readFileSync, readdir, readdirSync, writeFileSync } from 'fs';

// Some of these just straight up crash the browser I don't know why
const BANNED_URLS = [
  'https://www.huffpost.com/entry/world-ocean-plastic-trash_n_6674182'
]

// global browser
let browser;

async function getTextFromUrl(url) {

  const page = await browser.newPage();

  await page.setViewport({
    width: 1080,
    height: 4000, // simulate scrolling
  });

  // Navigate to the URL
  try {
    await page.goto(url);
  } catch (e) {
    console.log(`Failed to navigate to ${url}`);
    console.log(e);
    await page.close();
    return '';
  }

  // Wait for the page to fully load
  // page.setDefaultNavigationTimeout(0);
  try {
    await page.waitForNetworkIdle({
      idleTime: 1000,
      timeout: 15000
    });
  } catch (e) {
    if (e.name === 'TimeoutError') {
      console.log('Timeout error. Assume page is loaded');
    }
  }

  const textContent = await page.evaluate(() => {
    // Use this selector to get the text content based on the structure of the webpage
    const textElement = document.querySelector('body');

    // Return the text content
    return textElement ? textElement.innerText.trim() : '';
  });

  // writeFileSync('output.html', textContent);

  await page.close();

  return textContent;
}

async function main() {
  const sourceDirectory = process.argv[2];
  const destDirectory = process.argv[3];

  if (!sourceDirectory || !destDirectory) {
    console.log('Please provide source and destination directories');
    process.exit(1);
  }

  // list all files in the directory
  const files = readdirSync(sourceDirectory);

  const to_scrape = [];
  const scraped = readdirSync(destDirectory).map(file => JSON.parse(readFileSync(`${destDirectory}/${file}`)));

  for (const file of files) {
    const content = JSON.parse(readFileSync(`${sourceDirectory}/${file}`));
    to_scrape.push({
      file,
      content,
    });
  }

  console.log(`Found ${to_scrape.length} files to scrape`);

  browser = await launch({
    headless: false
  });

  for (const { file, content } of to_scrape) {
    if (BANNED_URLS.includes(content.href)) {
      console.log(`Skipping banned url ${content.href}`);
      continue;
    }

    if (scraped.find(({ href }) => href === content.href)?.textContent) {
      console.log(`Skipping ${content.href}`);
      continue;
    }

    const { href } = content;
    console.log(`Scraping ${href}`);
    const textContent = await getTextFromUrl(href);

    writeFileSync(`${destDirectory}/${file}`, JSON.stringify({
      ...content,
      textContent,
    }, null, 2));
  }

  await browser.close();
}

main();
