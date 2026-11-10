// "npx cap add ios"-dan sonra: icazə mətnləri və ikon
const fs = require('fs'), path = require('path'), { execSync } = require('child_process');
const plist = 'ios/App/App/Info.plist';
const set = (k, v) => {
  try { execSync(`/usr/libexec/PlistBuddy -c "Add :${k} string '${v}'" ${plist}`); }
  catch (e) { execSync(`/usr/libexec/PlistBuddy -c "Set :${k} '${v}'" ${plist}`); }
};
set('NSMicrophoneUsageDescription', 'VNote records your voice notes');
set('NSSpeechRecognitionUsageDescription', 'VNote converts speech to text');
set('NSPhotoLibraryUsageDescription', 'Attach photos to notes');
set('NSCameraUsageDescription', 'Attach photos to notes');
const dir = 'ios/App/App/Assets.xcassets/AppIcon.appiconset';
if (fs.existsSync(dir)) fs.readdirSync(dir).filter(f => f.endsWith('.png')).forEach(f => fs.copyFileSync('scripts/ios-icon-1024.png', path.join(dir, f)));
console.log('iOS patch OK');
