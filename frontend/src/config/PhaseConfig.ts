import type { Phase } from '../types';

export interface PhaseMetadata {
    key: Phase;
    label: string;
    description: string;
    icon: string;
    accentClass: string;
    bgAccentClass: string;
    placeholder: string;
    chips: string[];
}

export const PHASE_CONFIG: Record<Phase, PhaseMetadata> = {
    intake: {
        key: 'intake',
        label: 'Customer Intake',
        description: 'Collecting initial customer details and requirements.',
        icon: '📝',
        accentClass: 'text-phase-intake',
        bgAccentClass: 'bg-phase-intake',
        placeholder: 'Tell me about the customer, e.g. "Acme Corp in field service..."',
        chips: [],
    },
    recommendation: {
        key: 'recommendation',
        label: 'Product Recommendation',
        description: 'Select the optimal Getac device based on customer needs.',
        icon: '🎯',
        accentClass: 'text-phase-recommendation',
        bgAccentClass: 'bg-phase-recommendation',
        placeholder: 'e.g. "Recommend the F110 for this customer"',
        chips: ['Show product catalog', 'Compare with competitor', 'Suggest best match'],
    },
    calculation: {
        key: 'calculation',
        label: 'TVO Calculation',
        description: 'Calculate Total Value of Ownership and ROI metrics.',
        icon: '📊',
        accentClass: 'text-phase-calculation',
        bgAccentClass: 'bg-phase-calculation',
        placeholder: 'e.g. "Calculate TVO assuming 1 hour less downtime per incident"',
        chips: ['Calculate TVO', 'Show assumptions', 'Breakdown savings'],
    },
    review: {
        key: 'review',
        label: 'Proposal Review',
        description: 'Review the collected information before generating the proposal.',
        icon: '📋',
        accentClass: 'text-phase-review',
        bgAccentClass: 'bg-phase-review',
        placeholder: 'e.g. "The proposal looks good, approve it" or "Update the fleet size to 250"',
        chips: ['Approve proposal', 'Review all details', 'Modify product choice'],
    },
    generation: {
        key: 'generation',
        label: 'Export Deck',
        description: 'Generate the final PowerPoint presentation.',
        icon: '📄',
        accentClass: 'text-phase-generation',
        bgAccentClass: 'bg-phase-generation',
        placeholder: 'e.g. "Generate the deck"',
        chips: ['Generate PowerPoint', 'Include competitor slide'],
    },
    complete: {
        key: 'complete',
        label: 'Proposal Complete',
        description: 'Your TVO proposal is ready for download.',
        icon: '✅',
        accentClass: 'text-phase-complete',
        bgAccentClass: 'bg-phase-complete',
        placeholder: 'Type "restart" to begin a new proposal',
        chips: [],
    },
};
