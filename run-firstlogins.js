// run-firstlogins.js
require('dotenv').config();
const fs = require('fs');
const path = require('path');
const { runLogin } = require('./firstlogin-template');
const { encrypt, decrypt } = require('./vault');

async function runAll(){
  const results = {};
  // Expect environment var CREDENTIALS_MAP which is encrypted JSON mapping platform => {username,password,loginUrl,selectors,...}
  const enc = process.env.CREDENTIALS_MAP;
  if(!enc) {
    console.error("CREDENTIALS_MAP env missing. Create encrypted credentials with vault.encrypt and set it as CREDENTIALS_MAP.");
    process.exit(1);
  }
  let credentials;
  try {
    credentials = JSON.parse(decrypt(enc));
  } catch(e){
    console.error("Failed decrypt credentials:", e.message);
    process.exit(1);
  }

  for(const platform of Object.keys(credentials)){
    console.log("Running login for", platform);
    const cfg = credentials[platform];
    const res = await runLogin(platform, cfg);
    if(res.success){
      // encrypt storageState and save to disk or to Replit secret via API call
      const toSave = Buffer.from(JSON.stringify(res.storageState)).toString('base64');
      const encSave = encrypt(toSave);
      // write to local secure file (ensure this file is not committed) and/or call VA Bot secret store API
      const outFile = path.join(__dirname, `sessions/${platform}.session.enc`);
      fs.mkdirSync(path.join(__dirname,'sessions'), { recursive: true });
      fs.writeFileSync(outFile, encSave, { mode: 0o600 });
      results[platform] = { ok: true, file: outFile };
    } else {
      results[platform] = { ok:false, error: res.error };
    }
  }

  // produce short report to stdout and also POST to VA Bot status endpoint if available
  console.log("First-login results:", results);
  // Optionally POST to your VA Bot API to register sessions: uncomment if you have /store-session API
  /*
  const fetch = require('node-fetch');
  await fetch(process.env.VA_BOT_URL + '/store-firstlogin-report', {
    method: 'POST',
    headers: { 'Content-Type':'application/json','X-VA-TOKEN': process.env.VA_STATUS_TOKEN },
    body: JSON.stringify(results)
  });
  */
}

runAll();
