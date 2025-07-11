#!/usr/bin/env node
/**
 * Test runner script for frontend tests
 */
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
const command = args[0];

// Color codes for output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m'
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function runCommand(cmd, description) {
  log(`\n${description}...`, 'blue');
  try {
    execSync(cmd, { stdio: 'inherit' });
    log(`✓ ${description} completed`, 'green');
    return true;
  } catch (error) {
    log(`✗ ${description} failed`, 'red');
    return false;
  }
}

function installDependencies() {
  log('Checking dependencies...', 'yellow');
  
  const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
  const requiredDeps = [
    '@testing-library/react',
    '@testing-library/jest-dom',
    '@testing-library/user-event',
    'jest',
    'ts-jest'
  ];
  
  const missingDeps = requiredDeps.filter(dep => 
    !packageJson.devDependencies?.[dep] && !packageJson.dependencies?.[dep]
  );
  
  if (missingDeps.length > 0) {
    log(`Installing missing dependencies: ${missingDeps.join(', ')}`, 'yellow');
    runCommand('npm install', 'Installing dependencies');
  }
}

function runTests() {
  log('Running Frontend Tests', 'bright');
  log('='.repeat(50), 'bright');
  
  switch (command) {
    case 'watch':
      runCommand('npm test -- --watch', 'Running tests in watch mode');
      break;
      
    case 'coverage':
      runCommand('npm test -- --coverage', 'Running tests with coverage');
      break;
      
    case 'unit':
      runCommand('npm test -- --testPathPattern="(services|utils|hooks|store).*\\.test\\.(ts|tsx)"', 'Running unit tests');
      break;
      
    case 'component':
      runCommand('npm test -- --testPathPattern="components.*\\.test\\.(ts|tsx)"', 'Running component tests');
      break;
      
    case 'update':
      runCommand('npm test -- -u', 'Updating snapshots');
      break;
      
    case 'debug':
      runCommand('node --inspect-brk node_modules/.bin/jest --runInBand', 'Running tests in debug mode');
      break;
      
    default:
      // Run all tests
      const results = {
        unit: runCommand('npm test -- --testPathPattern="(services|utils|hooks|store).*\\.test\\.(ts|tsx)" --passWithNoTests', 'Unit tests'),
        component: runCommand('npm test -- --testPathPattern="components.*\\.test\\.(ts|tsx)" --passWithNoTests', 'Component tests'),
        integration: runCommand('npm test -- --testPathPattern="integration.*\\.test\\.(ts|tsx)" --passWithNoTests', 'Integration tests')
      };
      
      // Summary
      log('\n' + '='.repeat(50), 'bright');
      log('Test Summary:', 'bright');
      log('='.repeat(50), 'bright');
      
      Object.entries(results).forEach(([type, passed]) => {
        const status = passed ? '✓ PASSED' : '✗ FAILED';
        const color = passed ? 'green' : 'red';
        log(`${type.padEnd(15)} ${status}`, color);
      });
      
      const allPassed = Object.values(results).every(r => r);
      if (allPassed) {
        log('\nAll tests passed! 🎉', 'green');
      } else {
        log('\nSome tests failed. Please check the output above.', 'red');
        process.exit(1);
      }
  }
}

function showHelp() {
  log('Frontend Test Runner', 'bright');
  log('Usage: node run_tests.js [command]', 'yellow');
  log('\nCommands:');
  log('  (no command)  - Run all tests');
  log('  watch        - Run tests in watch mode');
  log('  coverage     - Run tests with coverage report');
  log('  unit         - Run only unit tests');
  log('  component    - Run only component tests');
  log('  update       - Update test snapshots');
  log('  debug        - Run tests in debug mode');
  log('  help         - Show this help message');
}

// Main execution
if (command === 'help') {
  showHelp();
} else {
  installDependencies();
  runTests();
}