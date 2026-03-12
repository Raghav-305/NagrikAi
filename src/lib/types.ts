export type ComplaintStatus = 'Pending' | 'In Progress' | 'Resolved' | 'Rejected';
export type ComplaintUrgency = 'Low' | 'Medium' | 'High';
export type ComplaintSentiment = 'Positive' | 'Neutral' | 'Negative';

export interface Location {
  lat: number;
  lng: number;
  address: string;
}

export interface TimelineEvent {
  id: string;
  status: string;
  timestamp: string;
  description: string;
  actor: string;
}

export interface Complaint {
  id: string;
  citizenName: string;
  text: string;
  category: string;
  status: ComplaintStatus;
  urgency: ComplaintUrgency;
  sentiment: ComplaintSentiment;
  department: string;
  location: Location;
  timestamp: string;
  imageUrl?: string;
  timeline: TimelineEvent[];
}

export interface DepartmentStats {
  name: string;
  total: number;
  resolved: number;
  pending: number;
  avgResolutionTimeDays: number;
  workloadScore: number;
}