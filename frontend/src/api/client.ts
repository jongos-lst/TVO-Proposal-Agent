import type { SSEEvent, CalculationParams, CompetitorProduct } from '../types';

const API_BASE = import.meta.env.VITE_API_URL || '';

export async function sendMessageStream(
  sessionId: string,
  message: string,
  onToken: (token: string) => void,
  onStateUpdate: (update: SSEEvent) => void,
  onDone: () => void,
  onError: (error: string) => void
): Promise<void> {
  const response = await fetch(`${API_BASE}/api/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message }),
  });

  if (!response.ok) {
    onError(`HTTP ${response.status}: ${response.statusText}`);
    return;
  }

  const reader = response.body?.getReader();
  if (!reader) {
    onError('No response body');
    return;
  }

  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const event: SSEEvent = JSON.parse(line.slice(6));
          switch (event.type) {
            case 'token':
              onToken(event.content || '');
              break;
            case 'state_update':
              onStateUpdate(event);
              break;
            case 'done':
              onDone();
              break;
            case 'error':
              onError(event.content || 'Unknown error');
              break;
          }
        } catch {
          // Skip malformed events
        }
      }
    }
  }
}

export async function sendMessage(sessionId: string, message: string) {
  const response = await fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message }),
  });
  return response.json();
}

export async function submitIntake(sessionId: string, persona: Record<string, unknown>) {
  const response = await fetch(`${API_BASE}/api/intake`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, ...persona }),
  });
  return response.json();
}

export function getExportUrl(sessionId: string): string {
  return `${API_BASE}/api/proposals/${sessionId}/export/pptx`;
}

export function getChartUrl(sessionId: string, productId: string, chartName: string): string {
  return `${API_BASE}/api/charts/${sessionId}/${productId}/${chartName}`;
}

export async function submitConfirmedCalculation(
  sessionId: string,
  params: CalculationParams
) {
  const response = await fetch(`${API_BASE}/api/calculate-confirmed`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, ...params }),
  });
  return response.json();
}

export async function fetchCompetitors(): Promise<CompetitorProduct[]> {
  const response = await fetch(`${API_BASE}/api/competitors`);
  return response.json();
}

export async function overridePhase(sessionId: string, targetPhase: string, proposalApproved?: boolean) {
  const payload: Record<string, unknown> = { session_id: sessionId, target_phase: targetPhase };
  if (proposalApproved !== undefined) {
    payload.proposal_approved = proposalApproved;
  }
  const response = await fetch(`${API_BASE}/api/chat/override-phase`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return response.json();
}
