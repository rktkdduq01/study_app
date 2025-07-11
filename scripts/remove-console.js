#!/usr/bin/env node
/**
 * Script to remove console statements from production builds
 */

const fs = require('fs');
const path = require('path');
const glob = require('glob');

const EXCLUDED_METHODS = ['warn', 'error'];
const FILE_PATTERNS = {
  frontend: 'frontend/src/**/*.{js,jsx,ts,tsx}',
  mobile: 'mobile/src/**/*.{js,jsx,ts,tsx}'
};

function removeConsoleStatements(content, filePath) {
  // Regular expression to match console statements
  const consoleRegex = /console\s*\.\s*(?!warn|error)(\w+)\s*\([^)]*\)\s*;?/g;
  
  let modifiedContent = content;
  let count = 0;
  
  // Replace console statements with empty string
  modifiedContent = content.replace(consoleRegex, (match) => {
    count++;
    return '/* console statement removed */';
  });
  
  if (count > 0) {
    console.log(`Removed ${count} console statements from ${filePath}`);
  }
  
  return modifiedContent;
}

function processFile(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    const modifiedContent = removeConsoleStatements(content, filePath);
    
    if (content !== modifiedContent) {
      fs.writeFileSync(filePath, modifiedContent, 'utf8');
    }
  } catch (error) {
    console.error(`Error processing file ${filePath}:`, error.message);
  }
}

function main() {
  const args = process.argv.slice(2);
  const target = args[0] || 'all';
  
  console.log('Removing console statements from production code...\n');
  
  let patterns = [];
  
  if (target === 'all') {
    patterns = Object.values(FILE_PATTERNS);
  } else if (FILE_PATTERNS[target]) {
    patterns = [FILE_PATTERNS[target]];
  } else {
    console.error(`Invalid target: ${target}. Use 'frontend', 'mobile', or 'all'`);
    process.exit(1);
  }
  
  patterns.forEach(pattern => {
    const files = glob.sync(pattern);
    console.log(`Processing ${files.length} files for pattern: ${pattern}`);
    
    files.forEach(processFile);
  });
  
  console.log('\nConsole statement removal complete!');
}

main();