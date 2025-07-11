// AI 튜터/챗봇 관련 타입 정의

export enum MessageType {
  USER = 'user',
  AI_TUTOR = 'ai_tutor',
  SYSTEM = 'system',
  QUEST_RECOMMENDATION = 'quest_recommendation',
  GROWTH_ROADMAP = 'growth_roadmap',
  HINT = 'hint',
  ENCOURAGEMENT = 'encouragement'
}

export enum TutorPersonality {
  FRIENDLY = 'friendly',        // 친근한 친구 같은 튜터
  PROFESSIONAL = 'professional', // 전문적인 선생님
  MOTIVATIONAL = 'motivational', // 동기부여 코치
  SOCRATIC = 'socratic'         // 소크라테스식 질문형
}

export enum ConversationContext {
  GENERAL_HELP = 'general_help',
  QUEST_GUIDANCE = 'quest_guidance',
  CONCEPT_EXPLANATION = 'concept_explanation',
  PROBLEM_SOLVING = 'problem_solving',
  CAREER_GUIDANCE = 'career_guidance',
  MOTIVATION = 'motivation',
  REVIEW = 'review'
}

export interface TutorMessage {
  id: string;
  type: MessageType;
  content: string;
  timestamp: string;
  sender: {
    name: string;
    avatar?: string;
    isAI: boolean;
  };
  metadata?: MessageMetadata;
  attachments?: MessageAttachment[];
  actions?: MessageAction[];
}

export interface MessageMetadata {
  context?: ConversationContext;
  emotion?: 'happy' | 'confused' | 'frustrated' | 'excited' | 'neutral';
  confidence?: number;
  relatedConcepts?: string[];
  questRecommendations?: QuestRecommendation[];
  growthInsights?: GrowthInsight[];
}

export interface MessageAttachment {
  type: 'image' | 'diagram' | 'code' | 'link' | 'quest' | 'achievement';
  url?: string;
  title: string;
  description?: string;
  data?: any;
}

export interface MessageAction {
  id: string;
  label: string;
  type: 'primary' | 'secondary' | 'success' | 'warning';
  action: string; // Route or function name
  data?: any;
}

// 퀘스트 추천 시스템
export interface QuestRecommendation {
  questId: number;
  title: string;
  reason: string;
  matchScore: number; // 0-100
  estimatedTime: number;
  difficulty: string;
  concepts: string[];
  benefits: string[];
  prerequisites?: string[];
}

export interface QuestRecommendationRequest {
  studentId: string;
  currentLevel: number;
  recentPerformance: PerformanceMetrics;
  interests: string[];
  availableTime?: number;
  learningGoals?: string[];
  excludeCompleted?: boolean;
}

export interface PerformanceMetrics {
  averageScore: number;
  completionRate: number;
  strugglingConcepts: string[];
  strongConcepts: string[];
  preferredDifficulty: string;
  learningPace: 'slow' | 'medium' | 'fast';
}

// 개인화된 힌트 시스템
export interface PersonalizedHint {
  id: string;
  content: string;
  level: number; // 1-5, 점진적으로 구체적
  type: HintType;
  personalizedElements: PersonalizationElement[];
  visualAid?: string;
  relatedExample?: string;
  nextSteps?: string[];
}

export enum HintType {
  CONCEPTUAL = 'conceptual',         // 개념 이해 힌트
  PROCEDURAL = 'procedural',         // 절차/방법 힌트
  STRATEGIC = 'strategic',           // 전략적 힌트
  METACOGNITIVE = 'metacognitive',   // 메타인지 힌트
  MOTIVATIONAL = 'motivational',     // 동기부여 힌트
  EXAMPLE_BASED = 'example_based'    // 예시 기반 힌트
}

export interface PersonalizationElement {
  type: 'learning_style' | 'past_mistake' | 'interest' | 'strength';
  value: string;
  application: string;
}

export interface HintRequest {
  studentId: string;
  questionId: string;
  currentAttempt: any;
  attemptHistory: AttemptHistory[];
  timeSpent: number;
  previousHints: string[];
}

export interface AttemptHistory {
  attempt: any;
  timestamp: string;
  correct: boolean;
  mistakeType?: string;
}

// 성장 로드맵
export interface GrowthRoadmap {
  studentId: string;
  currentStage: GrowthStage;
  milestones: Milestone[];
  shortTermGoals: Goal[];
  longTermGoals: Goal[];
  recommendedPath: LearningPathNode[];
  alternativePaths: LearningPathNode[][];
  estimatedCompletion: string;
  nextCheckpoint: Checkpoint;
}

export interface GrowthStage {
  level: number;
  title: string;
  description: string;
  masteredConcepts: string[];
  currentFocus: string[];
  readyForNext: boolean;
}

export interface Milestone {
  id: string;
  title: string;
  description: string;
  requiredAchievements: string[];
  requiredLevel: number;
  requiredConcepts: string[];
  reward: {
    type: 'badge' | 'title' | 'unlock' | 'feature';
    value: string;
  };
  completed: boolean;
  completedAt?: string;
  progress: number;
}

export interface Goal {
  id: string;
  title: string;
  type: 'academic' | 'skill' | 'personal' | 'social';
  timeframe: 'daily' | 'weekly' | 'monthly' | 'quarterly';
  measurableTarget: string;
  currentProgress: number;
  targetValue: number;
  strategies: string[];
  relatedQuests: number[];
}

export interface LearningPathNode {
  id: string;
  type: 'concept' | 'skill' | 'project' | 'assessment';
  title: string;
  estimatedTime: number;
  prerequisites: string[];
  outcomes: string[];
  resources: Resource[];
  alternativeActivities?: Activity[];
}

export interface Resource {
  type: 'video' | 'article' | 'interactive' | 'practice' | 'game';
  title: string;
  url: string;
  duration?: number;
}

export interface Activity {
  id: string;
  title: string;
  type: string;
  difficulty: string;
  estimatedTime: number;
}

export interface Checkpoint {
  date: string;
  goals: string[];
  assessmentType: 'quiz' | 'project' | 'portfolio' | 'peer_review';
  preparationTips: string[];
}

// AI 튜터 대화 관리
export interface TutorSession {
  id: string;
  studentId: string;
  startTime: string;
  endTime?: string;
  messages: TutorMessage[];
  context: ConversationContext;
  mood: 'positive' | 'neutral' | 'needs_support';
  topicsDiscussed: string[];
  questsRecommended: number[];
  insightsGenerated: GrowthInsight[];
}

export interface GrowthInsight {
  id: string;
  type: 'strength' | 'improvement' | 'opportunity' | 'achievement';
  title: string;
  description: string;
  evidence: string[];
  recommendations: string[];
  impact: 'high' | 'medium' | 'low';
  timestamp: string;
}

// AI 튜터 응답 구조
export interface TutorResponse {
  message: string;
  personality: TutorPersonality;
  suggestions?: Suggestion[];
  questRecommendations?: QuestRecommendation[];
  hints?: PersonalizedHint[];
  growthInsights?: GrowthInsight[];
  visualAids?: VisualAid[];
  followUpQuestions?: string[];
  emotionalSupport?: EmotionalSupport;
}

export interface Suggestion {
  type: 'action' | 'resource' | 'strategy' | 'practice';
  title: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
  estimatedImpact: string;
}

export interface VisualAid {
  type: 'diagram' | 'chart' | 'animation' | 'infographic';
  url: string;
  caption: string;
  interactionPoints?: { x: number; y: number; label: string }[];
}

export interface EmotionalSupport {
  type: 'encouragement' | 'celebration' | 'empathy' | 'motivation';
  message: string;
  gif?: string;
  suggestion?: string;
}

// 학습 상태 추적
export interface LearningState {
  currentActivity?: {
    type: string;
    id: string;
    startTime: string;
    progress: number;
  };
  recentConcepts: string[];
  strugglingAreas: string[];
  momentum: 'building' | 'steady' | 'slowing' | 'stopped';
  engagementLevel: number; // 0-100
  needsBreak: boolean;
  recommendedBreakTime?: number;
}

// AI 튜터 설정
export interface TutorSettings {
  personality: TutorPersonality;
  responseLength: 'concise' | 'balanced' | 'detailed';
  encouragementFrequency: 'low' | 'medium' | 'high';
  hintProgressiveness: 'gradual' | 'moderate' | 'direct';
  visualAidPreference: boolean;
  voiceEnabled: boolean;
  language: string;
}