// firstlogin-template.js
const { chromium } = require('playwright');
const { encrypt, decrypt } = require('./vault'); // if you need decrypt of stored creds

// Example input credentials loaded from env or secure store
// For real run, populate process.env.CREDENTIALS_JSON with encrypted JSON via vault.encrypt(...)
async function runLogin(platformName, loginConfig) {
  // loginConfig: { loginUrl, usernameField, passwordField, submitSelector, username, password, additionalSteps: [] }
  console.log(`[${platformName}] starting login`);
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();
  try {
    await page.goto(loginConfig.loginUrl, { waitUntil: 'networkidle' });

    if(loginConfig.preHooks){
      for(const h of loginConfig.preHooks) {
        await page[h.action](...h.args);
      }
    }

    await page.waitForSelector(loginConfig.usernameField, { timeout: 15000 });
    await page.fill(loginConfig.usernameField, loginConfig.username);
    await page.fill(loginConfig.passwordField, loginConfig.password);
    await page.click(loginConfig.submitSelector);

    // optional extra steps (2FA, accept cookie/terms)
    if(loginConfig.additionalSteps){
      for(const step of loginConfig.additionalSteps){
        if(step.type === 'waitFor') await page.waitForSelector(step.selector, { timeout: step.timeout || 15000 });
        if(step.type === 'click') await page.click(step.selector);
        if(step.type === 'fill') await page.fill(step.selector, step.value);
      }
    }

    // wait for success pattern — user should set successSelector
    if(loginConfig.successSelector){
      await page.waitForSelector(loginConfig.successSelector, { timeout: 20000 });
    } else {
      // generic wait a bit
      await page.waitForTimeout(3000);
    }

    // store cookies / localStorage
    const cookies = await context.cookies();
    const storageState = await context.storageState();
    // return object to be encrypted and saved
    console.log(`[${platformName}] login success, captured cookies`);
    await browser.close();
    return { success: true, cookies, storageState };
  } catch (err) {
    await browser.close();
    console.error(`[${platformName}] login failed:`, err.message);
    return { success: false, error: err.message };
  }
}

module.exports = { runLogin };
