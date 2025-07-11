// AI 학습 분석 및 문제 생성 관련 타입 정의

export enum LearningStyle {
  VISUAL = 'visual',        // 시각적 학습자
  AUDITORY = 'auditory',    // 청각적 학습자
  KINESTHETIC = 'kinesthetic', // 체험적 학습자
  READING_WRITING = 'reading_writing' // 읽기/쓰기 학습자
}

export enum ConceptLevel {
  INTRODUCTION = 'introduction',     // 개념 소개
  BASIC_UNDERSTANDING = 'basic',     // 기초 이해
  APPLICATION = 'application',       // 응용
  ANALYSIS = 'analysis',            // 분석
  SYNTHESIS = 'synthesis',          // 종합
  EVALUATION = 'evaluation'         // 평가
}

export enum ProblemPurpose {
  CONCEPT_CHECK = 'concept_check',           // 개념 확인
  MISCONCEPTION_DETECTION = 'misconception', // 오개념 발견
  SKILL_PRACTICE = 'skill_practice',         // 기술 연습
  CRITICAL_THINKING = 'critical_thinking',   // 비판적 사고
  CREATIVE_APPLICATION = 'creative',         // 창의적 적용
  REVIEW = 'review'                         // 복습
}

// 학생 프로필 및 학습 상태
export interface StudentLearningProfile {
  id: string;
  studentId: string;
  currentLevel: number;
  gradeLevel: number;
  learningStyle: LearningStyle;
  strengths: string[];
  weaknesses: string[];
  interests: string[];
  attentionSpan: number; // 분 단위
  preferredDifficulty: 'easy' | 'medium' | 'hard';
  learningHistory: LearningHistory[];
  conceptMastery: ConceptMastery[];
}

export interface LearningHistory {
  date: string;
  subject: string;
  topic: string;
  score: number;
  timeSpent: number;
  mistakePatterns: MistakePattern[];
}

export interface MistakePattern {
  type: string;
  frequency: number;
  lastOccurred: string;
  concept: string;
}

export interface ConceptMastery {
  concept: string;
  level: ConceptLevel;
  mastery: number; // 0-100
  lastPracticed: string;
  relatedConcepts: string[];
}

// AI 문제 생성 요청 및 응답
export interface AIQuestionRequest {
  studentProfile: StudentLearningProfile;
  subject: string;
  topic: string;
  purpose: ProblemPurpose;
  conceptLevel: ConceptLevel;
  count: number;
  constraints?: QuestionConstraints;
}

export interface QuestionConstraints {
  timeLimit?: number;
  avoidConcepts?: string[];
  focusConcepts?: string[];
  realWorldContext?: boolean;
  gamification?: boolean;
  collaborativeOption?: boolean;
}

// AI가 생성하는 문제 구조
export interface AIGeneratedQuestion {
  id: string;
  question: string;
  type: 'conceptual' | 'procedural' | 'analytical' | 'creative';
  purpose: ProblemPurpose;
  conceptsCovered: string[];
  difficulty: AdaptiveDifficulty;
  estimatedTime: number;
  
  // 단계별 학습 지원
  scaffolding: ScaffoldingStep[];
  
  // 개념 이해를 위한 구성요소
  conceptExplanation?: ConceptExplanation;
  visualAids?: VisualAid[];
  realWorldExample?: string;
  
  // 문제 데이터
  data: EnhancedQuestionData;
  
  // 적응형 힌트 시스템
  adaptiveHints: AdaptiveHint[];
  
  // 평가 및 피드백
  assessmentCriteria: AssessmentCriteria;
  feedbackStrategy: FeedbackStrategy;
}

export interface AdaptiveDifficulty {
  baseLevel: number; // 1-10
  adjustmentFactors: {
    studentPerformance: number;
    timeOfDay: number;
    previousAttempts: number;
    conceptNovelty: number;
  };
  recommendedLevel: number;
}

export interface ScaffoldingStep {
  order: number;
  type: 'guided_discovery' | 'worked_example' | 'partial_solution' | 'conceptual_bridge';
  content: string;
  triggerCondition: 'time' | 'attempts' | 'request' | 'automatic';
}

export interface ConceptExplanation {
  mainIdea: string;
  breakdown: ConceptBreakdown[];
  analogies: Analogy[];
  commonMisconceptions: Misconception[];
}

export interface ConceptBreakdown {
  part: string;
  explanation: string;
  importance: 'core' | 'supporting' | 'extension';
  visualRepresentation?: string;
}

export interface Analogy {
  concept: string;
  analogyTo: string;
  explanation: string;
  limitations?: string;
}

export interface Misconception {
  description: string;
  whyItHappens: string;
  correction: string;
  checkQuestion: string;
}

export interface VisualAid {
  type: 'diagram' | 'animation' | 'interactive' | 'infographic';
  url: string;
  description: string;
  interactionPoints?: InteractionPoint[];
}

export interface InteractionPoint {
  id: string;
  coordinates: { x: number; y: number };
  label: string;
  explanation: string;
}

export interface EnhancedQuestionData {
  // 기존 문제 데이터 + 개념 이해 강화 요소
  questionText: string;
  conceptualContext: string;
  
  // 다양한 표현 방식
  representations: {
    verbal: string;
    visual?: string;
    symbolic?: string;
    numerical?: string;
  };
  
  // 답변 옵션 (객관식의 경우)
  options?: EnhancedOption[];
  
  // 단계별 문제 해결
  solutionSteps?: SolutionStep[];
  
  // 개념 연결
  conceptConnections: ConceptConnection[];
}

export interface EnhancedOption {
  id: string;
  text: string;
  isCorrect: boolean;
  conceptualReason: string;
  ifSelected: {
    feedback: string;
    misconceptionAddressed?: string;
    followUpQuestion?: string;
  };
}

export interface SolutionStep {
  order: number;
  description: string;
  concept: string;
  hint: string;
  checkPoint?: {
    question: string;
    expectedAnswer: string;
  };
}

export interface ConceptConnection {
  fromConcept: string;
  toConcept: string;
  relationship: string;
  importance: 'essential' | 'helpful' | 'extension';
}

export interface AdaptiveHint {
  level: number; // 1-5, 점진적으로 구체적
  type: 'conceptual' | 'procedural' | 'metacognitive' | 'motivational';
  content: string;
  revealCondition: {
    afterAttempts?: number;
    afterTime?: number;
    onRequest?: boolean;
  };
  conceptReinforced: string;
}

export interface AssessmentCriteria {
  correctness: {
    weight: number;
    partial: boolean;
  };
  conceptualUnderstanding: {
    weight: number;
    indicators: string[];
  };
  processQuality: {
    weight: number;
    criteria: string[];
  };
  creativity?: {
    weight: number;
    aspects: string[];
  };
}

export interface FeedbackStrategy {
  type: 'immediate' | 'delayed' | 'adaptive';
  style: 'encouraging' | 'constructive' | 'socratic';
  components: FeedbackComponent[];
}

export interface FeedbackComponent {
  type: 'affirmation' | 'correction' | 'explanation' | 'extension' | 'reflection';
  content: string;
  visualSupport?: string;
  nextSteps?: string[];
}

// AI 학습 분석 결과
export interface LearningAnalysis {
  studentId: string;
  timestamp: string;
  
  // 개념 이해도 분석
  conceptualUnderstanding: {
    strongConcepts: ConceptStrength[];
    weakConcepts: ConceptWeakness[];
    emergingConcepts: string[];
  };
  
  // 학습 패턴 분석
  learningPatterns: {
    preferredQuestionTypes: string[];
    optimalSessionLength: number;
    bestTimeOfDay: string;
    effectiveStrategies: string[];
  };
  
  // 추천사항
  recommendations: {
    nextConcepts: string[];
    reviewNeeded: string[];
    challengeReady: string[];
    studyStrategies: StudyStrategy[];
  };
  
  // 동기부여 상태
  motivationProfile: {
    engagementLevel: number;
    confidenceLevel: number;
    frustrationPoints: string[];
    successTriggers: string[];
  };
}

export interface ConceptStrength {
  concept: string;
  masteryLevel: number;
  consistencyScore: number;
  applications: string[];
}

export interface ConceptWeakness {
  concept: string;
  masteryLevel: number;
  commonErrors: string[];
  suggestedInterventions: string[];
}

export interface StudyStrategy {
  name: string;
  description: string;
  whenToUse: string;
  expectedBenefit: string;
}

// AI 적응형 학습 경로
export interface AdaptiveLearningPath {
  studentId: string;
  subject: string;
  currentNode: LearningNode;
  completedNodes: string[];
  availableNodes: LearningNode[];
  recommendedPath: string[];
  alternativePaths: string[][];
}

export interface LearningNode {
  id: string;
  concept: string;
  prerequisites: string[];
  estimatedTime: number;
  activities: LearningActivity[];
  assessments: string[];
  masteryThreshold: number;
}

export interface LearningActivity {
  type: 'exploration' | 'practice' | 'application' | 'creation';
  title: string;
  description: string;
  concepts: string[];
  duration: number;
  adaptiveElements: AdaptiveElement[];
}

export interface AdaptiveElement {
  trigger: string;
  adaptation: string;
  purpose: string;
}