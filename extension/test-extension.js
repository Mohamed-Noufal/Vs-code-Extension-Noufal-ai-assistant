// Test script to verify Noufal AI Assistant extension
const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🧪 Testing Noufal AI Assistant Extension...\n');

// helpers
function exists(p) {
	try { return fs.existsSync(p); } catch { return false; }
}

// expected paths
const root = __dirname;
const vsix110 = path.join(root, 'noufal-ai-assistant-2.0.0.vsix');
const outExt = path.join(root, 'out', 'extension.js');
const outSimple = path.join(root, 'out', 'extension-simple.js');
const pkgPath = path.join(root, 'package.json');
const ignorePath = path.join(root, '.vscodeignore');

// 1) VSIX exists
console.log('1️⃣ Checking VSIX package...');
if (exists(vsix110)) {
	const stats = fs.statSync(vsix110);
	console.log('✅ VSIX package exists:', path.basename(vsix110), `(${(stats.size/1024).toFixed(2)} KB)`);
} else {
	console.log('❌ VSIX package not found:', path.basename(vsix110));
}

// 2) Compiled outputs
console.log('\n2️⃣ Checking compiled outputs...');
if (exists(outExt)) {
	const stats = fs.statSync(outExt);
	console.log('✅ out/extension.js found', `(${(stats.size/1024).toFixed(2)} KB)`);
} else {
	console.log('❌ out/extension.js missing');
}
console.log(exists(outSimple) ? '✅ out/extension-simple.js found' : 'ℹ️ out/extension-simple.js not found (optional)');

// 3) Package.json sanity
console.log('\n3️⃣ Checking package.json...');
if (exists(pkgPath)) {
	const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf8'));
	console.log('✅ package.json found');
	console.log('   name:', pkg.name);
	console.log('   version:', pkg.version);
	console.log('   main:', pkg.main);
	console.log('   engines.vscode:', pkg.engines && pkg.engines.vscode);
	console.log('   commands:', pkg.contributes && pkg.contributes.commands ? pkg.contributes.commands.length : 0);
} else {
	console.log('❌ package.json missing');
}

// 4) .vscodeignore present (prevents invalid relative paths)
console.log('\n4️⃣ Checking .vscodeignore...');
if (exists(ignorePath)) {
	const txt = fs.readFileSync(ignorePath, 'utf8');
	const hasRule = /\.\./.test(txt) && txt.includes('../.vscode/');
	console.log(hasRule ? '✅ .vscodeignore present with parent exclusion' : '⚠️ .vscodeignore present, please ensure parent exclusion exists');
} else {
	console.log('⚠️ .vscodeignore not found');
}

// 5) Feature tokens present in build
console.log('\n5️⃣ Scanning built code for key features...');
if (exists(outExt)) {
	const js = fs.readFileSync(outExt, 'utf8');
	const feats = [
		['Streaming', /interactWithAIStream/],
		['KeepAlive', /keepAlive\s*:\s*true/],
		['Timeouts', /setTimeout\(/],
		['Retries', /backoffMs/],
		['FileValidation', /isValidFilePath/],
		['OverwriteConfirm', /showWarningMessage\([^)]*Overwrite/],
		['ProgressUI', /withProgress\(/],
		['PrismHighlight', /prism/i],
		['Attachments', /attachmentsAdded/],
		['ToolBridgeRead', /toolReadFile/],
		['ToolBridgeWrite', /toolWriteFile/],
		['ToolBridgeCLI', /toolRunCommand/],
		['MemoryManager', /class MemoryManager/],
		['PlannerCoder', /plannerCoderCommand/]
	];
	feats.forEach(([label, re]) => {
		console.log(re.test(js) ? `✅ ${label}` : `❌ ${label} missing`);
	});
} else {
	console.log('❌ Skipped - built file missing');
}

console.log('\n🎯 Test run complete.');
