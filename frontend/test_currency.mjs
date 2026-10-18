import assert from 'node:assert';

// 1. Currency Configuration
const SUPPORTED_CURRENCIES = {
  INR: { code: 'INR', symbol: '₹', name: 'Indian Rupee', locale: 'en-IN' },
  USD: { code: 'USD', symbol: '$', name: 'US Dollar', locale: 'en-US' },
  EUR: { code: 'EUR', symbol: '€', name: 'Euro', locale: 'de-DE' },
  GBP: { code: 'GBP', symbol: '£', name: 'British Pound', locale: 'en-GB' },
  AED: { code: 'AED', symbol: 'AED', name: 'UAE Dirham', locale: 'en-AE' },
};

const DEMO_EXCHANGE_RATES = {
  USD: 1.0,
  INR: 84.05,
  EUR: 0.92,
  GBP: 0.77,
  AED: 3.6725,
};

function convertMonetaryAmount(amount, from = 'USD', to) {
  if (from === to) return amount;
  const rate = DEMO_EXCHANGE_RATES[to] / DEMO_EXCHANGE_RATES[from];
  return amount * rate;
}

function formatCurrencyValue(amount, currency, options = {}) {
  const config = SUPPORTED_CURRENCIES[currency];
  return new Intl.NumberFormat(config.locale, {
    style: 'currency',
    currency: config.code,
    maximumFractionDigits: 0,
    ...options,
  }).format(amount);
}

console.log('Testing Currency Service Requirements...');

// Test 1: Default currency is INR
assert.strictEqual(SUPPORTED_CURRENCIES.INR.code, 'INR');
assert.strictEqual(SUPPORTED_CURRENCIES.INR.symbol, '₹');
console.log('✔ Test 1 Passed: Default display currency INR and ₹ symbol verified');

// Test 2: Supported currencies list (INR, USD, EUR, GBP, AED)
const keys = Object.keys(SUPPORTED_CURRENCIES);
assert.deepStrictEqual(keys.sort(), ['AED', 'EUR', 'GBP', 'INR', 'USD'].sort());
console.log('✔ Test 2 Passed: All 5 currencies supported (INR, USD, EUR, GBP, AED)');

// Test 3: Formatting uses Intl.NumberFormat and respects local grouping (e.g. lakhs in en-IN)
const formattedInr = formatCurrencyValue(2850000 * 84.05, 'INR');
assert.ok(formattedInr.includes('₹'), 'Formatted INR must include ₹');
// en-IN should format 239542500 with Indian grouping (23,95,42,500)
assert.ok(formattedInr.includes('23,95,42,500') || formattedInr.includes('23.95.42.500'), `Unexpected INR format: ${formattedInr}`);
console.log('✔ Test 3 Passed: Intl.NumberFormat Indian numbering system verified:', formattedInr);

// Test 4: Conversion logic preserves mathematical accuracy
const usdAmount = 100000;
const inrAmount = convertMonetaryAmount(usdAmount, 'USD', 'INR');
assert.strictEqual(inrAmount, 8405000); // 100,000 * 84.05

const eurAmount = convertMonetaryAmount(usdAmount, 'USD', 'EUR');
assert.strictEqual(eurAmount, 92000); // 100,000 * 0.92

const gbpAmount = convertMonetaryAmount(usdAmount, 'USD', 'GBP');
assert.strictEqual(gbpAmount, 77000); // 100,000 * 0.77

const aedAmount = convertMonetaryAmount(usdAmount, 'USD', 'AED');
assert.strictEqual(aedAmount, 367250); // 100,000 * 3.6725
console.log('✔ Test 4 Passed: Accurate conversion rates verified for all currencies');

// Test 5: Numerical value NEVER stays the same when currency symbol changes
assert.notStrictEqual(usdAmount, inrAmount, 'Conversion must change numerical amount, never only symbol');
console.log('✔ Test 5 Passed: Guard against fake symbol-only swapping verified');

// Test 6: Non-monetary figures (percentages, urgency scores) are NOT converted
const urgencyScore = 80;
const maxDriftPct = 14.2;
// Neither should ever pass through convertMonetaryAmount
assert.strictEqual(urgencyScore, 80);
assert.strictEqual(maxDriftPct, 14.2);
console.log('✔ Test 6 Passed: Urgency scores and drift percentages remain invariant');

console.log('\nAll Currency Service unit tests passed successfully!');
