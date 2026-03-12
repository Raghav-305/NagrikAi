import { Complaint, DepartmentStats } from './types';

const CATEGORIES = [
  'Road Infrastructure',
  'Waste Management',
  'Public Safety',
  'Water Supply',
  'Electricity',
  'Health Services',
];

const DEPARTMENTS = [
  'Public Works Department',
  'Sanitation Department',
  'Police Headquarters',
  'Water Authority',
  'Electric Grid Corp',
  'Health Commission',
];

const STATUSES: Complaint['status'][] = ['Pending', 'In Progress', 'Resolved', 'Rejected'];
const URGENCIES: Complaint['urgency'][] = ['Low', 'Medium', 'High'];
const SENTIMENTS: Complaint['sentiment'][] = ['Positive', 'Neutral', 'Negative'];

const CITIZEN_NAMES = ['Aarav Sharma', 'Sanya Gupta', 'Vikram Singh', 'Ananya Iyer', 'Rahul Verma', 'Priya Reddy'];

const COMPLAINT_TEMPLATES = [
  'Huge pothole on the main road causing traffic jams and potential accidents.',
  'Garbage overflow at the street corner. It hasn’t been collected for 4 days.',
  'Streetlights are not working for the last week, making it unsafe to walk at night.',
  'Sudden water leakage in the pipeline near house number 42.',
  'Frequent power outages happening every evening for 2 hours.',
  'Illegal parking in the residential area blocking fire exit access.',
  'Sewerage blockage causing bad smell in the entire neighborhood.',
  'Stray dog menace near the local park, kids are afraid to play.',
  'Broken drainage cover on the sidewalk is dangerous for pedestrians.',
  'Unauthorized construction happening in the green belt zone.',
];

export const MOCK_COMPLAINTS: Complaint[] = Array.from({ length: 60 }).map((_, i) => {
  const id = `CN-${1000 + i}`;
  const templateIdx = i % COMPLAINT_TEMPLATES.length;
  const categoryIdx = i % CATEGORIES.length;
  const statusIdx = i % STATUSES.length;
  const urgencyIdx = (i + Math.floor(i / 10)) % URGENCIES.length;
  const sentimentIdx = (i + 1) % SENTIMENTS.length;
  
  const timestamp = new Date(Date.now() - Math.floor(Math.random() * 1000000000)).toISOString();

  return {
    id,
    citizenName: CITIZEN_NAMES[i % CITIZEN_NAMES.length],
    text: COMPLAINT_TEMPLATES[templateIdx],
    category: CATEGORIES[categoryIdx],
    status: STATUSES[statusIdx],
    urgency: URGENCIES[urgencyIdx],
    sentiment: SENTIMENTS[sentimentIdx],
    department: DEPARTMENTS[categoryIdx],
    location: {
      lat: 28.6139 + (Math.random() - 0.5) * 0.1,
      lng: 77.2090 + (Math.random() - 0.5) * 0.1,
      address: `${Math.floor(Math.random() * 500)}, Sector ${Math.floor(Math.random() * 20)}, New Delhi`,
    },
    timestamp,
    imageUrl: `https://picsum.photos/seed/${id}/600/400`,
    timeline: [
      {
        id: 't1',
        status: 'Submitted',
        timestamp: timestamp,
        description: 'Complaint registered by citizen.',
        actor: 'Citizen',
      },
      ...(statusIdx > 0 ? [{
        id: 't2',
        status: 'Assigned',
        timestamp: new Date(new Date(timestamp).getTime() + 3600000).toISOString(),
        description: `Routed to ${DEPARTMENTS[categoryIdx]} for review.`,
        actor: 'System AI',
      }] : []),
      ...(statusIdx > 1 ? [{
        id: 't3',
        status: 'In Progress',
        timestamp: new Date(new Date(timestamp).getTime() + 86400000).toISOString(),
        description: 'Inspection team dispatched to site.',
        actor: DEPARTMENTS[categoryIdx],
      }] : []),
    ],
  };
});

export const DEPARTMENT_STATS: DepartmentStats[] = DEPARTMENTS.map((name, i) => ({
  name,
  total: 10 + Math.floor(Math.random() * 30),
  resolved: 5 + Math.floor(Math.random() * 15),
  pending: 5 + Math.floor(Math.random() * 10),
  avgResolutionTimeDays: 2 + Math.random() * 5,
  workloadScore: 40 + Math.floor(Math.random() * 50),
}));