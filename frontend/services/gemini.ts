import { GoogleGenAI } from "@google/genai";

// Get API key from environment (Vite uses import.meta.env)
// Exported for components that need direct access
export const getApiKey = () => {
  // Check multiple possible env variable names
  return import.meta.env.VITE_GEMINI_API_KEY || 
         import.meta.env.GEMINI_API_KEY || 
         import.meta.env.API_KEY || 
         '';
};

// Latest Gemini models (as of 2025)
// Updated to use the most recent stable models
export const GEMINI_MODELS = {
  TEXT: 'gemini-2.5-flash-lite', // Latest stable for text (1M token context)
  VOICE: 'gemini-2.5-flash-native-audio-preview-09-2025', // Latest native audio for real-time voice (Gemini 2.5)
  // Note: Gemini 3 voice models may be available - check Google AI Studio for latest
  PRO: 'gemini-2.0-flash-exp', // Pro model for complex tasks
} as const;

// Initialize client lazily to avoid issues if key is missing initially
export const createGeminiClient = () => {
  const apiKey = getApiKey();
  if (!apiKey) {
    console.warn('Gemini API key not found. Please set GEMINI_API_KEY in .env.local');
  }
  return new GoogleGenAI({ apiKey });
};

export const MOCK_LOAN_DOC_CONTENT = `LOAN AGREEMENT

This Loan Agreement ("Agreement") is made and entered into on October 24, 2023, by and between:
LENDER: Global Finance Corp, located at 123 Wall St, NY.
BORROWER: John Doe, located at 456 Elm St, CA.

1. PRINCIPAL AMOUNT: $50,000.00 USD.
2. INTEREST RATE: 5.5% fixed per annum.
3. REPAYMENT TERM: 60 months.
4. COLLATERAL: 2022 Tesla Model 3 (VIN: 5YJ3E1EA1LF...).
5. DEFAULT: Failure to pay within 15 days of due date constitutes default.

IN WITNESS WHEREOF, the parties have executed this Agreement.
`;
