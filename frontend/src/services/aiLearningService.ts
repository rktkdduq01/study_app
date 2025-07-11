import api from './api';
import {
  AIQuestionRequest,
  AIGeneratedQuestion,
  StudentLearningProfile,
  LearningAnalysis,
  AdaptiveLearningPath,
  ConceptLevel,
  ProblemPurpose,
} from '../types/ai-learning';

class AILearningService {
  // 학생 프로필 분석 및 업데이트
  async analyzeStudentProfile(studentId: string): Promise<StudentLearningProfile> {
    const response = await api.get(`/ai/students/${studentId}/profile`);
    return response.data;
  }

  async updateStudentProfile(
    studentId: string, 
    updates: Partial<StudentLearningProfile>
  ): Promise<StudentLearningProfile> {
    const response = await api.patch(`/ai/students/${studentId}/profile`, updates);
    return response.data;
  }

  // AI 문제 생성
  async generateAdaptiveQuestions(request: AIQuestionRequest): Promise<AIGeneratedQuestion[]> {
    const response = await api.post('/ai/questions/generate', request);
    return response.data;
  }

  // 개념 기반 문제 생성
  async generateConceptualQuestions(
    studentId: string,
    subject: string,
    concept: string,
    level: ConceptLevel
  ): Promise<AIGeneratedQuestion[]> {
    const profile = await this.analyzeStudentProfile(studentId);
    
    const request: AIQuestionRequest = {
      studentProfile: profile,
      subject,
      topic: concept,
      purpose: ProblemPurpose.CONCEPT_CHECK,
      conceptLevel: level,
      count: 5,
      constraints: {
        realWorldContext: true,
        gamification: true,
      }
    };

    return this.generateAdaptiveQuestions(request);
  }

  // 오개념 진단 문제 생성
  async generateMisconceptionDiagnostics(
    studentId: string,
    subject: string,
    topic: string
  ): Promise<AIGeneratedQuestion[]> {
    const profile = await this.analyzeStudentProfile(studentId);
    
    const request: AIQuestionRequest = {
      studentProfile: profile,
      subject,
      topic,
      purpose: ProblemPurpose.MISCONCEPTION_DETECTION,
      conceptLevel: ConceptLevel.BASIC_UNDERSTANDING,
      count: 3,
    };

    return this.generateAdaptiveQuestions(request);
  }

  // 학습 분석
  async analyzeLearningProgress(
    studentId: string,
    timeframe?: { start: string; end: string }
  ): Promise<LearningAnalysis> {
    const params = timeframe ? { ...timeframe } : {};
    const response = await api.get(`/ai/students/${studentId}/analysis`, { params });
    return response.data;
  }

  // 적응형 학습 경로 생성
  async generateLearningPath(
    studentId: string,
    subject: string,
    targetConcepts: string[]
  ): Promise<AdaptiveLearningPath> {
    const response = await api.post('/ai/learning-path/generate', {
      studentId,
      subject,
      targetConcepts,
    });
    return response.data;
  }

  // 실시간 힌트 생성
  async generateAdaptiveHint(
    questionId: string,
    studentId: string,
    currentAttempt: any,
    attemptNumber: number
  ): Promise<{
    hint: string;
    visualAid?: string;
    relatedConcept: string;
  }> {
    const response = await api.post('/ai/hints/generate', {
      questionId,
      studentId,
      currentAttempt,
      attemptNumber,
    });
    return response.data;
  }

  // 피드백 생성
  async generatePersonalizedFeedback(
    questionId: string,
    studentId: string,
    answer: any,
    timeSpent: number
  ): Promise<{
    feedback: string;
    conceptsToReview: string[];
    nextSteps: string[];
    encouragement: string;
  }> {
    const response = await api.post('/ai/feedback/generate', {
      questionId,
      studentId,
      answer,
      timeSpent,
    });
    return response.data;
  }

  // 개념 설명 생성
  async generateConceptExplanation(
    concept: string,
    studentProfile: StudentLearningProfile
  ): Promise<{
    explanation: string;
    examples: string[];
    visualizations: string[];
    checkQuestions: string[];
  }> {
    const response = await api.post('/ai/concepts/explain', {
      concept,
      studentProfile,
    });
    return response.data;
  }

  // 학습 세션 최적화
  async optimizeLearningSession(
    studentId: string,
    availableTime: number,
    subjects: string[]
  ): Promise<{
    sessionPlan: Array<{
      activity: string;
      duration: number;
      concept: string;
      type: string;
    }>;
    expectedOutcomes: string[];
  }> {
    const response = await api.post('/ai/session/optimize', {
      studentId,
      availableTime,
      subjects,
    });
    return response.data;
  }

  // 동료 학습 매칭
  async findStudyPartners(
    studentId: string,
    subject: string,
    concept: string
  ): Promise<{
    partners: Array<{
      studentId: string;
      matchScore: number;
      strengths: string[];
      learningStyle: string;
    }>;
    collaborativeActivities: string[];
  }> {
    const response = await api.post('/ai/collaboration/match', {
      studentId,
      subject,
      concept,
    });
    return response.data;
  }
}

export default new AILearningService();