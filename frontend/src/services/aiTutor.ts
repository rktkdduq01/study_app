import { api } from './api';

export interface ContentGenerationRequest {
  subject: string;
  topic: string;
  difficultyLevel?: number;
  contentType?: string;
}

export interface FeedbackRequest {
  question: string;
  userAnswer: string;
  correctAnswer: string;
  subject: string;
}

export interface PracticeQuestionsRequest {
  subject: string;
  topic: string;
  count?: number;
}

export interface LearningPathRequest {
  goal: string;
  timelineDays?: number;
}

export interface ConceptExplanationRequest {
  concept: string;
  userLevel?: string;
  learningStyle?: string;
  examplesCount?: number;
}

export interface HintRequest {
  question: string;
  userAttempts: string[];
  hintLevel?: number;
}

export interface ChatRequest {
  message: string;
  context?: Record<string, any>;
  sessionId?: number;
}

export interface LearningContent {
  type: string;
  title: string;
  sections: Array<{
    type: string;
    content: string;
    examples?: string[];
    visuals?: string[];
  }>;
  practiceProblems: Array<{
    question: string;
    type: string;
    options?: string[];
    correctAnswer: string;
    explanation: string;
  }>;
  resources: string[];
  adaptationReason?: string;
}

export interface AIFeedback {
  isCorrect: boolean;
  feedback: string;
  strengths: string[];
  improvements: string[];
  nextSteps: string[];
  recommendations?: Array<{
    topic: string;
    reason: string;
  }>;
}

export interface PracticeQuestion {
  id: string;
  question: string;
  type: 'multiple_choice' | 'short_answer' | 'problem_solving';
  options?: string[];
  correctAnswer: string;
  explanation: string;
  difficulty: number;
  estimatedTime: number;
  topicTags: string[];
}

export interface LearningPath {
  goal: string;
  durationDays: number;
  modules: Array<{
    name: string;
    topics: string[];
    estimatedHours: number;
    order: number;
  }>;
  milestones: Array<{
    day: number;
    title: string;
    goals: string[];
    assessmentType: string;
  }>;
  dailySchedule: Record<string, any>;
}

export interface LearningStyleAnalysis {
  primaryStyle: 'visual' | 'auditory' | 'kinesthetic' | 'reading/writing' | 'balanced';
  characteristics: string[];
  optimalStrategies: string[];
  contentRecommendations: string[];
  studyScheduleSuggestions: string[];
  potentialChallenges: string[];
  solutions: string[];
}

export interface ConceptExplanation {
  concept: string;
  mainExplanation: string;
  examples: Array<{
    title: string;
    description: string;
    visual?: string;
  }>;
  visualDescriptions: string[];
  commonMisconceptions: string[];
  practiceTips: string[];
  interactiveElements: Array<{
    type: string;
    title: string;
    interactive: boolean;
  }>;
}

export interface Hint {
  hint: string;
  guidance: string;
  level: number;
  nextLevelAvailable: boolean;
}

export interface ChatResponse {
  userMessage: string;
  aiResponse: string;
  suggestions: string[];
  contextUpdated: boolean;
}

export interface SessionSummary {
  sessionId: number;
  durationMinutes: number;
  topicsCovered: string[];
  accuracy: number;
  strengths: string[];
  areasToImprove: string[];
  nextRecommendations: Array<{
    topic: string;
    reason: string;
    difficulty: number;
  }>;
}

class AITutorService {
  async generateContent(request: ContentGenerationRequest): Promise<LearningContent> {
    const response = await api.post('/ai-tutor/generate-content', request);
    return response.data.content;
  }

  async provideFeedback(request: FeedbackRequest): Promise<AIFeedback> {
    const response = await api.post('/ai-tutor/feedback', request);
    return response.data.feedback;
  }

  async generatePracticeQuestions(request: PracticeQuestionsRequest): Promise<PracticeQuestion[]> {
    const response = await api.post('/ai-tutor/practice-questions', request);
    return response.data.questions;
  }

  async createLearningPath(request: LearningPathRequest): Promise<LearningPath> {
    const response = await api.post('/ai-tutor/learning-path', request);
    return response.data.learning_path;
  }

  async analyzeLearningStyle(): Promise<LearningStyleAnalysis> {
    const response = await api.post('/ai-tutor/analyze-style');
    return response.data.analysis;
  }

  async explainConcept(request: ConceptExplanationRequest): Promise<ConceptExplanation> {
    const response = await api.post('/ai-tutor/explain', request);
    return response.data.explanation;
  }

  async getHint(request: HintRequest): Promise<Hint> {
    const response = await api.post('/ai-tutor/hint', request);
    return response.data.hint;
  }

  async chat(request: ChatRequest): Promise<ChatResponse> {
    const response = await api.post('/ai-tutor/chat', request);
    return response.data;
  }

  async getSessionSummary(sessionId: number): Promise<SessionSummary> {
    const response = await api.get(`/ai-tutor/session/${sessionId}/summary`);
    return response.data;
  }

  // Real-time features using WebSocket
  subscribeToAIFeedback(userId: string, callback: (feedback: AIFeedback) => void) {
    // This would connect to WebSocket and listen for AI feedback events
    // Implementation depends on your WebSocket setup
  }

  subscribeToContentGeneration(userId: string, callback: (content: LearningContent) => void) {
    // This would connect to WebSocket and listen for content generation events
    // Implementation depends on your WebSocket setup
  }
}

export const aiTutorService = new AITutorService();