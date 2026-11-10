// "npx cap add android"-dan sonra işləyir: icazələr, ikon qısayolu (basılı saxla), ikonlar
const fs = require('fs'), path = require('path');
const MAIN = 'android/app/src/main', RES = path.join(MAIN, 'res');
const mf = path.join(MAIN, 'AndroidManifest.xml');
let x = fs.readFileSync(mf, 'utf8');

if (!x.includes('android.permission.RECORD_AUDIO'))
  x = x.replace('</manifest>', '  <uses-permission android:name="android.permission.RECORD_AUDIO" />\n</manifest>');
for (const perm of ['POST_NOTIFICATIONS', 'SCHEDULE_EXACT_ALARM', 'RECEIVE_BOOT_COMPLETED', 'MODIFY_AUDIO_SETTINGS'])
  if (!x.includes('android.permission.' + perm))
    x = x.replace('</manifest>', `  <uses-permission android:name="android.permission.${perm}" />\n</manifest>`);
if (!x.includes('<queries>'))
  x = x.replace('</manifest>', '  <queries><intent><action android:name="android.speech.RecognitionService" /></intent></queries>\n</manifest>');
if (!x.includes('android.app.shortcuts') || !x.includes('vnote://record'))
  x = x.replace('</activity>',
`      <intent-filter>
        <action android:name="android.intent.action.VIEW" />
        <category android:name="android.intent.category.DEFAULT" />
        <category android:name="android.intent.category.BROWSABLE" />
        <data android:scheme="vnote" android:host="record" />
      </intent-filter>
      <meta-data android:name="android.app.shortcuts" android:resource="@xml/shortcuts" />
    </activity>`);
if (!x.includes('windowSoftInputMode')) x = x.replace('<activity ', '<activity android:windowSoftInputMode="adjustResize" ');
fs.writeFileSync(mf, x);

fs.mkdirSync(path.join(RES, 'xml'), { recursive: true });
fs.writeFileSync(path.join(RES, 'xml/shortcuts.xml'),
`<?xml version="1.0" encoding="utf-8"?>
<shortcuts xmlns:android="http://schemas.android.com/apk/res/android">
  <shortcut android:shortcutId="record" android:enabled="true" android:icon="@mipmap/ic_launcher"
    android:shortcutShortLabel="@string/shortcut_record" android:shortcutLongLabel="@string/shortcut_record">
    <intent android:action="android.intent.action.VIEW" android:data="vnote://record"
      android:targetPackage="com.vnote.app" android:targetClass="com.vnote.app.MainActivity" />
  </shortcut>
</shortcuts>
`);
const L = { '': 'Record voice', '-az': 'Səs yaz', '-tr': 'Ses kaydet', '-ru': 'Записать голос' };
for (const [s, v] of Object.entries(L)) {
  const d = path.join(RES, 'values' + s); fs.mkdirSync(d, { recursive: true });
  fs.writeFileSync(path.join(d, 'shortcut_strings.xml'), `<?xml version="1.0" encoding="utf-8"?>\n<resources><string name="shortcut_record">${v}</string></resources>\n`);
}
// İkon: yalnız narıncı mikrofon (çərçivəsiz, şəffaf fon)
fs.mkdirSync(path.join(RES, 'mipmap-anydpi-v26'), { recursive: true });
const AD = `<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
  <background android:drawable="@color/vnote_icon_bg" />
  <foreground android:drawable="@mipmap/vnote_fg" />
</adaptive-icon>
`;
fs.writeFileSync(path.join(RES, 'mipmap-anydpi-v26/ic_launcher.xml'), AD);
fs.writeFileSync(path.join(RES, 'mipmap-anydpi-v26/ic_launcher_round.xml'), AD);
fs.writeFileSync(path.join(RES, 'values/vnote_colors.xml'), '<?xml version="1.0" encoding="utf-8"?>\n<resources><color name="vnote_icon_bg">#00000000</color></resources>\n');
for (const d of ['mdpi', 'hdpi', 'xhdpi', 'xxhdpi', 'xxxhdpi']) {
  const dir = path.join(RES, 'mipmap-' + d);
  fs.mkdirSync(dir, { recursive: true });
  fs.copyFileSync(`scripts/icons/${d}.png`, path.join(dir, 'ic_launcher.png'));
  fs.copyFileSync(`scripts/icons/${d}_round.png`, path.join(dir, 'ic_launcher_round.png'));
  fs.copyFileSync(`scripts/icons/${d}_fg.png`, path.join(dir, 'vnote_fg.png'));
}

// Sabit imza açarı: yeni versiyanı köhnənin üstünə quraşdıranda notlar silinməsin
const gp = path.join('android/app/build.gradle');
let g = fs.readFileSync(gp, 'utf8');
if (!g.includes('vnote.p12')) {
  g = g.replace(/android\s*\{/, `android {
    signingConfigs {
        debug {
            storeFile file('../../scripts/vnote.p12')
            storePassword 'vnote123'
            keyAlias 'vnote'
            keyPassword 'vnote123'
            storeType 'pkcs12'
        }
    }`);
  fs.writeFileSync(gp, g);
}
g = fs.readFileSync(gp, 'utf8');
g = g.replace(/versionCode\s+\d+/, 'versionCode ' + Math.floor(Date.now() / 60000)).replace(/versionName\s+"[^"]*"/, 'versionName "' + (process.env.VER || '1.0') + '"');
fs.writeFileSync(gp, g);
console.log('Android patch OK');
