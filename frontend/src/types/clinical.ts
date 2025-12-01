// Action item categories
export type ActionItemCategory = 'prescription' | 'follow_up' | 'referral' | 'test' | 'other';

// Action item priority
export type ActionItemPriority = 'high' | 'medium' | 'low';

// Numerical value categories
export type NumericalCategory = 'vital' | 'lab' | 'measurement' | 'dosage';

// Action item extracted from transcription
export interface ActionItem {
  text: string;
  category: ActionItemCategory;
  priority: ActionItemPriority;
  timestamp_ms: number;
  related_segment_index: number;
  keywords: string[];
}

// Numerical value extracted from transcription
export interface NumericalValue {
  value: string;
  unit?: string;
  category: NumericalCategory;
  label: string;
  timestamp_ms: number;
  related_segment_index: number;
  raw_text: string;
}

// Complete clinical data extraction
export interface ClinicalData {
  action_items: ActionItem[];
  numerical_values: NumericalValue[];
  important_phrases: string[];
  medical_terms: string[];
}

// Category display info
export const CATEGORY_INFO: Record<ActionItemCategory, { label: string; icon: string; color: string }> = {
  prescription: { label: 'Prescription', icon: '💊', color: 'bg-blue-100 text-blue-800' },
  follow_up: { label: 'Follow-up', icon: '📅', color: 'bg-green-100 text-green-800' },
  referral: { label: 'Referral', icon: '🏥', color: 'bg-purple-100 text-purple-800' },
  test: { label: 'Test', icon: '🔬', color: 'bg-orange-100 text-orange-800' },
  other: { label: 'Other', icon: '📋', color: 'bg-gray-100 text-gray-800' },
};

// Priority display info
export const PRIORITY_INFO: Record<ActionItemPriority, { label: string; color: string }> = {
  high: { label: 'High', color: 'bg-red-100 text-red-800' },
  medium: { label: 'Medium', color: 'bg-yellow-100 text-yellow-800' },
  low: { label: 'Low', color: 'bg-gray-100 text-gray-600' },
};

