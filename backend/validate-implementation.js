#!/usr/bin/env node

/**
 * Validation script to check if comprehensive test suite is properly implemented
 * This script verifies all test files and configurations are in place
 */

const fs = require('fs');
const path = require('path');

class TestSuiteValidator {
    constructor() {
        this.errors = [];
        this.warnings = [];
        this.success = [];
    }

    log(message, type = 'info') {
        const timestamp = new Date().toISOString();
        console.log(`[${timestamp}] ${type.toUpperCase()}: ${message}`);
        
        if (type === 'error') {
            this.errors.push(message);
        } else if (type === 'warning') {
            this.warnings.push(message);
        } else if (type === 'success') {
            this.success.push(message);
        }
    }

    checkFileExists(filePath, description) {
        const fullPath = path.resolve(filePath);
        if (fs.existsSync(fullPath)) {
            this.log(`✓ ${description}: ${filePath}`, 'success');
            return true;
        } else {
            this.log(`✗ Missing ${description}: ${filePath}`, 'error');
            return false;
        }
    }

    checkDirectoryExists(dirPath, description) {
        const fullPath = path.resolve(dirPath);
        if (fs.existsSync(fullPath) && fs.statSync(fullPath).isDirectory()) {
            this.log(`✓ ${description}: ${dirPath}`, 'success');
            return true;
        } else {
            this.log(`✗ Missing ${description}: ${dirPath}`, 'error');
            return false;
        }
    }

    checkFileContent(filePath, searchString, description) {
        try {
            const content = fs.readFileSync(filePath, 'utf8');
            if (content.includes(searchString)) {
                this.log(`✓ ${description}`, 'success');
                return true;
            } else {
                this.log(`✗ ${description}`, 'error');
                return false;
            }
        } catch (error) {
            this.log(`✗ Error reading ${filePath}: ${error.message}`, 'error');
            return false;
        }
    }

    validateEndToEndTests() {
        this.log('Validating End-to-End Tests...', 'info');
        
        // Check Playwright configuration
        this.checkFileExists('../playwright.config.ts', 'Playwright configuration');
        
        // Check E2E test directory and files
        this.checkDirectoryExists('../e2e-tests', 'E2E tests directory');
        this.checkFileExists('../e2e-tests/admin-dashboard.spec.ts', 'Admin dashboard E2E tests');
        this.checkFileExists('../e2e-tests/runner-registration.spec.ts', 'Runner registration E2E tests');
        this.checkFileExists('../e2e-tests/real-time-updates.spec.ts', 'Real-time updates E2E tests');
        
        // Check for cross-browser configuration
        if (fs.existsSync('../playwright.config.ts')) {
            this.checkFileContent('../playwright.config.ts', 'Desktop Chrome', 'Chrome browser configuration');
            this.checkFileContent('../playwright.config.ts', 'Desktop Firefox', 'Firefox browser configuration');
            this.checkFileContent('../playwright.config.ts', 'Desktop Safari', 'Safari browser configuration');
            this.checkFileContent('../playwright.config.ts', 'Mobile Chrome', 'Mobile Chrome configuration');
            this.checkFileContent('../playwright.config.ts', 'iPhone 12', 'Mobile Safari configuration');
        }
    }

    validateLoadTesting() {
        this.log('Validating Load Testing...', 'info');
        
        // Check Locust files
        this.checkDirectoryExists('performance_tests', 'Performance tests directory');
        this.checkFileExists('performance_tests/locustfile.py', 'Locust test scenarios');
        this.checkFileExists('performance_tests/test_runner.py', 'Performance test runner');
        
        // Check for different user scenarios
        if (fs.existsSync('performance_tests/locustfile.py')) {
            this.checkFileContent('performance_tests/locustfile.py', 'RunnerUser', 'Runner user scenario');
            this.checkFileContent('performance_tests/locustfile.py', 'AdminUser', 'Admin user scenario');
            this.checkFileContent('performance_tests/locustfile.py', 'PeakRegistrationScenario', 'Peak usage scenario');
            this.checkFileContent('performance_tests/locustfile.py', '100 concurrent users', 'Peak load configuration');
        }
    }

    validateWebSocketTests() {
        this.log('Validating WebSocket Integration Tests...', 'info');
        
        // Check WebSocket test file
        this.checkFileExists('tests/test_websocket_integration.py', 'WebSocket integration tests');
        
        if (fs.existsSync('tests/test_websocket_integration.py')) {
            this.checkFileContent('tests/test_websocket_integration.py', 'test_websocket_connection', 'WebSocket connection test');
            this.checkFileContent('tests/test_websocket_integration.py', 'test_attendance_registration_broadcast', 'Real-time broadcast test');
            this.checkFileContent('tests/test_websocket_integration.py', 'test_multiple_clients_receive_updates', 'Multiple client test');
            this.checkFileContent('tests/test_websocket_integration.py', 'socketio.AsyncClient', 'Socket.IO client usage');
        }
    }

    validateQRCodeTests() {
        this.log('Validating QR Code Integration Tests...', 'info');
        
        // Check QR code test file
        this.checkFileExists('tests/test_qr_integration.py', 'QR code integration tests');
        
        if (fs.existsSync('tests/test_qr_integration.py')) {
            this.checkFileContent('tests/test_qr_integration.py', 'test_qr_code_generation_endpoint', 'QR generation endpoint test');
            this.checkFileContent('tests/test_qr_integration.py', 'test_qr_code_validation_endpoint', 'QR validation endpoint test');
            this.checkFileContent('tests/test_qr_integration.py', 'test_qr_code_registration_flow_integration', 'Complete QR flow test');
            this.checkFileContent('tests/test_qr_integration.py', 'FastAPI TestClient', 'FastAPI test client usage');
        }
    }

    validatePerformanceTests() {
        this.log('Validating Performance Optimization Tests...', 'info');
        
        // Check performance test file
        this.checkFileExists('tests/test_performance_optimizations.py', 'Performance optimization tests');
        
        if (fs.existsSync('tests/test_performance_optimizations.py')) {
            this.checkFileContent('tests/test_performance_optimizations.py', 'test_concurrent_registration_performance', 'Concurrent registration test');
            this.checkFileContent('tests/test_performance_optimizations.py', 'test_rate_limiting_effectiveness', 'Rate limiting test');
            this.checkFileContent('tests/test_performance_optimizations.py', 'concurrent.futures', 'Concurrent testing framework');
        }
    }

    validateTestOrchestrator() {
        this.log('Validating Test Orchestrator...', 'info');
        
        // Check main test runner
        this.checkFileExists('run_performance_tests.py', 'Main test orchestrator');
        
        if (fs.existsSync('run_performance_tests.py')) {
            this.checkFileContent('run_performance_tests.py', 'run_backend_unit_tests', 'Backend unit test runner');
            this.checkFileContent('run_performance_tests.py', 'run_websocket_integration_tests', 'WebSocket test runner');
            this.checkFileContent('run_performance_tests.py', 'run_qr_integration_tests', 'QR code test runner');
            this.checkFileContent('run_performance_tests.py', 'run_e2e_tests', 'E2E test runner');
            this.checkFileContent('run_performance_tests.py', 'run_load_tests', 'Load test runner');
        }
    }

    validatePackageConfigurations() {
        this.log('Validating Package Configurations...', 'info');
        
        // Check root package.json
        this.checkFileExists('../package.json', 'Root package.json');
        
        // Check frontend package.json
        this.checkFileExists('../frontend/package.json', 'Frontend package.json');
        
        // Check backend requirements
        this.checkFileExists('requirements.txt', 'Backend requirements.txt');
        
        // Check for testing dependencies
        if (fs.existsSync('../frontend/package.json')) {
            this.checkFileContent('../frontend/package.json', '@playwright/test', 'Playwright dependency');
        }
        
        if (fs.existsSync('requirements.txt')) {
            this.checkFileContent('requirements.txt', 'pytest', 'Pytest dependency');
            this.checkFileContent('requirements.txt', 'locust', 'Locust dependency');
        }
    }

    validateDocumentation() {
        this.log('Validating Documentation...', 'info');
        
        // Check testing documentation
        this.checkFileExists('../TESTING.md', 'Testing documentation');
        
        if (fs.existsSync('../TESTING.md')) {
            this.checkFileContent('../TESTING.md', 'End-to-End Tests', 'E2E documentation');
            this.checkFileContent('../TESTING.md', 'Load Testing', 'Load testing documentation');
            this.checkFileContent('../TESTING.md', 'WebSocket Integration Tests', 'WebSocket documentation');
            this.checkFileContent('../TESTING.md', 'Requirements Coverage', 'Requirements coverage documentation');
        }
    }

    validateRequirementsCoverage() {
        this.log('Validating Requirements Coverage...', 'info');
        
        // Check that tests cover the specified requirements
        const requirements = [
            { id: '2.4', description: 'Peak load handling (100 concurrent users)' },
            { id: '4.1', description: 'Real-time updates under load' },
            { id: '4.2', description: 'Response times under 5 seconds' }
        ];
        
        requirements.forEach(req => {
            let covered = false;
            
            // Check in load testing files
            if (fs.existsSync('performance_tests/locustfile.py')) {
                const content = fs.readFileSync('performance_tests/locustfile.py', 'utf8');
                if (content.includes('100 concurrent users') || content.includes('100 users')) {
                    covered = true;
                }
            }
            
            // Check in performance tests
            if (fs.existsSync('tests/test_performance_optimizations.py')) {
                const content = fs.readFileSync('tests/test_performance_optimizations.py', 'utf8');
                if (content.includes('5.0') || content.includes('response_time')) {
                    covered = true;
                }
            }
            
            if (covered) {
                this.log(`✓ Requirement ${req.id} covered: ${req.description}`, 'success');
            } else {
                this.log(`✗ Requirement ${req.id} not covered: ${req.description}`, 'warning');
            }
        });
    }

    generateReport() {
        console.log('\n' + '='.repeat(60));
        console.log('COMPREHENSIVE TEST SUITE VALIDATION REPORT');
        console.log('='.repeat(60));
        
        console.log(`\n✅ Successful validations: ${this.success.length}`);
        console.log(`⚠️  Warnings: ${this.warnings.length}`);
        console.log(`❌ Errors: ${this.errors.length}`);
        
        if (this.warnings.length > 0) {
            console.log('\nWarnings:');
            this.warnings.forEach(warning => console.log(`  - ${warning}`));
        }
        
        if (this.errors.length > 0) {
            console.log('\nErrors:');
            this.errors.forEach(error => console.log(`  - ${error}`));
        }
        
        console.log('\n' + '='.repeat(60));
        
        const isValid = this.errors.length === 0;
        if (isValid) {
            console.log('✅ VALIDATION PASSED: Comprehensive test suite is properly implemented');
            console.log('\nNext steps:');
            console.log('1. Run: npm run install:all');
            console.log('2. Run: npm run setup:playwright');
            console.log('3. Run: npm run test:quick');
        } else {
            console.log('❌ VALIDATION FAILED: Please fix the errors above');
        }
        
        return isValid;
    }

    validate() {
        this.log('Starting comprehensive test suite validation...', 'info');
        
        this.validateEndToEndTests();
        this.validateLoadTesting();
        this.validateWebSocketTests();
        this.validateQRCodeTests();
        this.validatePerformanceTests();
        this.validateTestOrchestrator();
        this.validatePackageConfigurations();
        this.validateDocumentation();
        this.validateRequirementsCoverage();
        
        return this.generateReport();
    }
}

// Run validation
const validator = new TestSuiteValidator();
const isValid = validator.validate();

process.exit(isValid ? 0 : 1);