import { WorklistResponse, HealthResponse } from '../contracts/types';
import mockData from '../mocks/worklist.json';

// Configure data source mode: defaults to checking Vite env
export const DEFAULT_USE_MOCKS = import.meta.env.VITE_USE_MOCKS === 'true';

export async function fetchWorklist(
  urgency: string = 'all',
  useMocks: boolean = DEFAULT_USE_MOCKS
): Promise<{ data: WorklistResponse; source: 'live' | 'mock' }> {
  if (useMocks) {
    // Simulate slight network latency for realistic UX feel
    await new Promise((r) => setTimeout(r, 200));
    
    let items = (mockData as WorklistResponse).items;
    if (urgency !== 'all') {
      items = items.filter((i) => i.urgencyLevel.toLowerCase() === urgency.toLowerCase());
    }
    
    return {
      source: 'mock',
      data: {
        totalCount: (mockData as WorklistResponse).totalCount,
        criticalCount: (mockData as WorklistResponse).criticalCount,
        highCount: (mockData as WorklistResponse).highCount,
        mediumCount: (mockData as WorklistResponse).mediumCount,
        lowCount: (mockData as WorklistResponse).lowCount,
        items,
      },
    };
  }

  const endpoint = `/api/v1/advisors/worklist?urgency=${encodeURIComponent(urgency)}`;
  const response = await fetch(endpoint, {
    headers: {
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Backend API error (${response.status}): ${response.statusText}`);
  }

  const data: WorklistResponse = await response.json();
  return {
    source: 'live',
    data,
  };
}

export async function checkBackendHealth(): Promise<HealthResponse | null> {
  try {
    const res = await fetch('/api/v1/health');
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}