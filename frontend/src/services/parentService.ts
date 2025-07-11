import api from './api';
import {
  FamilyResponse,
  FamilyMemberResponse,
  DashboardData,
  ParentQuestResponse,
  FamilyReportResponse,
  ParentNotificationResponse,
  FamilySettings,
  ActivityMonitoringResponse,
  CreateFamilyRequest,
  InviteFamilyMemberRequest,
  CreateParentQuestRequest,
  UpdateParentQuestRequest,
  GenerateReportRequest,
  UpdateSettingsRequest
} from '../types/family';
import { mockDelay } from '../utils/mockHelpers';

// Types
interface DashboardData {
  parentId: string;
  parentName: string;
  children: ChildSummary[];
  notifications: number;
  lastUpdated: Date;
}

interface ChildSummary {
  id: string;
  name: string;
  avatar: string;
  level: number;
  xp: number;
  streakDays: number;
  lastActive: Date;
  todayProgress: number;
}

interface ChildProfile {
  id: string;
  name: string;
  avatar: string;
  age: number;
  grade: string;
  level: number;
  xp: number;
  totalXP: number;
  streakDays: number;
  joinDate: Date;
  lastActive: Date;
  interests: string[];
  strengths: string[];
  areasForImprovement: string[];
}

interface Activity {
  id: string;
  childId: string;
  type: 'quest' | 'lesson' | 'challenge' | 'achievement';
  title: string;
  description: string;
  timestamp: Date;
  duration: number;
  xpEarned: number;
  status: 'completed' | 'in-progress' | 'failed';
  subject?: string;
  difficulty?: string;
}

interface ActivityFilters {
  type?: string;
  dateFrom?: Date;
  dateTo?: Date;
  status?: string;
  subject?: string;
}

interface ProgressData {
  childId: string;
  timeRange: string;
  dailyProgress: DailyProgress[];
  subjectProgress: SubjectProgress[];
  overallGrowth: number;
  averageSessionTime: number;
  totalXPEarned: number;
}

interface DailyProgress {
  date: Date;
  xpEarned: number;
  lessonsCompleted: number;
  timeSpent: number;
  subjects: string[];
}

interface SubjectProgress {
  subject: string;
  level: number;
  xp: number;
  mastery: number;
  recentActivities: number;
}

interface LearningStats {
  childId: string;
  currentStreak: number;
  todayXP: number;
  weeklyXP: number;
  monthlyXP: number;
  favoriteSubject: string;
  averageAccuracy: number;
  lessonsToday: number;
  timeSpentToday: number;
  activeNow: boolean;
  currentActivity?: string;
}

interface AIInsight {
  id: string;
  childId: string;
  type: 'strength' | 'improvement' | 'recommendation' | 'milestone';
  title: string;
  description: string;
  actionable: boolean;
  priority: 'high' | 'medium' | 'low';
  createdAt: Date;
  relatedSubject?: string;
}

interface Achievement {
  id: string;
  childId: string;
  title: string;
  description: string;
  icon: string;
  category: string;
  unlockedAt: Date;
  xpReward: number;
  rarity: 'common' | 'rare' | 'epic' | 'legendary';
  progress?: number;
  maxProgress?: number;
}

interface ParentNotification {
  id: string;
  type: 'achievement' | 'milestone' | 'alert' | 'message' | 'approval';
  title: string;
  message: string;
  childId?: string;
  childName?: string;
  timestamp: Date;
  read: boolean;
  priority: 'high' | 'normal' | 'low';
  actionRequired?: boolean;
  actionType?: string;
  actionData?: any;
}

interface ParentalControls {
  screenTimeLimit: number;
  allowedHours: { start: string; end: string };
  contentFilters: string[];
  subjectRestrictions: string[];
  socialFeatures: boolean;
  purchaseApproval: boolean;
  difficultyLevel: 'auto' | 'easy' | 'medium' | 'hard';
}

interface LearningGoal {
  id: string;
  childId: string;
  title: string;
  description: string;
  targetDate: Date;
  subject?: string;
  targetXP?: number;
  targetLessons?: number;
  progress: number;
  status: 'active' | 'completed' | 'paused';
}

// Mock data generators
const generateMockChildren = (): ChildSummary[] => [
  {
    id: 'child-1',
    name: 'Emma',
    avatar: '/avatars/emma.png',
    level: 12,
    xp: 2450,
    streakDays: 7,
    lastActive: new Date(Date.now() - 1000 * 60 * 30),
    todayProgress: 75,
  },
  {
    id: 'child-2',
    name: 'Lucas',
    avatar: '/avatars/lucas.png',
    level: 8,
    xp: 1820,
    streakDays: 3,
    lastActive: new Date(Date.now() - 1000 * 60 * 60 * 2),
    todayProgress: 45,
  },
];

const generateMockActivities = (childId: string): Activity[] => [
  {
    id: 'act-1',
    childId,
    type: 'quest',
    title: 'Math Adventure: Fractions',
    description: 'Completed the fractions quest with 95% accuracy',
    timestamp: new Date(Date.now() - 1000 * 60 * 60),
    duration: 25,
    xpEarned: 150,
    status: 'completed',
    subject: 'Mathematics',
    difficulty: 'medium',
  },
  {
    id: 'act-2',
    childId,
    type: 'lesson',
    title: 'Science Basics: Solar System',
    description: 'Learned about planets and their characteristics',
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 3),
    duration: 30,
    xpEarned: 100,
    status: 'completed',
    subject: 'Science',
    difficulty: 'easy',
  },
  {
    id: 'act-3',
    childId,
    type: 'challenge',
    title: 'Weekly Math Challenge',
    description: 'Currently attempting the weekly math challenge',
    timestamp: new Date(Date.now() - 1000 * 60 * 20),
    duration: 15,
    xpEarned: 0,
    status: 'in-progress',
    subject: 'Mathematics',
    difficulty: 'hard',
  },
];

// API Functions

// Dashboard data fetching
export const getParentDashboard = async (): Promise<DashboardData> => {
  await mockDelay();
  
  return {
    parentId: 'parent-123',
    parentName: 'Sarah Johnson',
    children: generateMockChildren(),
    notifications: 3,
    lastUpdated: new Date(),
  };
};

export const getChildProfile = async (childId: string): Promise<ChildProfile> => {
  await mockDelay();
  
  const mockProfiles: Record<string, ChildProfile> = {
    'child-1': {
      id: 'child-1',
      name: 'Emma',
      avatar: '/avatars/emma.png',
      age: 10,
      grade: '5th Grade',
      level: 12,
      xp: 2450,
      totalXP: 8500,
      streakDays: 7,
      joinDate: new Date('2024-01-15'),
      lastActive: new Date(Date.now() - 1000 * 60 * 30),
      interests: ['Science', 'Art', 'Puzzles'],
      strengths: ['Mathematics', 'Problem Solving'],
      areasForImprovement: ['Reading Comprehension', 'Writing'],
    },
    'child-2': {
      id: 'child-2',
      name: 'Lucas',
      avatar: '/avatars/lucas.png',
      age: 8,
      grade: '3rd Grade',
      level: 8,
      xp: 1820,
      totalXP: 5200,
      streakDays: 3,
      joinDate: new Date('2024-02-20'),
      lastActive: new Date(Date.now() - 1000 * 60 * 60 * 2),
      interests: ['Dinosaurs', 'Space', 'Building'],
      strengths: ['Science', 'Creativity'],
      areasForImprovement: ['Mathematics', 'Focus'],
    },
  };
  
  return mockProfiles[childId] || mockProfiles['child-1'];
};

export const getChildActivities = async (
  childId: string,
  filters?: ActivityFilters
): Promise<Activity[]> => {
  await mockDelay();
  
  let activities = generateMockActivities(childId);
  
  // Apply filters
  if (filters) {
    if (filters.type) {
      activities = activities.filter(a => a.type === filters.type);
    }
    if (filters.status) {
      activities = activities.filter(a => a.status === filters.status);
    }
    if (filters.subject) {
      activities = activities.filter(a => a.subject === filters.subject);
    }
    if (filters.dateFrom) {
      activities = activities.filter(a => a.timestamp >= filters.dateFrom!);
    }
    if (filters.dateTo) {
      activities = activities.filter(a => a.timestamp <= filters.dateTo!);
    }
  }
  
  return activities;
};

export const getChildProgress = async (
  childId: string,
  timeRange: 'week' | 'month' | 'year'
): Promise<ProgressData> => {
  await mockDelay();
  
  const generateDailyProgress = (days: number): DailyProgress[] => {
    const progress: DailyProgress[] = [];
    for (let i = 0; i < days; i++) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      progress.push({
        date,
        xpEarned: Math.floor(Math.random() * 200) + 50,
        lessonsCompleted: Math.floor(Math.random() * 5) + 1,
        timeSpent: Math.floor(Math.random() * 90) + 30,
        subjects: ['Mathematics', 'Science', 'Reading'].filter(() => Math.random() > 0.5),
      });
    }
    return progress.reverse();
  };
  
  const days = timeRange === 'week' ? 7 : timeRange === 'month' ? 30 : 365;
  
  return {
    childId,
    timeRange,
    dailyProgress: generateDailyProgress(days),
    subjectProgress: [
      { subject: 'Mathematics', level: 5, xp: 1200, mastery: 78, recentActivities: 15 },
      { subject: 'Science', level: 4, xp: 980, mastery: 65, recentActivities: 12 },
      { subject: 'Reading', level: 6, xp: 1450, mastery: 82, recentActivities: 20 },
      { subject: 'Writing', level: 3, xp: 650, mastery: 45, recentActivities: 8 },
    ],
    overallGrowth: 15.5,
    averageSessionTime: 45,
    totalXPEarned: days * 125,
  };
};

// Monitoring functions
export const getChildLearningStats = async (childId: string): Promise<LearningStats> => {
  await mockDelay();
  
  return {
    childId,
    currentStreak: 7,
    todayXP: 250,
    weeklyXP: 1450,
    monthlyXP: 5200,
    favoriteSubject: 'Mathematics',
    averageAccuracy: 85.5,
    lessonsToday: 3,
    timeSpentToday: 65,
    activeNow: Math.random() > 0.5,
    currentActivity: Math.random() > 0.5 ? 'Math Quest: Geometry Basics' : undefined,
  };
};

export const getAIInsights = async (childId: string): Promise<AIInsight[]> => {
  await mockDelay();
  
  return [
    {
      id: 'insight-1',
      childId,
      type: 'strength',
      title: 'Mathematical Problem Solving',
      description: 'Emma shows exceptional problem-solving skills in mathematics, completing challenges 40% faster than average.',
      actionable: true,
      priority: 'high',
      createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24),
      relatedSubject: 'Mathematics',
    },
    {
      id: 'insight-2',
      childId,
      type: 'improvement',
      title: 'Reading Comprehension Focus',
      description: 'Consider more reading exercises. Performance dips after 20 minutes of reading activities.',
      actionable: true,
      priority: 'medium',
      createdAt: new Date(Date.now() - 1000 * 60 * 60 * 48),
      relatedSubject: 'Reading',
    },
    {
      id: 'insight-3',
      childId,
      type: 'recommendation',
      title: 'Try Science Experiments',
      description: 'Based on recent interests, hands-on science experiments could boost engagement.',
      actionable: true,
      priority: 'low',
      createdAt: new Date(Date.now() - 1000 * 60 * 60 * 72),
      relatedSubject: 'Science',
    },
  ];
};

export const getChildAchievements = async (childId: string): Promise<Achievement[]> => {
  await mockDelay();
  
  return [
    {
      id: 'ach-1',
      childId,
      title: 'Math Wizard',
      description: 'Complete 50 math lessons',
      icon: '🧙‍♂️',
      category: 'Mathematics',
      unlockedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 2),
      xpReward: 500,
      rarity: 'rare',
    },
    {
      id: 'ach-2',
      childId,
      title: '7 Day Streak',
      description: 'Learn for 7 days in a row',
      icon: '🔥',
      category: 'Consistency',
      unlockedAt: new Date(Date.now() - 1000 * 60 * 60 * 6),
      xpReward: 300,
      rarity: 'common',
    },
    {
      id: 'ach-3',
      childId,
      title: 'Science Explorer',
      description: 'Complete all solar system lessons',
      icon: '🚀',
      category: 'Science',
      unlockedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 5),
      xpReward: 400,
      rarity: 'epic',
      progress: 8,
      maxProgress: 10,
    },
  ];
};

// Communication
export const getParentNotifications = async (): Promise<ParentNotification[]> => {
  await mockDelay();
  
  return [
    {
      id: 'notif-1',
      type: 'achievement',
      title: 'Emma earned a new achievement!',
      message: 'Emma just unlocked "Math Wizard" for completing 50 math lessons',
      childId: 'child-1',
      childName: 'Emma',
      timestamp: new Date(Date.now() - 1000 * 60 * 30),
      read: false,
      priority: 'normal',
      actionRequired: false,
    },
    {
      id: 'notif-2',
      type: 'approval',
      title: 'Quest Approval Required',
      message: 'Lucas wants to start "Advanced Science Challenge" - approval needed',
      childId: 'child-2',
      childName: 'Lucas',
      timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2),
      read: false,
      priority: 'high',
      actionRequired: true,
      actionType: 'quest-approval',
      actionData: { questId: 'quest-advanced-science' },
    },
    {
      id: 'notif-3',
      type: 'milestone',
      title: 'Weekly Progress Report',
      message: 'Your children completed 25 lessons this week!',
      timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24),
      read: true,
      priority: 'normal',
      actionRequired: false,
    },
  ];
};

export const markNotificationRead = async (notificationId: string): Promise<boolean> => {
  await mockDelay();
  
  // In a real implementation, this would update the database
  console.log(`Marking notification ${notificationId} as read`);
  return true;
};

export const sendMessageToChild = async (
  childId: string,
  message: string
): Promise<boolean> => {
  await mockDelay();
  
  // In a real implementation, this would send the message through the system
  console.log(`Sending message to child ${childId}: ${message}`);
  return true;
};

// Settings and controls
export const updateParentalControls = async (
  childId: string,
  controls: Partial<ParentalControls>
): Promise<ParentalControls> => {
  await mockDelay();
  
  // Mock current controls
  const currentControls: ParentalControls = {
    screenTimeLimit: 120, // minutes
    allowedHours: { start: '07:00', end: '20:00' },
    contentFilters: ['age-appropriate', 'educational'],
    subjectRestrictions: [],
    socialFeatures: true,
    purchaseApproval: true,
    difficultyLevel: 'auto',
  };
  
  // Merge with updates
  const updatedControls = { ...currentControls, ...controls };
  console.log(`Updating parental controls for child ${childId}:`, updatedControls);
  
  return updatedControls;
};

export const setLearningGoals = async (
  childId: string,
  goals: Partial<LearningGoal>[]
): Promise<LearningGoal[]> => {
  await mockDelay();
  
  // Create new goals with generated IDs
  const newGoals: LearningGoal[] = goals.map((goal, index) => ({
    id: `goal-${Date.now()}-${index}`,
    childId,
    title: goal.title || 'New Learning Goal',
    description: goal.description || '',
    targetDate: goal.targetDate || new Date(Date.now() + 1000 * 60 * 60 * 24 * 30),
    subject: goal.subject,
    targetXP: goal.targetXP,
    targetLessons: goal.targetLessons,
    progress: 0,
    status: 'active',
  }));
  
  console.log(`Setting learning goals for child ${childId}:`, newGoals);
  return newGoals;
};

export const approveQuest = async (questId: string, childId: string): Promise<boolean> => {
  await mockDelay();
  
  // In a real implementation, this would update the quest status in the database
  console.log(`Approving quest ${questId} for child ${childId}`);
  return true;
};

// New API-based functions
export const familyService = {
  // Family Management
  createFamily: async (data: CreateFamilyRequest): Promise<FamilyResponse> => {
    const response = await api.post<FamilyResponse>('/parent/families', data);
    return response.data;
  },

  getMyFamily: async (): Promise<FamilyResponse> => {
    const response = await api.get<FamilyResponse>('/parent/families/my');
    return response.data;
  },

  getFamilyMembers: async (familyId: number): Promise<FamilyMemberResponse[]> => {
    const response = await api.get<FamilyMemberResponse[]>(`/parent/families/${familyId}/members`);
    return response.data;
  },

  inviteFamilyMember: async (familyId: number, data: InviteFamilyMemberRequest): Promise<any> => {
    const response = await api.post(`/parent/families/${familyId}/invite`, data);
    return response.data;
  },

  // Dashboard
  getDashboard: async (): Promise<DashboardData> => {
    const response = await api.get<DashboardData>('/parent/dashboard');
    return response.data;
  },

  getRecentActivities: async (hours: number = 24, childId?: number): Promise<ActivityMonitoringResponse[]> => {
    const params = new URLSearchParams({ hours: hours.toString() });
    if (childId) params.append('child_id', childId.toString());
    
    const response = await api.get<ActivityMonitoringResponse[]>(`/parent/dashboard/activities?${params}`);
    return response.data;
  },

  // Quest Management
  createQuest: async (questData: CreateParentQuestRequest): Promise<ParentQuestResponse> => {
    const response = await api.post<ParentQuestResponse>('/parent/quests', questData);
    return response.data;
  },

  getQuests: async (filters?: { child_id?: number; is_active?: boolean; is_completed?: boolean }): Promise<ParentQuestResponse[]> => {
    const params = new URLSearchParams();
    if (filters?.child_id !== undefined) params.append('child_id', filters.child_id.toString());
    if (filters?.is_active !== undefined) params.append('is_active', filters.is_active.toString());
    if (filters?.is_completed !== undefined) params.append('is_completed', filters.is_completed.toString());
    
    const response = await api.get<ParentQuestResponse[]>(`/parent/quests?${params}`);
    return response.data;
  },

  updateQuest: async (questId: number, updateData: UpdateParentQuestRequest): Promise<ParentQuestResponse> => {
    const response = await api.put<ParentQuestResponse>(`/parent/quests/${questId}`, updateData);
    return response.data;
  },

  cancelQuest: async (questId: number): Promise<any> => {
    const response = await api.delete(`/parent/quests/${questId}`);
    return response.data;
  },

  // Reports
  generateReport: async (reportData: GenerateReportRequest): Promise<FamilyReportResponse> => {
    const response = await api.post<FamilyReportResponse>('/parent/reports', reportData);
    return response.data;
  },

  getReports: async (skip: number = 0, limit: number = 20): Promise<FamilyReportResponse[]> => {
    const response = await api.get<FamilyReportResponse[]>(`/parent/reports?skip=${skip}&limit=${limit}`);
    return response.data;
  },

  downloadReport: async (reportId: number): Promise<{ download_url: string }> => {
    const response = await api.get<{ download_url: string }>(`/parent/reports/${reportId}/download`);
    return response.data;
  },

  // Notifications
  getNotifications: async (unreadOnly: boolean = false, skip: number = 0, limit: number = 20): Promise<ParentNotificationResponse[]> => {
    const params = new URLSearchParams({
      unread_only: unreadOnly.toString(),
      skip: skip.toString(),
      limit: limit.toString()
    });
    
    const response = await api.get<ParentNotificationResponse[]>(`/parent/notifications?${params}`);
    return response.data;
  },

  markNotificationAsRead: async (notificationId: number): Promise<any> => {
    const response = await api.put(`/parent/notifications/${notificationId}/read`);
    return response.data;
  },

  // Settings
  getSettings: async (): Promise<FamilySettings> => {
    const response = await api.get<FamilySettings>('/parent/settings');
    return response.data;
  },

  updateSettings: async (settings: UpdateSettingsRequest): Promise<FamilySettings> => {
    const response = await api.put<FamilySettings>('/parent/settings', settings);
    return response.data;
  },

  // WebSocket connection for real-time monitoring
  connectToMonitoring: (familyId: number): string => {
    return `/api/v1/parent/ws/${familyId}`;
  }
};

// Export all functions as a service object for convenience
const parentService = {
  // Dashboard
  getParentDashboard,
  getChildProfile,
  getChildActivities,
  getChildProgress,
  
  // Monitoring
  getChildLearningStats,
  getAIInsights,
  getChildAchievements,
  
  // Communication
  getParentNotifications,
  markNotificationRead,
  sendMessageToChild,
  
  // Settings
  updateParentalControls,
  setLearningGoals,
  approveQuest,
  
  // New Family API
  ...familyService
};

export default parentService;