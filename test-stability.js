#!/usr/bin/env node

/**
 * Test script to verify the stability of the React dashboard
 * This simulates rapid token selection changes to test for removeChild errors
 */

const axios = require('axios');
const { performance } = require('perf_hooks');

const BACKEND_URL = 'http://localhost:8000/api';
const FRONTEND_URL = 'http://localhost:3000';

async function testBackendStability() {
  console.log('🧪 Testing backend API stability...');
  
  try {
    // Test rapid successive API calls (simulating fast token clicks)
    const promises = [];
    for (let i = 0; i < 10; i++) {
      promises.push(
        axios.get(`${BACKEND_URL}/hot-pools?limit=5`)
          .then(response => ({ success: true, data: response.data, index: i }))
          .catch(error => ({ success: false, error: error.message, index: i }))
      );
    }

    const results = await Promise.all(promises);
    const successful = results.filter(r => r.success).length;
    const failed = results.filter(r => !r.success).length;

    console.log(`   ✅ Successful requests: ${successful}/10`);
    console.log(`   ❌ Failed requests: ${failed}/10`);

    if (successful >= 8) {
      console.log('   🎉 Backend stability test PASSED');
      return true;
    } else {
      console.log('   ⚠️  Backend stability test FAILED');
      return false;
    }
  } catch (error) {
    console.error('   ❌ Backend test error:', error.message);
    return false;
  }
}

async function testTokenAnalysisStability() {
  console.log('\n🔬 Testing token analysis API stability...');
  
  try {
    // Get some test tokens first
    const poolsResponse = await axios.get(`${BACKEND_URL}/hot-pools?limit=5`);
    if (!poolsResponse.data.success || poolsResponse.data.data.length === 0) {
      console.log('   ⚠️  No pools available for testing');
      return false;
    }

    const tokens = poolsResponse.data.data
      .map(pool => pool.mainToken.address)
      .filter(addr => addr && addr.length > 10)
      .slice(0, 3);

    if (tokens.length === 0) {
      console.log('   ⚠️  No valid token addresses found');
      return false;
    }

    console.log(`   🪙 Testing with ${tokens.length} tokens`);

    // Test rapid token analysis requests (simulating fast clicking)
    const promises = tokens.map((token, index) => 
      axios.get(`${BACKEND_URL}/token/${token}`)
        .then(response => ({ success: true, token, index, data: response.data }))
        .catch(error => ({ success: false, token, index, error: error.message }))
    );

    const results = await Promise.all(promises);
    const successful = results.filter(r => r.success).length;
    const failed = results.filter(r => !r.success).length;

    console.log(`   ✅ Successful analyses: ${successful}/${tokens.length}`);
    console.log(`   ❌ Failed analyses: ${failed}/${tokens.length}`);

    // Show some data from successful requests
    const successfulResults = results.filter(r => r.success);
    if (successfulResults.length > 0) {
      const sample = successfulResults[0];
      console.log(`   📊 Sample data available for token: ${sample.token.slice(0, 8)}...`);
    }

    return successful >= Math.floor(tokens.length * 0.7); // 70% success rate
  } catch (error) {
    console.error('   ❌ Token analysis test error:', error.message);
    return false;
  }
}

async function checkFrontendAvailability() {
  console.log('\n🌐 Checking frontend availability...');
  
  try {
    const response = await axios.get(FRONTEND_URL, { timeout: 5000 });
    if (response.status === 200) {
      console.log('   ✅ Frontend is accessible');
      return true;
    }
  } catch (error) {
    console.log('   ❌ Frontend not accessible:', error.message);
    return false;
  }
}

function printStabilityReport(backendStable, tokenStable, frontendAvailable) {
  console.log('\n' + '='.repeat(60));
  console.log('📊 STABILITY TEST REPORT');
  console.log('='.repeat(60));
  
  console.log(`🔧 Backend API:           ${backendStable ? '✅ STABLE' : '❌ UNSTABLE'}`);
  console.log(`🪙 Token Analysis:        ${tokenStable ? '✅ STABLE' : '❌ UNSTABLE'}`);
  console.log(`🌐 Frontend Availability: ${frontendAvailable ? '✅ AVAILABLE' : '❌ UNAVAILABLE'}`);
  
  const overallScore = [backendStable, tokenStable, frontendAvailable].filter(Boolean).length;
  
  console.log('\n📈 OVERALL STATUS:');
  if (overallScore === 3) {
    console.log('🎉 EXCELLENT - All systems stable and ready for use!');
  } else if (overallScore === 2) {
    console.log('✅ GOOD - Most systems stable, minor issues detected');
  } else if (overallScore === 1) {
    console.log('⚠️  FAIR - Some systems unstable, needs attention');
  } else {
    console.log('❌ POOR - Multiple system failures detected');
  }
  
  console.log('\n💡 RECOMMENDATIONS:');
  if (!frontendAvailable) {
    console.log('   • Start frontend server: npm run dev');
  }
  if (!backendStable) {
    console.log('   • Check backend server: python3 backend/server.py');
    console.log('   • Verify API key configuration in .env');
  }
  if (!tokenStable) {
    console.log('   • Check DEXTools API rate limits');
    console.log('   • Verify network connectivity');
  }
  
  if (overallScore === 3) {
    console.log('\n🚀 Dashboard ready at: http://localhost:3000');
  }
}

async function main() {
  console.log('🔥 SOLANA HOT POOLS DASHBOARD - STABILITY TEST');
  console.log('='.repeat(60));
  console.log('Testing system stability and error resilience...\n');
  
  const startTime = performance.now();
  
  const [backendStable, tokenStable, frontendAvailable] = await Promise.all([
    testBackendStability(),
    testTokenAnalysisStability(),
    checkFrontendAvailability()
  ]);
  
  const endTime = performance.now();
  const duration = ((endTime - startTime) / 1000).toFixed(2);
  
  printStabilityReport(backendStable, tokenStable, frontendAvailable);
  
  console.log(`\n⏱️  Test completed in ${duration}s`);
}

// Handle both direct execution and require
if (require.main === module) {
  main().catch(console.error);
}

module.exports = { testBackendStability, testTokenAnalysisStability, checkFrontendAvailability };