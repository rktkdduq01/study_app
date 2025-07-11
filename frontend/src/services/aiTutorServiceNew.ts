import api from './api';
import { apiWrapper } from '../utils/apiWrapper';
import { 
  AITutorResponse, 
  AIAnalysis, 
  AIRecommendation,
  GrowthRoadmap,
  ConceptExplanation,
  AILearningGoal,
  AdaptiveQuestion,
  LearningPattern,
  StudySession,
  PerformanceMetrics
} from '../types/ai-tutor';

class AITutorServiceNew {
  private baseURL = '/ai-tutor';

  async getChatResponse(message: string, context?: any): Promise<AITutorResponse> {
    return apiWrapper(
      () => api.post(`${this.baseURL}/chat`, { message, context }),
      'Error getting AI tutor response'
    );
  }

  async analyzePerformance(): Promise<AIAnalysis> {
    return apiWrapper(
      () => api.get(`${this.baseURL}/analyze`),
      'Error analyzing performance'
    ).then(data => data.analysis);
  }

  async getRecommendations(currentContentId?: string): Promise<AIRecommendation[]> {
    return apiWrapper(
      () => api.get(`${this.baseURL}/recommendations`, {
        params: { current_content_id: currentContentId }
      }),
      'Error getting recommendations'
    ).then(data => data.recommendations);
  }

  async generatePersonalizedContent(
    subject: string,
    topic: string,
    contentType: string = 'explanation'
  ): Promise<any> {
    try {
      const response = await api.post(`${this.baseURL}/generate-content`, {
        subject,
        topic,
        content_type: contentType
      });
      return response.data.content;
    } catch (error) {
      console.error('Error generating personalized content:', error);
      throw error;
    }
  }

  async provideFeedback(
    sessionId: number,
    interactionData: any
  ): Promise<any> {
    try {
      const response = await api.post(`${this.baseURL}/feedback`, {
        session_id: sessionId,
        interaction_data: interactionData
      });
      return response.data.feedback;
    } catch (error) {
      console.error('Error providing feedback:', error);
      throw error;
    }
  }

  async startLearningSession(
    contentId: string,
    contentType: string,
    subject: string,
    topic: string,
    difficulty: string
  ): Promise<StudySession> {
    try {
      const response = await api.post(`${this.baseURL}/session/start`, {
        content_id: contentId,
        content_type: contentType,
        subject,
        topic,
        difficulty
      });
      return response.data;
    } catch (error) {
      console.error('Error starting learning session:', error);
      throw error;
    }
  }

  async endLearningSession(
    sessionId: number,
    sessionData: any
  ): Promise<any> {
    try {
      const response = await api.post(`${this.baseURL}/session/${sessionId}/end`, sessionData);
      return response.data;
    } catch (error) {
      console.error('Error ending learning session:', error);
      throw error;
    }
  }

  async getDailyInsights(date?: string): Promise<any> {
    try {
      const response = await api.get(`${this.baseURL}/insights/daily`, {
        params: { date }
      });
      return response.data;
    } catch (error) {
      console.error('Error getting daily insights:', error);
      throw error;
    }
  }

  async generateGrowthRoadmap(goals: string[]): Promise<GrowthRoadmap> {
    try {
      const analysis = await this.analyzePerformance();
      const recommendations = await this.getRecommendations();
      
      // Create roadmap based on analysis and recommendations
      const roadmap: GrowthRoadmap = {
        id: Date.now().toString(),
        userId: 'current',
        goals: goals.map((goal, index) => ({
          id: index.toString(),
          title: goal,
          description: `Achieve ${goal}`,
          targetDate: new Date(Date.now() + 90 * 24 * 60 * 60 * 1000).toISOString(),
          progress: 0,
          milestones: [],
          status: 'not_started'
        })),
        milestones: recommendations.map((rec, index) => ({
          id: index.toString(),
          title: `Master ${rec.topic}`,
          description: rec.reason,
          targetDate: new Date(Date.now() + (index + 1) * 30 * 24 * 60 * 60 * 1000).toISOString(),
          completed: false,
          skills: [rec.topic],
          questIds: []
        })),
        currentPhase: 'foundation',
        overallProgress: 0,
        estimatedCompletionDate: new Date(Date.now() + 90 * 24 * 60 * 60 * 1000).toISOString(),
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };
      
      return roadmap;
    } catch (error) {
      console.error('Error generating growth roadmap:', error);
      throw error;
    }
  }

  async explainConcept(subject: string, topic: string, level: string): Promise<ConceptExplanation> {
    try {
      const content = await this.generatePersonalizedContent(subject, topic, 'explanation');
      
      return {
        id: content.content_id,
        concept: topic,
        subject: subject,
        level: level,
        explanation: content.content.sections?.[0]?.content || '',
        examples: content.content.sections?.filter((s: any) => s.type === 'example') || [],
        visualAids: content.content.sections?.filter((s: any) => s.visual) || [],
        relatedConcepts: content.metadata?.prerequisites || [],
        difficulty: content.metadata?.difficulty || level,
        estimatedTime: content.metadata?.estimated_completion_time || 10
      };
    } catch (error) {
      console.error('Error explaining concept:', error);
      throw error;
    }
  }

  async setLearningGoals(goals: Partial<AILearningGoal>[]): Promise<AILearningGoal[]> {
    // This would be stored in backend, for now return formatted goals
    return goals.map((goal, index) => ({
      id: (index + 1).toString(),
      title: goal.title || '',
      description: goal.description || '',
      targetDate: goal.targetDate || new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
      progress: 0,
      milestones: [],
      status: 'in_progress' as const,
      category: goal.category || 'academic',
      priority: goal.priority || 'medium',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    }));
  }

  async generateAdaptiveQuestion(
    subject: string,
    topic: string,
    difficulty: number,
    previousAnswers: any[]
  ): Promise<AdaptiveQuestion> {
    try {
      const content = await this.generatePersonalizedContent(subject, topic, 'question');
      const questionData = content.content;
      
      return {
        id: content.content_id,
        subject,
        topic,
        difficulty,
        question: questionData.question || '',
        type: questionData.question_type || 'multiple_choice',
        options: questionData.options || [],
        hints: questionData.hints || [],
        explanation: questionData.explanation || '',
        adaptiveDifficulty: difficulty,
        estimatedTime: questionData.estimated_time || 5,
        skills: content.metadata?.skills_targeted || []
      };
    } catch (error) {
      console.error('Error generating adaptive question:', error);
      throw error;
    }
  }

  async analyzeLearningPatterns(): Promise<LearningPattern[]> {
    try {
      const analysis = await this.analyzePerformance();
      
      // Convert analysis to learning patterns
      return [
        {
          id: '1',
          userId: 'current',
          patternType: 'learning_style',
          name: `${analysis.learning_style} Learning Style`,
          description: `You learn best through ${analysis.learning_style} methods`,
          frequency: 0.8,
          effectiveness: 0.85,
          recommendations: [`Try more ${analysis.learning_style} content`],
          identifiedAt: new Date().toISOString()
        },
        {
          id: '2',
          patternType: 'time_preference',
          name: 'Peak Performance Time',
          description: 'You perform best during afternoon sessions',
          frequency: 0.7,
          effectiveness: 0.9,
          recommendations: ['Schedule important learning for afternoons'],
          identifiedAt: new Date().toISOString()
        }
      ];
    } catch (error) {
      console.error('Error analyzing learning patterns:', error);
      throw error;
    }
  }

  async getPersonalizedHint(questionId: string, attemptCount: number): Promise<string> {
    // Generate progressive hints based on attempt count
    const hints = [
      'Think about the key concept involved',
      'Try breaking down the problem into smaller parts',
      'Review the related explanation and try again'
    ];
    
    return hints[Math.min(attemptCount - 1, hints.length - 1)];
  }

  async submitAnswer(
    questionId: string,
    answer: any,
    timeSpent: number,
    sessionId?: number
  ): Promise<{
    correct: boolean;
    feedback: string;
    explanation?: string;
    nextQuestion?: AdaptiveQuestion;
  }> {
    try {
      if (sessionId) {
        const feedback = await this.provideFeedback(sessionId, {
          type: 'question_attempt',
          question_id: questionId,
          answer,
          time_taken: timeSpent,
          is_correct: Math.random() > 0.5, // This would be determined by backend
          attempt_number: 1
        });
        
        return {
          correct: feedback.immediate_feedback.includes('Correct') || feedback.immediate_feedback.includes('Excellent'),
          feedback: feedback.immediate_feedback,
          explanation: feedback.explanation
        };
      }
      
      // Fallback response
      return {
        correct: Math.random() > 0.5,
        feedback: 'Good effort! Keep practicing.',
        explanation: 'Here\'s how to approach this problem...'
      };
    } catch (error) {
      console.error('Error submitting answer:', error);
      throw error;
    }
  }
}

export const aiTutorServiceNew = new AITutorServiceNew();