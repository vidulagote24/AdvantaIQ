import React, { createContext, useContext, useState, useMemo, useCallback } from 'react';
import { CurrencyCode, CurrencyConfig, ExchangeRateInfo } from '../contracts/types';
import {
  SUPPORTED_CURRENCIES,
  DEFAULT_SOURCE_CURRENCY,
  getStoredCurrencyPreference,
  setStoredCurrencyPreference,
  formatConvertedCurrency,
  formatCurrencyValue,
  convertMonetaryAmount,
  getExchangeRate,
} from '../services/currencyService';

interface CurrencyContextValue {
  displayCurrency: CurrencyCode;
  setDisplayCurrency: (currency: CurrencyCode) => void;
  currencies: CurrencyConfig[];
  activeConfig: CurrencyConfig;
  formatMoney: (
    amount: number,
    sourceCurrency?: CurrencyCode,
    options?: Intl.NumberFormatOptions
  ) => {
    displayString: string;
    convertedAmount: number;
    originalString: string;
    isConverted: boolean;
    rateInfo: ExchangeRateInfo;
  };
  formatDirect: (
    amount: number,
    currency?: CurrencyCode,
    options?: Intl.NumberFormatOptions
  ) => string;
  convert: (amount: number, from?: CurrencyCode, to?: CurrencyCode) => number;
  rateInfo: ExchangeRateInfo;
}

const CurrencyContext = createContext<CurrencyContextValue | null>(null);

export const CurrencyProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [displayCurrency, setDisplayCurrencyState] = useState<CurrencyCode>(() =>
    getStoredCurrencyPreference()
  );

  const setDisplayCurrency = useCallback((currency: CurrencyCode) => {
    if (SUPPORTED_CURRENCIES[currency]) {
      setDisplayCurrencyState(currency);
      setStoredCurrencyPreference(currency);
    }
  }, []);

  const activeConfig = useMemo(
    () => SUPPORTED_CURRENCIES[displayCurrency] || SUPPORTED_CURRENCIES.INR,
    [displayCurrency]
  );

  const rateInfo = useMemo(
    () => getExchangeRate(DEFAULT_SOURCE_CURRENCY, displayCurrency),
    [displayCurrency]
  );

  const formatMoney = useCallback(
    (
      amount: number,
      sourceCurrency: CurrencyCode = DEFAULT_SOURCE_CURRENCY,
      options?: Intl.NumberFormatOptions
    ) => {
      return formatConvertedCurrency(amount, sourceCurrency, displayCurrency, options);
    },
    [displayCurrency]
  );

  const formatDirect = useCallback(
    (
      amount: number,
      currency: CurrencyCode = displayCurrency,
      options?: Intl.NumberFormatOptions
    ) => {
      return formatCurrencyValue(amount, currency, options);
    },
    [displayCurrency]
  );

  const convert = useCallback(
    (
      amount: number,
      from: CurrencyCode = DEFAULT_SOURCE_CURRENCY,
      to: CurrencyCode = displayCurrency
    ) => {
      return convertMonetaryAmount(amount, from, to);
    },
    [displayCurrency]
  );

  const value = useMemo(
    () => ({
      displayCurrency,
      setDisplayCurrency,
      currencies: Object.values(SUPPORTED_CURRENCIES),
      activeConfig,
      formatMoney,
      formatDirect,
      convert,
      rateInfo,
    }),
    [displayCurrency, setDisplayCurrency, activeConfig, formatMoney, formatDirect, convert, rateInfo]
  );

  return <CurrencyContext.Provider value={value}>{children}</CurrencyContext.Provider>;
};

export const useCurrency = (): CurrencyContextValue => {
  const ctx = useContext(CurrencyContext);
  if (!ctx) {
    throw new Error('useCurrency must be used within a CurrencyProvider');
  }
  return ctx;
};
