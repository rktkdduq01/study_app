import api from './api';
import {
  TutorMessage,
  TutorResponse,
  QuestRecommendation,
  QuestRecommendationRequest,
  PersonalizedHint,
  HintRequest,
  GrowthRoadmap,
  TutorSession,
  LearningState,
  TutorSettings,
  ConversationContext,
  MessageType,
} from '../types/ai-tutor';

class AITutorService {
  private currentSession: TutorSession | null = null;

  // 튜터 세션 시작
  async startTutorSession(
    studentId: string,
    context: ConversationContext = ConversationContext.GENERAL_HELP
  ): Promise<TutorSession> {
    const response = await api.post('/ai/tutor/session/start', {
      studentId,
      context,
    });
    this.currentSession = response.data;
    return response.data;
  }

  // 메시지 전송 및 응답 받기
  async sendMessage(
    message: string,
    context?: ConversationContext,
    attachments?: any[]
  ): Promise<TutorResponse> {
    if (!this.currentSession) {
      throw new Error('No active tutor session');
    }

    const response = await api.post('/ai/tutor/message', {
      sessionId: this.currentSession.id,
      message,
      context,
      attachments,
    });

    // 세션에 메시지 추가
    const userMessage: TutorMessage = {
      id: Date.now().toString(),
      type: MessageType.USER,
      content: message,
      timestamp: new Date().toISOString(),
      sender: {
        name: 'You',
        isAI: false,
      },
    };

    const aiMessage: TutorMessage = {
      id: (Date.now() + 1).toString(),
      type: MessageType.AI_TUTOR,
      content: response.data.message,
      timestamp: new Date().toISOString(),
      sender: {
        name: 'AI Tutor',
        avatar: '/ai-tutor-avatar.png',
        isAI: true,
      },
      metadata: {
        context,
        questRecommendations: response.data.questRecommendations,
        growthInsights: response.data.growthInsights,
      },
    };

    this.currentSession.messages.push(userMessage, aiMessage);

    return response.data;
  }

  // 퀘스트 추천 요청
  async getQuestRecommendations(
    request: QuestRecommendationRequest
  ): Promise<QuestRecommendation[]> {
    const response = await api.post('/ai/tutor/quests/recommend', request);
    return response.data;
  }

  // 개인화된 퀘스트 추천 (대화 컨텍스트 기반)
  async getContextualQuestRecommendations(
    studentId: string,
    conversationContext: string[],
    recentPerformance: any
  ): Promise<{
    recommendations: QuestRecommendation[];
    reasoning: string;
  }> {
    const response = await api.post('/ai/tutor/quests/contextual', {
      studentId,
      conversationContext,
      recentPerformance,
    });
    return response.data;
  }

  // 개인화된 힌트 생성
  async generatePersonalizedHint(
    request: HintRequest
  ): Promise<PersonalizedHint> {
    const response = await api.post('/ai/tutor/hints/generate', request);
    return response.data;
  }

  // 적응형 힌트 시퀀스 생성
  async generateHintSequence(
    studentId: string,
    questionId: string,
    maxHints: number = 5
  ): Promise<PersonalizedHint[]> {
    const response = await api.post('/ai/tutor/hints/sequence', {
      studentId,
      questionId,
      maxHints,
    });
    return response.data;
  }

  // 성장 로드맵 생성 및 업데이트
  async generateGrowthRoadmap(
    studentId: string,
    timeframe: 'month' | 'quarter' | 'year'
  ): Promise<GrowthRoadmap> {
    const response = await api.post('/ai/tutor/roadmap/generate', {
      studentId,
      timeframe,
    });
    return response.data;
  }

  // 로드맵 진행상황 업데이트
  async updateRoadmapProgress(
    studentId: string,
    completedItems: string[]
  ): Promise<GrowthRoadmap> {
    const response = await api.patch('/ai/tutor/roadmap/update', {
      studentId,
      completedItems,
    });
    return response.data;
  }

  // 학습 상태 분석
  async analyzeLearningState(studentId: string): Promise<LearningState> {
    const response = await api.get(`/ai/tutor/state/${studentId}`);
    return response.data;
  }

  // 동기부여 메시지 생성
  async generateMotivationalMessage(
    studentId: string,
    situation: 'struggling' | 'success' | 'milestone' | 'return'
  ): Promise<{
    message: string;
    visualSupport?: string;
    nextAction?: string;
  }> {
    const response = await api.post('/ai/tutor/motivation', {
      studentId,
      situation,
    });
    return response.data;
  }

  // 개념 설명 요청
  async explainConcept(
    concept: string,
    studentProfile: any,
    depth: 'simple' | 'detailed' | 'eli5' = 'simple'
  ): Promise<{
    explanation: string;
    examples: string[];
    visualAids: any[];
    relatedConcepts: string[];
    practiceQuestions: any[];
  }> {
    const response = await api.post('/ai/tutor/explain', {
      concept,
      studentProfile,
      depth,
    });
    return response.data;
  }

  // 학습 전략 제안
  async suggestLearningStrategies(
    studentId: string,
    subject: string,
    goal: string
  ): Promise<{
    strategies: Array<{
      name: string;
      description: string;
      steps: string[];
      estimatedTime: number;
      effectiveness: number;
    }>;
    personalizedTips: string[];
  }> {
    const response = await api.post('/ai/tutor/strategies', {
      studentId,
      subject,
      goal,
    });
    return response.data;
  }

  // 진로 가이던스
  async provideCareerGuidance(
    studentId: string,
    interests: string[],
    strengths: string[]
  ): Promise<{
    careerPaths: Array<{
      title: string;
      description: string;
      requiredSkills: string[];
      recommendedSubjects: string[];
      growthPotential: string;
    }>;
    immediateSteps: string[];
    longTermPlan: any;
  }> {
    const response = await api.post('/ai/tutor/career', {
      studentId,
      interests,
      strengths,
    });
    return response.data;
  }

  // 학부모 리포트 생성
  async generateParentReport(
    studentId: string,
    period: { start: string; end: string }
  ): Promise<{
    summary: string;
    achievements: string[];
    areasOfImprovement: string[];
    recommendations: string[];
    nextSteps: string[];
  }> {
    const response = await api.post('/ai/tutor/parent-report', {
      studentId,
      period,
    });
    return response.data;
  }

  // 음성 대화 (텍스트 변환)
  async processVoiceInput(
    audioBlob: Blob,
    sessionId: string
  ): Promise<{
    transcription: string;
    response: TutorResponse;
  }> {
    const formData = new FormData();
    formData.append('audio', audioBlob);
    formData.append('sessionId', sessionId);

    const response = await api.post('/ai/tutor/voice', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  // 튜터 설정 업데이트
  async updateTutorSettings(
    studentId: string,
    settings: Partial<TutorSettings>
  ): Promise<TutorSettings> {
    const response = await api.patch(`/ai/tutor/settings/${studentId}`, settings);
    return response.data;
  }

  // 세션 종료
  async endTutorSession(sessionId: string): Promise<{
    summary: string;
    keyTakeaways: string[];
    followUpTasks: string[];
  }> {
    const response = await api.post(`/ai/tutor/session/${sessionId}/end`);
    this.currentSession = null;
    return response.data;
  }

  // 이전 세션 기록 조회
  async getSessionHistory(
    studentId: string,
    limit: number = 10
  ): Promise<TutorSession[]> {
    const response = await api.get(`/ai/tutor/sessions/${studentId}`, {
      params: { limit },
    });
    return response.data;
  }

  // 학습 인사이트 대시보드 데이터
  async getInsightsDashboard(studentId: string): Promise<{
    weeklyProgress: any;
    conceptMastery: any;
    learningPatterns: any;
    recommendations: any;
  }> {
    const response = await api.get(`/ai/tutor/insights/${studentId}`);
    return response.data;
  }
}

export default new AITutorService();