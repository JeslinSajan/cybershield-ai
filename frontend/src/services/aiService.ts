import { apiFetch } from './api';

export interface ExplanationResponse {
  target_id: string;
  target_type: string;
  explanation: string;
  provider: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

export interface Conversation {
  id: string;
  subject_type: string;
  subject_id: string;
  provider_type: string;
  created_at: string;
  updated_at: string;
  messages?: ChatMessage[];
}

export interface ChatResponse {
  conversation_id: string;
  response: string;
  context_type: string;
  context_id: string;
  provider: string;
}

export const aiService = {
  explainAlert: async (alertId: string): Promise<ExplanationResponse> => {
    return apiFetch<ExplanationResponse>('/ai/explain-alert', {
      method: 'POST',
      body: JSON.stringify({ alert_id: alertId }),
    });
  },

  explainVulnerability: async (vulnerabilityId: string): Promise<ExplanationResponse> => {
    return apiFetch<ExplanationResponse>('/ai/explain-vulnerability', {
      method: 'POST',
      body: JSON.stringify({ vulnerability_id: vulnerabilityId }),
    });
  },

  explainRisk: async (deviceId: string): Promise<ExplanationResponse> => {
    return apiFetch<ExplanationResponse>('/ai/explain-risk', {
      method: 'POST',
      body: JSON.stringify({ device_id: deviceId }),
    });
  },

  chat: async (message: string, contextType: string, contextId: string): Promise<ChatResponse> => {
    return apiFetch<ChatResponse>('/ai/chat', {
      method: 'POST',
      body: JSON.stringify({
        message,
        context_type: contextType,
        context_id: contextId,
      }),
    });
  },

  listConversations: async (): Promise<Conversation[]> => {
    return apiFetch<Conversation[]>('/ai/conversations');
  },

  getConversation: async (conversationId: string): Promise<Conversation> => {
    return apiFetch<Conversation>(`/ai/conversations/${conversationId}`);
  },
};
