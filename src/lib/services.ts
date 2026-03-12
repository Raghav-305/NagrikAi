import { MOCK_COMPLAINTS, DEPARTMENT_STATS } from './mock-data';
import { Complaint, DepartmentStats } from './types';

/**
 * AI Service Mock
 * In production, this would call real GenAI models via Genkit or Vertex AI.
 */
export const AIService = {
  classify: async (text: string) => {
    // Simulated AI latency
    await new Promise(r => setTimeout(r, 800));
    return {
      category: "Road Infrastructure",
      urgency: "High" as const,
      sentiment: "Negative" as const,
      confidence: 0.94
    };
  }
};

/**
 * Blockchain Service Mock
 * In production, this would log immutable records to a public or private ledger (e.g., Ethereum).
 */
export const BlockchainService = {
  logEvent: async (complaintId: string, status: string) => {
    console.log(`[Blockchain] Logging status change for ${complaintId} to ${status}`);
    return {
      txHash: `0x${Math.random().toString(16).slice(2, 42)}`,
      blockNumber: Math.floor(Math.random() * 1000000)
    };
  }
};

/**
 * Database Service Mock
 * In production, this would interact with PostgreSQL or Firestore.
 */
export const DatabaseService = {
  getComplaints: async (): Promise<Complaint[]> => {
    return MOCK_COMPLAINTS;
  },
  getComplaintById: async (id: string): Promise<Complaint | undefined> => {
    return MOCK_COMPLAINTS.find(c => c.id === id);
  },
  getDashboardMetrics: async () => {
    const total = MOCK_COMPLAINTS.length;
    const resolved = MOCK_COMPLAINTS.filter(c => c.status === 'Resolved').length;
    const open = total - resolved;
    const pending = MOCK_COMPLAINTS.filter(c => c.status === 'Pending').length;
    
    return {
      total,
      resolved,
      open,
      pending,
      avgResolutionTime: "3.2 Days",
      growth: "+12%"
    };
  },
  getDepartmentStats: async (): Promise<DepartmentStats[]> => {
    return DEPARTMENT_STATS;
  }
};