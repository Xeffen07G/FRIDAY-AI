import puppeteer from 'puppeteer';

(async () => {
  console.log("Launching headless browser with fake media streams...");
  const browser = await puppeteer.launch({
    headless: true, // true or "new"
    args: [
      '--use-fake-ui-for-media-stream',
      '--use-fake-device-for-media-stream',
      // We aren't supplying a specific wav file, so chrome will generate a default beep audio
    ]
  });
  
  const page = await browser.newPage();
  
  // Intercept console to monitor frontend logs
  page.on('console', msg => console.log('BROWSER:', msg.text()));

  console.log("Navigating to frontend...");
  await page.goto('http://localhost:5173/');
  
  console.log("Waiting for app to initialize...");
  await new Promise(r => setTimeout(r, 2000));

  console.log("Triggering startRecording via mic button...");
  await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button')).find(b => b.title === 'Voice Command');
    if (btn) {
      console.log("Found Voice Command button. Clicking...");
      btn.click();
    } else {
      console.log("Could not find Voice Command button.");
    }
  });

  // Let it record for 3 seconds (it should capture the fake beep audio)
  console.log("Recording fake audio for 3 seconds...");
  await new Promise(r => setTimeout(r, 3000));

  console.log("Triggering stopRecording...");
  await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button')).find(b => b.title === 'Stop Listening');
    if (btn) {
      console.log("Found Stop Listening button. Clicking...");
      btn.click();
    } else {
      console.log("Could not find Stop Listening button.");
    }
  });

  // Wait for STT and TTS response cycle
  console.log("Waiting for backend response...");
  await new Promise(r => setTimeout(r, 8000));

  console.log("Test complete. Closing browser.");
  await browser.close();
})();
