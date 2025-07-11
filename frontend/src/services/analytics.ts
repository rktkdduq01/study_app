import axios from 'axios';
import { API_BASE_URL } from '../config';

const analyticsAPI = axios.create({
  baseURL: `${API_BASE_URL}/analytics`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
analyticsAPI.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export const analyticsService = {
  // Event tracking
  trackEvent: (eventData: {
    event_name: string;
    event_category: string;
    session_id?: string;
    properties?: any;
  }) => analyticsAPI.post('/track/event', eventData),

  // Activity tracking
  trackActivity: (activityData: {
    activity_type: string;
    activity_data?: any;
    duration_seconds?: number;
  }) => analyticsAPI.post('/track/activity', activityData),

  // Learning progress tracking
  trackProgress: (progressData: {
    subject_id: number;
    content_id?: number;
    quest_id?: number;
    progress_percentage: number;
    time_spent: number;
    score?: number;
    completed?: boolean;
  }) => analyticsAPI.post('/track/progress', progressData),

  // Get analytics data
  getUserAnalytics: (params?: {
    start_date?: string;
    end_date?: string;
  }) => analyticsAPI.get('/user/me', { params }),

  getSpecificUserAnalytics: (userId: number, params?: {
    start_date?: string;
    end_date?: string;
  }) => analyticsAPI.get(`/user/${userId}`, { params }),

  getContentEffectiveness: (contentId: number) => 
    analyticsAPI.get(`/content/${contentId}/effectiveness`),

  getGlobalAnalytics: (params?: {
    start_date?: string;
    end_date?: string;
  }) => analyticsAPI.get('/global', { params }),

  getRealtimeMetrics: () => analyticsAPI.get('/real-time'),

  getDashboardSummary: () => analyticsAPI.get('/dashboard/summary'),

  getLeaderboard: (params?: {
    metric?: string;
    period?: string;
    limit?: number;
  }) => analyticsAPI.get('/leaderboard', { params }),

  // Report generation
  generateReport: (params: {
    report_type: string;
    start_date: string;
    end_date: string;
    filters?: any;
  }) => analyticsAPI.post('/report/generate', null, { params }),

  exportAnalytics: (params: {
    format: string;
    report_type: string;
    start_date: string;
    end_date: string;
  }) => analyticsAPI.get('/export', { 
    params,
    responseType: params.format === 'csv' ? 'blob' : 'json'
  }),

  // Realtime metrics
  getRealtimeMetrics: () => analyticsAPI.get('/realtime'),
};

// Also export the axios instance for direct use
export { analyticsAPI };

// Auto-track certain events
export const autoTrack = {
  pageView: (page: string) => {
    analyticsService.trackEvent({
      event_name: 'page_view',
      event_category: 'navigation',
      properties: { page }
    });
  },

  buttonClick: (buttonName: string, location: string) => {
    analyticsService.trackEvent({
      event_name: 'button_click',
      event_category: 'interaction',
      properties: { button_name: buttonName, location }
    });
  },

  lessonStart: (lessonId: number, subjectId: number) => {
    analyticsService.trackEvent({
      event_name: 'lesson_start',
      event_category: 'learning',
      properties: { lesson_id: lessonId, subject_id: subjectId }
    });
  },

  lessonComplete: (lessonId: number, score: number, timeSpent: number) => {
    analyticsService.trackEvent({
      event_name: 'lesson_complete',
      event_category: 'learning',
      properties: { 
        lesson_id: lessonId, 
        score, 
        time_spent: timeSpent 
      }
    });
  },

  questStart: (questId: number) => {
    analyticsService.trackEvent({
      event_name: 'quest_start',
      event_category: 'quest',
      properties: { quest_id: questId }
    });
  },

  questComplete: (questId: number, xpEarned: number) => {
    analyticsService.trackEvent({
      event_name: 'quest_complete',
      event_category: 'quest',
      properties: { quest_id: questId, xp_earned: xpEarned }
    });
  },

  achievementUnlock: (achievementId: number, achievementName: string) => {
    analyticsService.trackEvent({
      event_name: 'achievement_unlock',
      event_category: 'achievement',
      properties: { 
        achievement_id: achievementId,
        achievement_name: achievementName 
      }
    });
  },

  socialInteraction: (type: string, targetUserId?: number) => {
    analyticsService.trackEvent({
      event_name: `social_${type}`,
      event_category: 'social',
      properties: { 
        interaction_type: type,
        target_user_id: targetUserId 
      }
    });
  },
};

export { analyticsAPI };