import {
  MentorProfile,
  MenteeProfile,
  MentorshipRelationship,
  MentorshipSession,
  MentorshipMatch,
  MentorshipReview,
  MentorshipGoal,
  ProgressMilestone,
  ActionItem,
  MentorSearchFilters,
  MenteeSearchFilters,
  MentorListResponse,
  MenteeListResponse,
  MatchSuggestionsResponse,
  SessionScheduleResponse,
  MentorshipStats,
  PersonalMentorshipStats,
  MentorshipSettings,
  MessageTemplate,
  MentorshipStatus,
  MentorshipType,
  SessionStatus,
  SessionType,
  MentorLevel,
  MatchingCriteria,
} from '../types/mentoring';

class MentoringService {
  private baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const token = localStorage.getItem('token');
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : '',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API request failed: ${response.statusText}`);
    }

    return response.json();
  }

  // Mentor Profile Management
  async createMentorProfile(profileData: Partial<MentorProfile>): Promise<MentorProfile> {
    return this.request<MentorProfile>('/api/mentoring/mentors', {
      method: 'POST',
      body: JSON.stringify(profileData),
    });
  }

  async updateMentorProfile(profileId: string, profileData: Partial<MentorProfile>): Promise<MentorProfile> {
    return this.request<MentorProfile>(`/api/mentoring/mentors/${profileId}`, {
      method: 'PUT',
      body: JSON.stringify(profileData),
    });
  }

  async getMentorProfile(profileId: string): Promise<MentorProfile> {
    return this.request<MentorProfile>(`/api/mentoring/mentors/${profileId}`);
  }

  async getMyMentorProfile(): Promise<MentorProfile> {
    return this.request<MentorProfile>('/api/mentoring/mentors/me');
  }

  async searchMentors(filters?: MentorSearchFilters, page: number = 1, limit: number = 20): Promise<MentorListResponse> {
    const params = new URLSearchParams();
    params.append('page', page.toString());
    params.append('limit', limit.toString());
    
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          if (typeof value === 'object') {
            params.append(key, JSON.stringify(value));
          } else {
            params.append(key, value.toString());
          }
        }
      });
    }

    return this.request<MentorListResponse>(`/api/mentoring/mentors/search?${params}`);
  }

  // Mentee Profile Management
  async createMenteeProfile(profileData: Partial<MenteeProfile>): Promise<MenteeProfile> {
    return this.request<MenteeProfile>('/api/mentoring/mentees', {
      method: 'POST',
      body: JSON.stringify(profileData),
    });
  }

  async updateMenteeProfile(profileId: string, profileData: Partial<MenteeProfile>): Promise<MenteeProfile> {
    return this.request<MenteeProfile>(`/api/mentoring/mentees/${profileId}`, {
      method: 'PUT',
      body: JSON.stringify(profileData),
    });
  }

  async getMenteeProfile(profileId: string): Promise<MenteeProfile> {
    return this.request<MenteeProfile>(`/api/mentoring/mentees/${profileId}`);
  }

  async getMyMenteeProfile(): Promise<MenteeProfile> {
    return this.request<MenteeProfile>('/api/mentoring/mentees/me');
  }

  async searchMentees(filters?: MenteeSearchFilters, page: number = 1, limit: number = 20): Promise<MenteeListResponse> {
    const params = new URLSearchParams();
    params.append('page', page.toString());
    params.append('limit', limit.toString());
    
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          if (typeof value === 'object') {
            params.append(key, JSON.stringify(value));
          } else {
            params.append(key, value.toString());
          }
        }
      });
    }

    return this.request<MenteeListResponse>(`/api/mentoring/mentees/search?${params}`);
  }

  // Matching System
  async getMatchSuggestions(userType: 'mentor' | 'mentee'): Promise<MatchSuggestionsResponse> {
    return this.request<MatchSuggestionsResponse>(`/api/mentoring/matches/suggestions?type=${userType}`);
  }

  async createMatch(mentorId: string, menteeId: string, message?: string): Promise<MentorshipMatch> {
    return this.request<MentorshipMatch>('/api/mentoring/matches', {
      method: 'POST',
      body: JSON.stringify({
        mentor_id: mentorId,
        mentee_id: menteeId,
        message,
      }),
    });
  }

  async respondToMatch(matchId: string, accept: boolean, message?: string): Promise<MentorshipMatch> {
    return this.request<MentorshipMatch>(`/api/mentoring/matches/${matchId}/respond`, {
      method: 'POST',
      body: JSON.stringify({ accept, message }),
    });
  }

  async getMyMatches(): Promise<MentorshipMatch[]> {
    return this.request<MentorshipMatch[]>('/api/mentoring/matches/me');
  }

  // Mentorship Relationships
  async createMentorship(matchId: string, mentorshipData: Partial<MentorshipRelationship>): Promise<MentorshipRelationship> {
    return this.request<MentorshipRelationship>('/api/mentoring/relationships', {
      method: 'POST',
      body: JSON.stringify({ match_id: matchId, ...mentorshipData }),
    });
  }

  async getMentorship(relationshipId: string): Promise<MentorshipRelationship> {
    return this.request<MentorshipRelationship>(`/api/mentoring/relationships/${relationshipId}`);
  }

  async getMyMentorships(): Promise<MentorshipRelationship[]> {
    return this.request<MentorshipRelationship[]>('/api/mentoring/relationships/me');
  }

  async updateMentorship(relationshipId: string, updates: Partial<MentorshipRelationship>): Promise<MentorshipRelationship> {
    return this.request<MentorshipRelationship>(`/api/mentoring/relationships/${relationshipId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async endMentorship(relationshipId: string, reason: string, feedback?: string): Promise<void> {
    return this.request<void>(`/api/mentoring/relationships/${relationshipId}/end`, {
      method: 'POST',
      body: JSON.stringify({ reason, feedback }),
    });
  }

  // Goals Management
  async createGoal(mentorshipId: string, goalData: Partial<MentorshipGoal>): Promise<MentorshipGoal> {
    return this.request<MentorshipGoal>(`/api/mentoring/relationships/${mentorshipId}/goals`, {
      method: 'POST',
      body: JSON.stringify(goalData),
    });
  }

  async updateGoal(goalId: string, updates: Partial<MentorshipGoal>): Promise<MentorshipGoal> {
    return this.request<MentorshipGoal>(`/api/mentoring/goals/${goalId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async completeGoal(goalId: string, reflection: string): Promise<MentorshipGoal> {
    return this.request<MentorshipGoal>(`/api/mentoring/goals/${goalId}/complete`, {
      method: 'POST',
      body: JSON.stringify({ reflection }),
    });
  }

  async getGoals(mentorshipId: string): Promise<MentorshipGoal[]> {
    return this.request<MentorshipGoal[]>(`/api/mentoring/relationships/${mentorshipId}/goals`);
  }

  // Progress Tracking
  async createMilestone(mentorshipId: string, milestoneData: Partial<ProgressMilestone>): Promise<ProgressMilestone> {
    return this.request<ProgressMilestone>(`/api/mentoring/relationships/${mentorshipId}/milestones`, {
      method: 'POST',
      body: JSON.stringify(milestoneData),
    });
  }

  async updateMilestone(milestoneId: string, updates: Partial<ProgressMilestone>): Promise<ProgressMilestone> {
    return this.request<ProgressMilestone>(`/api/mentoring/milestones/${milestoneId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async completeMilestone(milestoneId: string, evidenceData: any, reflection: string): Promise<ProgressMilestone> {
    return this.request<ProgressMilestone>(`/api/mentoring/milestones/${milestoneId}/complete`, {
      method: 'POST',
      body: JSON.stringify({ evidence_data: evidenceData, mentee_reflection: reflection }),
    });
  }

  // Session Management
  async scheduleSession(mentorshipId: string, sessionData: Partial<MentorshipSession>): Promise<MentorshipSession> {
    return this.request<MentorshipSession>(`/api/mentoring/relationships/${mentorshipId}/sessions`, {
      method: 'POST',
      body: JSON.stringify(sessionData),
    });
  }

  async updateSession(sessionId: string, updates: Partial<MentorshipSession>): Promise<MentorshipSession> {
    return this.request<MentorshipSession>(`/api/mentoring/sessions/${sessionId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async cancelSession(sessionId: string, reason: string): Promise<void> {
    return this.request<void>(`/api/mentoring/sessions/${sessionId}/cancel`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
  }

  async rescheduleSession(sessionId: string, newStartTime: string, newEndTime: string): Promise<MentorshipSession> {
    return this.request<MentorshipSession>(`/api/mentoring/sessions/${sessionId}/reschedule`, {
      method: 'POST',
      body: JSON.stringify({ new_start_time: newStartTime, new_end_time: newEndTime }),
    });
  }

  async startSession(sessionId: string): Promise<MentorshipSession> {
    return this.request<MentorshipSession>(`/api/mentoring/sessions/${sessionId}/start`, {
      method: 'POST',
    });
  }

  async endSession(sessionId: string, sessionSummary: string, actionItems: Partial<ActionItem>[]): Promise<MentorshipSession> {
    return this.request<MentorshipSession>(`/api/mentoring/sessions/${sessionId}/end`, {
      method: 'POST',
      body: JSON.stringify({ session_summary: sessionSummary, action_items: actionItems }),
    });
  }

  async getSessionSchedule(timeframe: 'week' | 'month' = 'week'): Promise<SessionScheduleResponse> {
    return this.request<SessionScheduleResponse>(`/api/mentoring/sessions/schedule?timeframe=${timeframe}`);
  }

  async getSessions(mentorshipId: string): Promise<MentorshipSession[]> {
    return this.request<MentorshipSession[]>(`/api/mentoring/relationships/${mentorshipId}/sessions`);
  }

  // Reviews and Ratings
  async createReview(mentorshipId: string, reviewData: Partial<MentorshipReview>): Promise<MentorshipReview> {
    return this.request<MentorshipReview>(`/api/mentoring/relationships/${mentorshipId}/reviews`, {
      method: 'POST',
      body: JSON.stringify(reviewData),
    });
  }

  async getReviews(mentorId: string): Promise<MentorshipReview[]> {
    return this.request<MentorshipReview[]>(`/api/mentoring/mentors/${mentorId}/reviews`);
  }

  async reportReview(reviewId: string, reason: string): Promise<void> {
    return this.request<void>(`/api/mentoring/reviews/${reviewId}/report`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
  }

  // Statistics and Analytics
  async getMentorshipStats(): Promise<MentorshipStats> {
    return this.request<MentorshipStats>('/api/mentoring/stats');
  }

  async getPersonalStats(): Promise<PersonalMentorshipStats> {
    return this.request<PersonalMentorshipStats>('/api/mentoring/stats/personal');
  }

  // Settings
  async getSettings(): Promise<MentorshipSettings> {
    return this.request<MentorshipSettings>('/api/mentoring/settings');
  }

  async updateSettings(settings: Partial<MentorshipSettings>): Promise<MentorshipSettings> {
    return this.request<MentorshipSettings>('/api/mentoring/settings', {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
  }

  // Message Templates
  async getMessageTemplates(): Promise<MessageTemplate[]> {
    return this.request<MessageTemplate[]>('/api/mentoring/templates');
  }

  async createMessageTemplate(template: Partial<MessageTemplate>): Promise<MessageTemplate> {
    return this.request<MessageTemplate>('/api/mentoring/templates', {
      method: 'POST',
      body: JSON.stringify(template),
    });
  }

  // Action Items
  async updateActionItem(actionItemId: string, updates: Partial<ActionItem>): Promise<ActionItem> {
    return this.request<ActionItem>(`/api/mentoring/action-items/${actionItemId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async completeActionItem(actionItemId: string, notes: string): Promise<ActionItem> {
    return this.request<ActionItem>(`/api/mentoring/action-items/${actionItemId}/complete`, {
      method: 'POST',
      body: JSON.stringify({ completion_notes: notes }),
    });
  }

  // File Upload
  async uploadSessionMaterial(sessionId: string, file: File): Promise<{ url: string; filename: string }> {
    const formData = new FormData();
    formData.append('file', file);

    const token = localStorage.getItem('token');
    const response = await fetch(`${this.baseUrl}/api/mentoring/sessions/${sessionId}/materials`, {
      method: 'POST',
      headers: {
        'Authorization': token ? `Bearer ${token}` : '',
      },
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Failed to upload file: ${response.statusText}`);
    }

    return response.json();
  }

  // Mock Data Methods (for development)
  async getMockMentors(): Promise<MentorProfile[]> {
    return [
      {
        id: 'mentor1',
        user_id: 'user1',
        character_id: 'char1',
        character_name: '김선생',
        avatar_url: '/avatars/teacher-kim.png',
        bio: '15년 경력의 수학 전문 멘토입니다. 중고등학교 수학부터 대학 수학까지 폭넓게 가르치고 있습니다.',
        tagline: '수학을 재미있게, 이해하기 쉽게!',
        subjects: ['수학', '물리학', '통계학'],
        skills: ['문제 해결', '논리적 사고', '수학적 모델링'],
        certifications: ['수학교육학 석사', '교원자격증', 'SAT Math 만점'],
        achievements: ['우수멘토상 3회', '학습자 만족도 4.9/5.0', '500+ 성공 멘토링'],
        mentor_level: MentorLevel.EXPERT,
        mentoring_types: [MentorshipType.ACADEMIC, MentorshipType.SKILL],
        total_mentees: 127,
        active_mentees: 8,
        max_mentees: 10,
        mentoring_experience_years: 5,
        total_sessions_completed: 1250,
        success_rate: 94.5,
        average_rating: 4.9,
        total_reviews: 89,
        response_rate: 98.2,
        response_time_hours: 2.5,
        available_days: ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
        available_hours: { start: '09:00', end: '18:00' },
        timezone: 'Asia/Seoul',
        preferred_session_duration: 60,
        preferred_communication: ['video', 'chat', 'voice'],
        languages: ['한국어', '영어'],
        teaching_style: '체계적이고 단계별 접근',
        learning_styles_supported: ['visual', 'auditory', 'kinesthetic'],
        is_paid: true,
        hourly_rate: 50000,
        free_consultation_minutes: 30,
        is_available: true,
        is_verified: true,
        is_featured: true,
        last_active: new Date().toISOString(),
        recommendation_count: 45,
        badge_earned: ['수학마스터', '베스트멘토', '5년멘토'],
        created_at: new Date(Date.now() - 365 * 24 * 60 * 60 * 1000).toISOString(),
        updated_at: new Date().toISOString(),
      },
      {
        id: 'mentor2',
        user_id: 'user2',
        character_id: 'char2',
        character_name: '이코치',
        avatar_url: '/avatars/coach-lee.png',
        bio: '영어 학습 전문가로 회화부터 시험 준비까지 도움을 드립니다.',
        tagline: '글로벌 소통의 문을 열어드립니다!',
        subjects: ['영어', '영문법', '영어회화', 'TOEFL'],
        skills: ['언어 교육', '회화 실력 향상', '시험 전략'],
        certifications: ['TESOL', 'TOEFL 115점', '영어교육학 학사'],
        achievements: ['영어교육 우수상', '학습자 만족도 4.8/5.0', '300+ 성공 멘토링'],
        mentor_level: MentorLevel.SENIOR,
        mentoring_types: [MentorshipType.ACADEMIC, MentorshipType.SKILL, MentorshipType.CAREER],
        total_mentees: 89,
        active_mentees: 6,
        max_mentees: 8,
        mentoring_experience_years: 3,
        total_sessions_completed: 780,
        success_rate: 91.2,
        average_rating: 4.8,
        total_reviews: 67,
        response_rate: 95.8,
        response_time_hours: 4.2,
        available_days: ['monday', 'wednesday', 'friday', 'saturday', 'sunday'],
        available_hours: { start: '14:00', end: '22:00' },
        timezone: 'Asia/Seoul',
        preferred_session_duration: 45,
        preferred_communication: ['video', 'voice'],
        languages: ['한국어', '영어', '중국어'],
        teaching_style: '실용적이고 대화형 학습',
        learning_styles_supported: ['auditory', 'kinesthetic'],
        is_paid: true,
        hourly_rate: 35000,
        free_consultation_minutes: 20,
        is_available: true,
        is_verified: true,
        is_featured: false,
        last_active: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
        recommendation_count: 28,
        badge_earned: ['영어마스터', '회화전문가'],
        created_at: new Date(Date.now() - 200 * 24 * 60 * 60 * 1000).toISOString(),
        updated_at: new Date().toISOString(),
      }
    ];
  }

  async getMockMentorships(): Promise<MentorshipRelationship[]> {
    return [
      {
        id: 'mentorship1',
        mentor_id: 'mentor1',
        mentee_id: 'user1',
        type: MentorshipType.ACADEMIC,
        status: MentorshipStatus.ACTIVE,
        start_date: new Date(Date.now() - 60 * 24 * 60 * 60 * 1000).toISOString(),
        expected_duration_weeks: 16,
        goals: [
          {
            id: 'goal1',
            mentorship_id: 'mentorship1',
            title: '수학 성적 향상',
            description: '중간고사 수학 점수 80점 이상 달성',
            category: 'academic',
            priority: 'high',
            target_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
            created_date: new Date(Date.now() - 50 * 24 * 60 * 60 * 1000).toISOString(),
            is_completed: false,
            progress_percentage: 65,
            success_criteria: ['중간고사 80점 이상', '문제 해결 속도 향상', '자신감 증진'],
            measurement_method: '시험 점수 및 모의고사 결과',
            milestones: ['기본 개념 이해', '문제 유형별 연습', '실전 문제 풀이'],
            resources_needed: ['교과서', '문제집', '온라인 강의'],
            obstacles: ['시간 부족', '기초 개념 부족']
          }
        ],
        progress_milestones: [],
        overall_progress_percentage: 65,
        total_sessions_planned: 20,
        sessions_completed: 12,
        sessions_remaining: 8,
        last_session_date: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
        next_session_date: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString(),
        meeting_frequency: 'weekly',
        session_duration_minutes: 60,
        communication_preferences: ['video', 'chat'],
        ground_rules: ['시간 엄수', '과제 완료', '적극적 참여'],
        mentor_satisfaction: 4.5,
        mentee_satisfaction: 4.8,
        is_paid: true,
        total_cost: 600000,
        payment_status: 'paid',
        created_at: new Date(Date.now() - 60 * 24 * 60 * 60 * 1000).toISOString(),
        updated_at: new Date().toISOString(),
      }
    ];
  }

  async getMockSessions(): Promise<MentorshipSession[]> {
    return [
      {
        id: 'session1',
        mentorship_id: 'mentorship1',
        mentor_id: 'mentor1',
        mentee_id: 'user1',
        title: '이차함수 개념 정리',
        description: '이차함수의 기본 개념과 그래프 그리기 연습',
        type: SessionType.ONE_ON_ONE,
        status: SessionStatus.COMPLETED,
        scheduled_start: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
        scheduled_end: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000 + 60 * 60 * 1000).toISOString(),
        actual_start: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
        actual_end: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000 + 65 * 60 * 1000).toISOString(),
        duration_minutes: 60,
        meeting_type: 'video_call',
        meeting_link: 'https://zoom.us/j/123456789',
        agenda: ['이차함수 정의 복습', '그래프 그리기 연습', '문제 풀이'],
        topics_covered: ['y = ax² + bx + c 형태', '포물선의 성질', '최댓값과 최솟값'],
        resources_shared: ['이차함수 정리 노트', '연습 문제 10개'],
        homework_assigned: ['교과서 p.45-50 문제', '그래프 그리기 연습 5개'],
        session_summary: '이차함수의 기본 개념을 잘 이해했고, 그래프 그리기도 향상되었습니다.',
        mentor_notes: '학습자가 적극적으로 참여했고, 질문도 많이 했습니다.',
        mentee_notes: '어려웠던 부분이 명확해졌습니다.',
        action_items: [
          {
            id: 'action1',
            session_id: 'session1',
            assigned_to: 'mentee',
            title: '과제 완료',
            description: '교과서 문제 풀이 및 그래프 연습',
            due_date: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString(),
            priority: 'medium',
            is_completed: true,
            completion_date: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
            resources: ['교과서', '그래프 용지'],
            created_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
          }
        ],
        mentor_rating: 5,
        mentee_rating: 5,
        mentor_attended: true,
        mentee_attended: true,
        follow_up_required: false,
        next_session_topics: ['이차방정식 풀이', '판별식'],
        created_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
        updated_at: new Date().toISOString(),
      }
    ];
  }

  async getMockMatches(): Promise<MentorshipMatch[]> {
    return [
      {
        id: 'match1',
        mentor_id: 'mentor2',
        mentee_id: 'user1',
        compatibility_score: 88,
        match_criteria: [MatchingCriteria.SUBJECT_EXPERTISE, MatchingCriteria.AVAILABILITY, MatchingCriteria.COMMUNICATION_STYLE],
        match_reasons: ['영어 전문성 일치', '시간대 호환성', '학습 스타일 유사'],
        algorithm_version: 'v2.1',
        status: 'suggested',
        suggested_date: new Date().toISOString(),
        response_deadline: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
        mentor_message: '안녕하세요! 영어 학습에 도움을 드리고 싶습니다. 함께 목표를 달성해보아요!',
        subject_match_score: 95,
        schedule_match_score: 82,
        personality_match_score: 85,
        communication_match_score: 90,
        experience_match_score: 88,
        suggested_session_frequency: 'weekly',
        suggested_duration_weeks: 12,
        suggested_focus_areas: ['회화 실력', 'TOEFL 준비', '발음 교정'],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }
    ];
  }

  async getMockStats(): Promise<PersonalMentorshipStats> {
    return {
      total_mentees: 3,
      active_mentees: 1,
      completed_mentorships: 2,
      total_sessions_given: 45,
      average_mentee_rating: 4.7,
      current_mentor: 'mentor1',
      total_mentors: 1,
      total_sessions_attended: 12,
      goals_achieved: 3,
      average_mentor_rating: 4.8,
      current_goals: 2,
      completed_goals: 3,
      goal_completion_rate: 60,
      badges_earned: ['우수멘티', '목표달성자', '성실상'],
      certifications_earned: [],
      recommendations_received: 2,
      total_hours_mentored: 75,
      total_hours_received: 18,
      average_session_length: 60,
      last_session_date: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
      upcoming_sessions: 1,
      response_rate: 95,
      skill_improvements: [
        { skill: '수학', before: 60, after: 80 },
        { skill: '영어', before: 70, after: 85 }
      ],
      subject_progress: [
        { subject: '수학', improvement_percentage: 33 },
        { subject: '영어', improvement_percentage: 21 }
      ]
    };
  }
}

export const mentoringService = new MentoringService();
export default mentoringService;