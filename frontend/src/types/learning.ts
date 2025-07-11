export enum ContentType {
  VIDEO = 'video',
  TEXT = 'text',
  INTERACTIVE = 'interactive',
  QUIZ = 'quiz',
  CODING = 'coding',
  DIAGRAM = 'diagram',
  SIMULATION = 'simulation'
}

export enum QuestionType {
  MULTIPLE_CHOICE = 'multiple_choice',
  SHORT_ANSWER = 'short_answer',
  TRUE_FALSE = 'true_false',
  FILL_IN_BLANK = 'fill_in_blank',
  MATCHING = 'matching',
  ORDERING = 'ordering',
  CODING = 'coding',
  DRAWING = 'drawing'
}

export enum DifficultyLevel {
  BEGINNER = 'beginner',
  INTERMEDIATE = 'intermediate',
  ADVANCED = 'advanced'
}

export interface LearningContent {
  id: string;
  title: string;
  description: string;
  type: ContentType;
  subject: string;
  grade: number;
  difficulty: DifficultyLevel;
  estimatedTime: number; // in minutes
  objectives: string[];
  prerequisites?: string[];
  content: ContentData;
  relatedQuestions?: Question[];
  metadata?: ContentMetadata;
}

export interface ContentData {
  // For video content
  videoUrl?: string;
  thumbnailUrl?: string;
  duration?: number;
  subtitles?: SubtitleTrack[];
  
  // For text content
  text?: string;
  richText?: any; // For formatted text
  
  // For interactive content
  interactiveUrl?: string;
  interactiveData?: any;
  
  // For diagrams
  diagramData?: any;
  
  // For simulations
  simulationConfig?: any;
}

export interface SubtitleTrack {
  language: string;
  label: string;
  url: string;
}

export interface ContentMetadata {
  author?: string;
  createdAt: string;
  updatedAt: string;
  tags: string[];
  difficulty: DifficultyLevel;
  likes: number;
  views: number;
}

export interface Question {
  id: string;
  type: QuestionType;
  question: string;
  points: number;
  difficulty: DifficultyLevel;
  subject: string;
  topic: string;
  explanation?: string;
  hint?: string;
  timeLimit?: number; // in seconds
  data: QuestionData;
  validation?: ValidationRule[];
}

export interface QuestionData {
  // Multiple choice
  options?: string[];
  correctAnswer?: string | string[];
  
  // Short answer
  acceptableAnswers?: string[];
  caseSensitive?: boolean;
  
  // Fill in the blank
  blanks?: BlankData[];
  
  // Matching
  pairs?: MatchingPair[];
  
  // Ordering
  items?: string[];
  correctOrder?: number[];
  
  // Coding
  starterCode?: string;
  testCases?: TestCase[];
  language?: string;
  
  // Drawing
  canvas?: CanvasConfig;
  referenceImage?: string;
}

export interface BlankData {
  id: string;
  acceptableAnswers: string[];
  placeholder?: string;
}

export interface MatchingPair {
  left: string;
  right: string;
  id: string;
}

export interface TestCase {
  input: string;
  expectedOutput: string;
  hidden?: boolean;
}

export interface CanvasConfig {
  width: number;
  height: number;
  tools: string[];
  colors: string[];
}

export interface ValidationRule {
  type: 'required' | 'minLength' | 'maxLength' | 'pattern' | 'custom';
  value?: any;
  message: string;
}

export interface LearningProgress {
  contentId: string;
  userId: string;
  startedAt: string;
  completedAt?: string;
  progress: number; // 0-100
  timeSpent: number; // in seconds
  questionsAttempted: number;
  questionsCorrect: number;
  score?: number;
  notes?: string[];
  bookmarks?: Bookmark[];
}

export interface Bookmark {
  id: string;
  timestamp: number;
  note?: string;
  createdAt: string;
}

export interface AnswerSubmission {
  questionId: string;
  answer: any;
  timeSpent: number;
  attempts: number;
}

export interface AnswerResult {
  questionId: string;
  correct: boolean;
  score: number;
  feedback?: string;
  explanation?: string;
  correctAnswer?: any;
}