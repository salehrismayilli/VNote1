# VNote v5.5 (patched)

## Web app
Open `www/index.html` in a modern browser, or deploy the `www/` folder to HTTPS hosting. Microphone access requires HTTPS or localhost.

## Android
Run `npm install`, `npx cap add android`, `node scripts/patch-android.js`, `npx cap sync android`, then build the Android project. The Android patch is idempotent and checks the shortcut metadata rather than the app name.

## iOS
Requires macOS and Xcode. Run `npm install`, `npx cap add ios`, `node scripts/patch-ios.js`, and `npx cap sync ios`. A signed IPA requires an Apple signing identity and provisioning profile.

## Checks
- `npm run check:js` checks patch-script JavaScript syntax.
- `npm run test:smoke` runs the Playwright smoke test (install Playwright and its Chromium browser first).

Speech-to-text providers require the user's own API credentials and network access. Do not publish API keys or the included signing certificate.
