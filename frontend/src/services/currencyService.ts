import { CurrencyCode, CurrencyConfig, ExchangeRateInfo } from '../contracts/types';

export const SUPPORTED_CURRENCIES: Record<CurrencyCode, CurrencyConfig> = {
  INR: {
    code: 'INR',
    symbol: '₹',
    name: 'Indian Rupee',
    locale: 'en-IN',
    flag: '🇮🇳',
  },
  USD: {
    code: 'USD',
    symbol: '$',
    name: 'US Dollar',
    locale: 'en-US',
    flag: '🇺🇸',
  },
  EUR: {
    code: 'EUR',
    symbol: '€',
    name: 'Euro',
    locale: 'de-DE',
    flag: '🇪🇺',
  },
  GBP: {
    code: 'GBP',
    symbol: '£',
    name: 'British Pound',
    locale: 'en-GB',
    flag: '🇬🇧',
  },
  AED: {
    code: 'AED',
    symbol: 'AED',
    name: 'UAE Dirham',
    locale: 'en-AE',
    flag: '🇦🇪',
  },
};

export const DEFAULT_DISPLAY_CURRENCY: CurrencyCode = 'INR';
export const DEFAULT_SOURCE_CURRENCY: CurrencyCode = 'USD';
export const CURRENCY_STORAGE_KEY = 'advantaiq_display_currency';

// Institutional demo benchmark exchange rates (Base: USD = 1.0)
// Rates as of Reference Date: 2026-10-18T00:00:00Z
export const DEMO_EXCHANGE_RATES: Record<CurrencyCode, number> = {
  USD: 1.0,
  INR: 84.05,
  EUR: 0.92,
  GBP: 0.77,
  AED: 3.6725,
};

export const RATE_METADATA = {
  timestamp: '2026-10-18T00:00:00Z',
  provider: 'Institutional Demo Benchmark FX',
  isDemoRate: true,
  disclaimer:
    'Display currency conversion is provided for advisor reference only using benchmark rates. Underlying client assets remain held in their native custodian currencies.',
};

/**
 * Returns the exchange rate metadata between two currencies.
 */
export function getExchangeRate(
  from: CurrencyCode = DEFAULT_SOURCE_CURRENCY,
  to: CurrencyCode
): ExchangeRateInfo {
  const fromRate = DEMO_EXCHANGE_RATES[from] || 1.0;
  const toRate = DEMO_EXCHANGE_RATES[to] || 1.0;
  const effectiveRate = toRate / fromRate;

  return {
    sourceCurrency: from,
    targetCurrency: to,
    rate: effectiveRate,
    timestamp: RATE_METADATA.timestamp,
    provider: RATE_METADATA.provider,
    isDemoRate: RATE_METADATA.isDemoRate,
    disclaimer: RATE_METADATA.disclaimer,
  };
}

/**
 * Converts a monetary amount from source currency to target currency.
 */
export function convertMonetaryAmount(
  amount: number,
  from: CurrencyCode = DEFAULT_SOURCE_CURRENCY,
  to: CurrencyCode
): number {
  if (from === to) return amount;
  const rateInfo = getExchangeRate(from, to);
  return amount * rateInfo.rate;
}

/**
 * Centralized currency formatting using JavaScript Intl.NumberFormat.
 * Respects internationalized locales (e.g. en-IN uses lakhs/crores formatting).
 */
export function formatCurrencyValue(
  amount: number,
  currency: CurrencyCode,
  options?: Intl.NumberFormatOptions
): string {
  const config = SUPPORTED_CURRENCIES[currency] || SUPPORTED_CURRENCIES.INR;
  const formatter = new Intl.NumberFormat(config.locale, {
    style: 'currency',
    currency: config.code,
    maximumFractionDigits: 0,
    ...options,
  });
  return formatter.format(amount);
}

/**
 * Converts and formats a monetary amount, returning both the display string
 * and explicit source currency attribution to prevent misleading advisors.
 */
export function formatConvertedCurrency(
  amount: number,
  sourceCurrency: CurrencyCode = DEFAULT_SOURCE_CURRENCY,
  displayCurrency: CurrencyCode,
  options?: Intl.NumberFormatOptions
): {
  displayString: string;
  convertedAmount: number;
  originalString: string;
  isConverted: boolean;
  rateInfo: ExchangeRateInfo;
} {
  const rateInfo = getExchangeRate(sourceCurrency, displayCurrency);
  const convertedAmount = convertMonetaryAmount(amount, sourceCurrency, displayCurrency);
  const displayString = formatCurrencyValue(convertedAmount, displayCurrency, options);
  const originalString = formatCurrencyValue(amount, sourceCurrency, options);

  return {
    displayString,
    convertedAmount,
    originalString,
    isConverted: sourceCurrency !== displayCurrency,
    rateInfo,
  };
}

/**
 * Retrieve persisted user currency preference from localStorage.
 * Defaults to INR if not set or invalid.
 */
export function getStoredCurrencyPreference(): CurrencyCode {
  try {
    const stored = localStorage.getItem(CURRENCY_STORAGE_KEY) as CurrencyCode;
    if (stored && SUPPORTED_CURRENCIES[stored]) {
      return stored;
    }
  } catch {
    // localStorage may be unavailable in some restricted environments
  }
  return DEFAULT_DISPLAY_CURRENCY;
}

/**
 * Persist user currency preference into localStorage.
 */
export function setStoredCurrencyPreference(currency: CurrencyCode): void {
  try {
    localStorage.setItem(CURRENCY_STORAGE_KEY, currency);
  } catch {
    // localStorage may be unavailable
  }
}
