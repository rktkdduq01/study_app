import {
  Friend,
  FriendRequest,
  FriendSuggestion,
  FriendActivity,
  FriendInteraction,
  ChatRoom,
  ChatMessage,
  ChatParticipant,
  Guild,
  GuildMember,
  GuildEvent,
  StudyGroup,
  StudyGroupMember,
  StudyResource,
  FriendsListResponse,
  FriendRequestsResponse,
  FriendSuggestionsResponse,
  FriendActivitiesResponse,
  ChatRoomsResponse,
  ChatMessagesResponse,
  GuildsResponse,
  StudyGroupsResponse,
  FriendSearchFilters,
  GuildSearchFilters,
  SocialSettings,
  FriendshipStats,
  FriendStatus,
  OnlineStatus,
  ActivityType,
} from '../types/friend';

class FriendService {
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

  // Friend Management
  async getFriends(filters?: FriendSearchFilters, cursor?: string): Promise<FriendsListResponse> {
    const params = new URLSearchParams();
    if (cursor) params.append('cursor', cursor);
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

    return this.request<FriendsListResponse>(`/api/friends?${params}`);
  }

  async sendFriendRequest(userId: string, message?: string): Promise<FriendRequest> {
    return this.request<FriendRequest>('/api/friends/request', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, message }),
    });
  }

  async respondToFriendRequest(requestId: string, accept: boolean): Promise<void> {
    return this.request<void>(`/api/friends/request/${requestId}`, {
      method: 'PUT',
      body: JSON.stringify({ accept }),
    });
  }

  async getFriendRequests(): Promise<FriendRequestsResponse> {
    return this.request<FriendRequestsResponse>('/api/friends/requests');
  }

  async removeFriend(friendId: string): Promise<void> {
    return this.request<void>(`/api/friends/${friendId}`, {
      method: 'DELETE',
    });
  }

  async blockFriend(friendId: string): Promise<void> {
    return this.request<void>(`/api/friends/${friendId}/block`, {
      method: 'POST',
    });
  }

  async unblockFriend(friendId: string): Promise<void> {
    return this.request<void>(`/api/friends/${friendId}/unblock`, {
      method: 'POST',
    });
  }

  // Friend Suggestions
  async getFriendSuggestions(): Promise<FriendSuggestionsResponse> {
    return this.request<FriendSuggestionsResponse>('/api/friends/suggestions');
  }

  async dismissSuggestion(suggestionId: string): Promise<void> {
    return this.request<void>(`/api/friends/suggestions/${suggestionId}/dismiss`, {
      method: 'POST',
    });
  }

  // Friend Activities
  async getFriendActivities(cursor?: string): Promise<FriendActivitiesResponse> {
    const params = new URLSearchParams();
    if (cursor) params.append('cursor', cursor);
    
    return this.request<FriendActivitiesResponse>(`/api/friends/activities?${params}`);
  }

  async likeFriendActivity(activityId: string): Promise<void> {
    return this.request<void>(`/api/friends/activities/${activityId}/like`, {
      method: 'POST',
    });
  }

  async unlikeFriendActivity(activityId: string): Promise<void> {
    return this.request<void>(`/api/friends/activities/${activityId}/like`, {
      method: 'DELETE',
    });
  }

  async commentOnActivity(activityId: string, comment: string): Promise<void> {
    return this.request<void>(`/api/friends/activities/${activityId}/comment`, {
      method: 'POST',
      body: JSON.stringify({ comment }),
    });
  }

  // Chat System
  async getChatRooms(): Promise<ChatRoomsResponse> {
    return this.request<ChatRoomsResponse>('/api/chat/rooms');
  }

  async createDirectChat(userId: string): Promise<ChatRoom> {
    return this.request<ChatRoom>('/api/chat/rooms', {
      method: 'POST',
      body: JSON.stringify({ type: 'direct', participant_id: userId }),
    });
  }

  async createGroupChat(name: string, description: string, participantIds: string[]): Promise<ChatRoom> {
    return this.request<ChatRoom>('/api/chat/rooms', {
      method: 'POST',
      body: JSON.stringify({
        type: 'group',
        name,
        description,
        participant_ids: participantIds,
      }),
    });
  }

  async getChatMessages(roomId: string, cursor?: string): Promise<ChatMessagesResponse> {
    const params = new URLSearchParams();
    if (cursor) params.append('cursor', cursor);
    
    return this.request<ChatMessagesResponse>(`/api/chat/rooms/${roomId}/messages?${params}`);
  }

  async sendMessage(roomId: string, content: string, type: string = 'text', metadata?: any): Promise<ChatMessage> {
    return this.request<ChatMessage>(`/api/chat/rooms/${roomId}/messages`, {
      method: 'POST',
      body: JSON.stringify({ content, message_type: type, metadata }),
    });
  }

  async markMessagesAsRead(roomId: string, messageIds: string[]): Promise<void> {
    return this.request<void>(`/api/chat/rooms/${roomId}/read`, {
      method: 'POST',
      body: JSON.stringify({ message_ids: messageIds }),
    });
  }

  async addReaction(messageId: string, emoji: string): Promise<void> {
    return this.request<void>(`/api/chat/messages/${messageId}/reactions`, {
      method: 'POST',
      body: JSON.stringify({ emoji }),
    });
  }

  async removeReaction(messageId: string, emoji: string): Promise<void> {
    return this.request<void>(`/api/chat/messages/${messageId}/reactions`, {
      method: 'DELETE',
      body: JSON.stringify({ emoji }),
    });
  }

  // Guild System
  async getGuilds(filters?: GuildSearchFilters): Promise<GuildsResponse> {
    const params = new URLSearchParams();
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

    return this.request<GuildsResponse>(`/api/guilds?${params}`);
  }

  async createGuild(guildData: Partial<Guild>): Promise<Guild> {
    return this.request<Guild>('/api/guilds', {
      method: 'POST',
      body: JSON.stringify(guildData),
    });
  }

  async joinGuild(guildId: string, message?: string): Promise<void> {
    return this.request<void>(`/api/guilds/${guildId}/join`, {
      method: 'POST',
      body: JSON.stringify({ message }),
    });
  }

  async leaveGuild(guildId: string): Promise<void> {
    return this.request<void>(`/api/guilds/${guildId}/leave`, {
      method: 'POST',
    });
  }

  async getGuildMembers(guildId: string): Promise<GuildMember[]> {
    return this.request<GuildMember[]>(`/api/guilds/${guildId}/members`);
  }

  async inviteToGuild(guildId: string, userId: string): Promise<void> {
    return this.request<void>(`/api/guilds/${guildId}/invite`, {
      method: 'POST',
      body: JSON.stringify({ user_id: userId }),
    });
  }

  async getGuildEvents(guildId: string): Promise<GuildEvent[]> {
    return this.request<GuildEvent[]>(`/api/guilds/${guildId}/events`);
  }

  async createGuildEvent(guildId: string, eventData: Partial<GuildEvent>): Promise<GuildEvent> {
    return this.request<GuildEvent>(`/api/guilds/${guildId}/events`, {
      method: 'POST',
      body: JSON.stringify(eventData),
    });
  }

  async joinGuildEvent(eventId: string): Promise<void> {
    return this.request<void>(`/api/guild-events/${eventId}/join`, {
      method: 'POST',
    });
  }

  // Study Groups
  async getStudyGroups(): Promise<StudyGroupsResponse> {
    return this.request<StudyGroupsResponse>('/api/study-groups');
  }

  async createStudyGroup(groupData: Partial<StudyGroup>): Promise<StudyGroup> {
    return this.request<StudyGroup>('/api/study-groups', {
      method: 'POST',
      body: JSON.stringify(groupData),
    });
  }

  async joinStudyGroup(groupId: string): Promise<void> {
    return this.request<void>(`/api/study-groups/${groupId}/join`, {
      method: 'POST',
    });
  }

  async leaveStudyGroup(groupId: string): Promise<void> {
    return this.request<void>(`/api/study-groups/${groupId}/leave`, {
      method: 'POST',
    });
  }

  async getStudyGroupResources(groupId: string): Promise<StudyResource[]> {
    return this.request<StudyResource[]>(`/api/study-groups/${groupId}/resources`);
  }

  async uploadStudyResource(groupId: string, resourceData: FormData): Promise<StudyResource> {
    const token = localStorage.getItem('token');
    const response = await fetch(`${this.baseUrl}/api/study-groups/${groupId}/resources`, {
      method: 'POST',
      headers: {
        'Authorization': token ? `Bearer ${token}` : '',
      },
      body: resourceData,
    });

    if (!response.ok) {
      throw new Error(`Failed to upload resource: ${response.statusText}`);
    }

    return response.json();
  }

  // Settings
  async getSocialSettings(): Promise<SocialSettings> {
    return this.request<SocialSettings>('/api/social/settings');
  }

  async updateSocialSettings(settings: Partial<SocialSettings>): Promise<SocialSettings> {
    return this.request<SocialSettings>('/api/social/settings', {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
  }

  // Stats and Analytics
  async getFriendshipStats(): Promise<FriendshipStats> {
    return this.request<FriendshipStats>('/api/friends/stats');
  }

  async searchUsers(query: string, filters?: any): Promise<any[]> {
    const params = new URLSearchParams();
    params.append('query', query);
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          params.append(key, value.toString());
        }
      });
    }

    return this.request<any[]>(`/api/users/search?${params}`);
  }

  // Mock data methods (for development)
  async getMockFriends(): Promise<Friend[]> {
    return [
      {
        id: '1',
        user_id: 'user1',
        friend_user_id: 'friend1',
        status: FriendStatus.ACCEPTED,
        created_at: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
        updated_at: new Date().toISOString(),
        friend_character: {
          id: 'char1',
          name: '지혜로운 사라',
          avatar_url: '/avatars/sara.png',
          total_level: 25,
          class: 'Scholar',
          title: '수학 마스터',
          badge: '🏆'
        },
        online_status: OnlineStatus.ONLINE,
        last_seen: new Date().toISOString(),
        current_activity: ActivityType.STUDYING,
        activity_details: '수학 문제 풀이 중',
        location: '/student/learning/math',
        show_activity: true,
        show_online_status: true,
        allow_messages: true,
        friendship_points: 1250,
        interactions_count: 45,
        last_interaction: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
        mutual_friends_count: 8,
        mutual_achievements_count: 12,
        mutual_guilds: ['study-masters', 'math-wizards']
      },
      {
        id: '2',
        user_id: 'user1',
        friend_user_id: 'friend2',
        status: FriendStatus.ACCEPTED,
        created_at: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000).toISOString(),
        updated_at: new Date().toISOString(),
        friend_character: {
          id: 'char2',
          name: '용감한 알렉스',
          avatar_url: '/avatars/alex.png',
          total_level: 18,
          class: 'Warrior',
          title: '과학 탐험가'
        },
        online_status: OnlineStatus.AWAY,
        last_seen: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
        current_activity: ActivityType.QUEST,
        activity_details: '화학 실험 퀘스트',
        show_activity: true,
        show_online_status: true,
        allow_messages: true,
        friendship_points: 890,
        interactions_count: 23,
        last_interaction: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
        mutual_friends_count: 5,
        mutual_achievements_count: 7,
        mutual_guilds: ['science-explorers']
      },
      {
        id: '3',
        user_id: 'user1',
        friend_user_id: 'friend3',
        status: FriendStatus.ACCEPTED,
        created_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
        updated_at: new Date().toISOString(),
        friend_character: {
          id: 'char3',
          name: '창의적인 루나',
          avatar_url: '/avatars/luna.png',
          total_level: 22,
          class: 'Artist',
          title: '예술 창작자',
          badge: '🎨'
        },
        online_status: OnlineStatus.OFFLINE,
        last_seen: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
        current_activity: ActivityType.IDLE,
        show_activity: false,
        show_online_status: true,
        allow_messages: true,
        friendship_points: 520,
        interactions_count: 12,
        last_interaction: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
        mutual_friends_count: 3,
        mutual_achievements_count: 4,
        mutual_guilds: ['creative-minds']
      }
    ];
  }

  async getMockFriendRequests(): Promise<FriendRequest[]> {
    return [
      {
        id: 'req1',
        from_user_id: 'user_new1',
        to_user_id: 'user1',
        message: '안녕하세요! 같은 학교에 다니는 것 같아서 친구 신청 드립니다. 함께 공부해요!',
        status: FriendStatus.PENDING,
        created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
        expires_at: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString(),
        from_character: {
          id: 'char_new1',
          name: '호기심 많은 민지',
          avatar_url: '/avatars/minji.png',
          total_level: 15,
          class: 'Explorer',
          title: '신입 모험가'
        },
        mutual_friends_count: 2,
        suggested_reason: '같은 학교 학생'
      },
      {
        id: 'req2',
        from_user_id: 'user_new2',
        to_user_id: 'user1',
        status: FriendStatus.PENDING,
        created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
        expires_at: new Date(Date.now() + 4 * 24 * 60 * 60 * 1000).toISOString(),
        from_character: {
          id: 'char_new2',
          name: '똑똑한 준호',
          avatar_url: '/avatars/junho.png',
          total_level: 28,
          class: 'Scholar',
          title: '수학 천재'
        },
        mutual_friends_count: 4,
        suggested_reason: '공통 관심사: 수학, 과학'
      }
    ];
  }

  async getMockChatRooms(): Promise<ChatRoom[]> {
    return [
      {
        id: 'room1',
        type: 'direct',
        participants: [
          {
            user_id: 'user1',
            character_name: '나',
            role: 'member',
            joined_at: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
            last_read_at: new Date().toISOString(),
            is_online: true,
            is_typing: false,
            permissions: {
              can_send_messages: true,
              can_add_members: false,
              can_remove_members: false,
              can_edit_room: false
            }
          },
          {
            user_id: 'friend1',
            character_name: '지혜로운 사라',
            avatar_url: '/avatars/sara.png',
            role: 'member',
            joined_at: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
            last_read_at: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
            is_online: true,
            is_typing: false,
            permissions: {
              can_send_messages: true,
              can_add_members: false,
              can_remove_members: false,
              can_edit_room: false
            }
          }
        ],
        created_by: 'user1',
        created_at: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
        updated_at: new Date(Date.now() - 10 * 60 * 1000).toISOString(),
        last_message: {
          id: 'msg1',
          room_id: 'room1',
          sender_id: 'friend1',
          sender_name: '지혜로운 사라',
          sender_avatar: '/avatars/sara.png',
          content: '오늘 수학 문제 정말 어려웠어! 내일 같이 풀어볼래?',
          message_type: 'text',
          created_at: new Date(Date.now() - 10 * 60 * 1000).toISOString(),
          is_edited: false,
          is_deleted: false,
          reactions: [],
          read_by: ['friend1'],
          delivered_to: ['user1', 'friend1']
        },
        last_activity: new Date(Date.now() - 10 * 60 * 1000).toISOString(),
        is_active: true,
        is_muted: false,
        notification_level: 'all',
        total_messages: 156,
        unread_count: 1
      }
    ];
  }

  async getMockStudyGroups(): Promise<StudyGroup[]> {
    return [
      {
        id: 'group1',
        name: '수학 마스터즈',
        description: '중학교 수학을 함께 정복하는 스터디 그룹입니다.',
        subject: '수학',
        level: 'intermediate',
        members: [
          {
            user_id: 'user1',
            character_name: '나',
            role: 'member',
            joined_at: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString(),
            attendance_rate: 85,
            study_hours: 24,
            topics_mastered: 8,
            contribution_score: 420,
            is_active: true,
            last_activity: new Date().toISOString()
          },
          {
            user_id: 'friend1',
            character_name: '지혜로운 사라',
            avatar_url: '/avatars/sara.png',
            role: 'leader',
            joined_at: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
            attendance_rate: 95,
            study_hours: 45,
            topics_mastered: 12,
            contribution_score: 850,
            is_active: true,
            last_activity: new Date(Date.now() - 30 * 60 * 1000).toISOString()
          }
        ],
        max_members: 8,
        leader_id: 'friend1',
        schedule: {
          days: ['monday', 'wednesday', 'friday'],
          start_time: '19:00',
          end_time: '20:30',
          timezone: 'Asia/Seoul',
          duration_weeks: 12
        },
        topics: ['대수', '기하', '확률과 통계', '함수'],
        resources: [],
        progress: {
          current_topic: 2,
          topics_completed: 8,
          total_study_hours: 156
        },
        is_private: false,
        requires_approval: true,
        study_method: 'collaborative',
        status: 'active',
        created_at: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
        updated_at: new Date().toISOString()
      }
    ];
  }
}

export const friendService = new FriendService();
export default friendService;