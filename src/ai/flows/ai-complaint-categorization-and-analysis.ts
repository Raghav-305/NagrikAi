'use server';
/**
 * @fileOverview This file defines a Genkit flow for AI-powered complaint categorization and analysis.
 *
 * - aiComplaintCategorizationAndAnalysis - A function that analyzes a complaint to classify its category,
 *   detect sentiment, and determine urgency using AI.
 * - AIComplaintCategorizationAndAnalysisInput - The input type for the aiComplaintCategorizationAndAnalysis function.
 * - AIComplaintCategorizationAndAnalysisOutput - The return type for the aiComplaintCategorizationAndAnalysis function.
 */

import { ai } from '@/ai/genkit';
import { z } from 'genkit';

const AIComplaintCategorizationAndAnalysisInputSchema = z.object({
  complaintText: z.string().describe('The text content of the citizen complaint.'),
});
export type AIComplaintCategorizationAndAnalysisInput = z.infer<typeof AIComplaintCategorizationAndAnalysisInputSchema>;

const AIComplaintCategorizationAndAnalysisOutputSchema = z.object({
  category: z.string().describe('The classified category of the complaint (e.g., "Road Infrastructure", "Waste Management", "Public Safety", "Water Supply", "Electricity").'),
  sentiment: z.enum(['Positive', 'Neutral', 'Negative']).describe('The detected sentiment of the complaint text.'),
  urgency: z.enum(['Low', 'Medium', 'High']).describe('The determined urgency level of the complaint.'),
});
export type AIComplaintCategorizationAndAnalysisOutput = z.infer<typeof AIComplaintCategorizationAndAnalysisOutputSchema>;

export async function aiComplaintCategorizationAndAnalysis(input: AIComplaintCategorizationAndAnalysisInput): Promise<AIComplaintCategorizationAndAnalysisOutput> {
  return aiComplaintCategorizationAndAnalysisFlow(input);
}

const prompt = ai.definePrompt({
  name: 'categorizeComplaintPrompt',
  input: { schema: AIComplaintCategorizationAndAnalysisInputSchema },
  output: { schema: AIComplaintCategorizationAndAnalysisOutputSchema },
  prompt: `You are an expert public service complaint analyst. Your task is to analyze the provided citizen complaint text and determine its category, sentiment, and urgency.

Complaint Text: {{{complaintText}}}

Carefully consider the tone and content to accurately assign the sentiment and urgency. For category, choose from common public service areas.`, 
});

const aiComplaintCategorizationAndAnalysisFlow = ai.defineFlow(
  {
    name: 'aiComplaintCategorizationAndAnalysisFlow',
    inputSchema: AIComplaintCategorizationAndAnalysisInputSchema,
    outputSchema: AIComplaintCategorizationAndAnalysisOutputSchema,
  },
  async (input) => {
    const { output } = await prompt(input);
    if (!output) {
      throw new Error('Failed to categorize complaint. Output was null or undefined.');
    }
    return output;
  }
);
