const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('⚡ [CLIVE BUILD] Starting Netlify / Production Multi-Target Build...');

const rootDir = path.resolve(__dirname, '..');
const frontendDir = path.join(rootDir, 'frontend');
const frontendDist = path.join(frontendDir, 'dist');
const rootDist = path.join(rootDir, 'dist');

// 1. Install frontend dependencies if needed & run Vite build
console.log('📦 [1/3] Building Vite Frontend in ' + frontendDir + '...');
try {
  execSync('npm run build', { cwd: frontendDir, stdio: 'inherit' });
} catch (e) {
  console.log('Retrying with npm install first...');
  execSync('npm install', { cwd: frontendDir, stdio: 'inherit' });
  execSync('npm run build', { cwd: frontendDir, stdio: 'inherit' });
}

// 2. Ensure root dist exists and copy all files
console.log('📂 [2/3] Mirroring dist to root ./dist for universal Netlify publish paths...');
if (fs.existsSync(rootDist)) {
  fs.rmSync(rootDist, { recursive: true, force: true });
}

function copyDir(src, dest) {
  fs.mkdirSync(dest, { recursive: true });
  const entries = fs.readdirSync(src, { withFileTypes: true });
  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      copyDir(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

copyDir(frontendDist, rootDist);

// 3. Ensure _redirects is present in both rootDist and frontendDist
const redirectsSrc = path.join(frontendDir, 'public', '_redirects');
if (fs.existsSync(redirectsSrc)) {
  fs.copyFileSync(redirectsSrc, path.join(rootDist, '_redirects'));
  fs.copyFileSync(redirectsSrc, path.join(frontendDist, '_redirects'));
} else {
  fs.writeFileSync(path.join(rootDist, '_redirects'), '/*    /index.html   200\n');
  fs.writeFileSync(path.join(frontendDist, '_redirects'), '/*    /index.html   200\n');
}

console.log('✅ [3/3] Build complete! Published at ./dist and ./frontend/dist successfully.');
