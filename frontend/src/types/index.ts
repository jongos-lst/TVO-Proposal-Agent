export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export interface CustomerPersona {
  customer_name?: string;
  industry?: string;
  pain_points?: string[];
  use_scenarios?: string[];
  budget_amount?: number;
  service_warranty_needs?: string;
  current_devices?: string[];
  fleet_size?: number;
  deployment_timeline?: string;
}

export interface GetacProduct {
  id: string;
  name: string;
  category: string;
  base_price: number;
  display_size: string;
  processor: string;
  ram_options: string[];
  storage_options: string[];
  rugged_rating: string;
  operating_temp: string;
  battery_life: string;
  warranty_standard: string;
  warranty_options: string[];
  key_features: string[];
  target_industries: string[];
  annual_failure_rate: number;
}

export interface ProductivityFactor {
  name: string;
  description: string;
  formula: string;
  annual_value: number;
  total_value: number;
  applies: boolean;
  assumptions: string[];
}

export interface TCOLineItem {
  label: string;
  formula: string;
  getac_value: number;
  competitor_value: number;
  difference: number;
  notes: string;
}

export interface TVOCalculation {
  fleet_size: number;
  deployment_years: number;
  hourly_productivity_value: number;
  tco_line_items: TCOLineItem[];
  getac_total_tco: number;
  competitor_total_tco: number;
  tco_savings: number;
  tco_savings_percent: number;
  getac_annual_downtime_hours: number;
  competitor_annual_downtime_hours: number;
  productivity_savings_annual: number;
  productivity_savings_total: number;
  getac_expected_failures: number;
  competitor_expected_failures: number;
  risk_reduction_percent: number;
  roi_payback_months?: number;
  yearly_getac_cumulative?: number[];
  yearly_competitor_cumulative?: number[];
  productivity_breakdown?: ProductivityFactor[];
  total_value_advantage: number;
  assumptions: string[];
}

export interface ProductCalcParams {
  product_id: string;
  product_name: string;
  unit_price: number;
  warranty_years: number;
  failure_rate: number;
  competitor_name: string;
  competitor_price: number;
  competitor_warranty_years: number;
  competitor_failure_rate: number;
  // Feature flags for productivity factors
  has_hot_swap: boolean;
  display_nits: number;
  competitor_display_nits: number;
  ip_rating: number;
  competitor_ip_rating: number;
  has_wifi7: boolean;
  competitor_has_wifi7: boolean;
}

export interface CalculationParams {
  fleet_size: number;
  deployment_years: number;
  hourly_productivity_value: number;
  avg_downtime_hours_per_failure: number;
  annual_repair_cost: number;
  products: ProductCalcParams[];
}

export interface CompetitorProduct {
  name: string;
  category: string;
  base_price: number;
  warranty_standard: string;
  annual_failure_rate: number;
  weaknesses: string[];
}

export type Phase = 'intake' | 'recommendation' | 'calculation' | 'review' | 'generation' | 'complete';

export interface ProposalState {
  phase: Phase;
  persona?: CustomerPersona;
  // Multi-product support
  selectedProducts?: GetacProduct[];
  competitiveAdvantages?: Record<string, string[]>;      // product_id -> advantages
  competitorProductNames?: Record<string, string>;        // product_id -> competitor name
  tvoResults?: Record<string, TVOCalculation>;            // product_id -> TVO result
  proposalApproved: boolean;
  pptxPath?: string;
}

export interface SSEEvent {
  type: 'token' | 'state_update' | 'done' | 'error';
  content?: string;
  phase?: Phase;
  persona?: CustomerPersona;
  // Multi-product fields from backend
  selected_products?: GetacProduct[];
  tvo_results?: Record<string, TVOCalculation>;
  competitive_advantages?: Record<string, string[]>;
  competitor_product_names?: Record<string, string>;
  proposal_approved?: boolean;
  pptx_path?: string;
}
