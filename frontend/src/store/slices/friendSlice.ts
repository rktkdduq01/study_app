import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import {
  Friend,
  FriendRequest,
  FriendSuggestion,
  FriendActivity,
  ChatRoom,
  ChatMessage,
  Guild,
  StudyGroup,
  SocialSettings,
  FriendshipStats,
  FriendStatus,
  OnlineStatus,
  FriendSearchFilters,
  GuildSearchFilters,
} from '../../types/friend';
import friendService from '../../services/friendService';

interface FriendState {
  // Friends
  friends: Friend[];
  friendsLoading: boolean;
  friendsError: string | null;
  friendsHasMore: boolean;
  friendsCursor: string | null;
  
  // Friend Requests
  sentRequests: FriendRequest[];
  receivedRequests: FriendRequest[];
  requestsLoading: boolean;
  requestsError: string | null;
  
  // Friend Suggestions
  suggestions: FriendSuggestion[];
  suggestionsLoading: boolean;
  suggestionsError: string | null;
  
  // Friend Activities
  activities: FriendActivity[];
  activitiesLoading: boolean;
  activitiesError: string | null;
  activitiesHasMore: boolean;
  activitiesCursor: string | null;
  
  // Chat
  chatRooms: ChatRoom[];
  activeRoomId: string | null;
  chatMessages: Record<string, ChatMessage[]>;
  chatLoading: boolean;
  chatError: string | null;
  typingUsers: Record<string, string[]>; // roomId -> user names
  
  // Guilds
  guilds: Guild[];
  myGuilds: Guild[];
  recommendedGuilds: Guild[];
  guildsLoading: boolean;
  guildsError: string | null;
  
  // Study Groups
  studyGroups: StudyGroup[];
  myStudyGroups: StudyGroup[];
  recommendedStudyGroups: StudyGroup[];
  studyGroupsLoading: boolean;
  studyGroupsError: string | null;
  
  // Settings
  socialSettings: SocialSettings | null;
  settingsLoading: boolean;
  settingsError: string | null;
  
  // Stats
  friendshipStats: FriendshipStats | null;
  statsLoading: boolean;
  
  // Search and Filters
  searchQuery: string;
  searchResults: any[];
  searchLoading: boolean;
  friendFilters: FriendSearchFilters;
  guildFilters: GuildSearchFilters;
  
  // UI State
  selectedTab: 'friends' | 'requests' | 'suggestions' | 'activities' | 'chat' | 'guilds' | 'study_groups';
  friendsPanelOpen: boolean;
  chatPanelOpen: boolean;
  selectedFriendId: string | null;
  
  // Online Status
  onlineFriends: Set<string>;
  userActivities: Record<string, { activity: string; location: string; timestamp: string }>;
}

const initialState: FriendState = {
  friends: [],
  friendsLoading: false,
  friendsError: null,
  friendsHasMore: true,
  friendsCursor: null,
  
  sentRequests: [],
  receivedRequests: [],
  requestsLoading: false,
  requestsError: null,
  
  suggestions: [],
  suggestionsLoading: false,
  suggestionsError: null,
  
  activities: [],
  activitiesLoading: false,
  activitiesError: null,
  activitiesHasMore: true,
  activitiesCursor: null,
  
  chatRooms: [],
  activeRoomId: null,
  chatMessages: {},
  chatLoading: false,
  chatError: null,
  typingUsers: {},
  
  guilds: [],
  myGuilds: [],
  recommendedGuilds: [],
  guildsLoading: false,
  guildsError: null,
  
  studyGroups: [],
  myStudyGroups: [],
  recommendedStudyGroups: [],
  studyGroupsLoading: false,
  studyGroupsError: null,
  
  socialSettings: null,
  settingsLoading: false,
  settingsError: null,
  
  friendshipStats: null,
  statsLoading: false,
  
  searchQuery: '',
  searchResults: [],
  searchLoading: false,
  friendFilters: {},
  guildFilters: {},
  
  selectedTab: 'friends',
  friendsPanelOpen: false,
  chatPanelOpen: false,
  selectedFriendId: null,
  
  onlineFriends: new Set(),
  userActivities: {},
};

// Async thunks
export const fetchFriends = createAsyncThunk(
  'friends/fetchFriends',
  async ({ filters, cursor }: { filters?: FriendSearchFilters; cursor?: string } = {}) => {
    return await friendService.getFriends(filters, cursor);
  }
);

export const sendFriendRequest = createAsyncThunk(
  'friends/sendFriendRequest',
  async ({ userId, message }: { userId: string; message?: string }) => {
    return await friendService.sendFriendRequest(userId, message);
  }
);

export const respondToFriendRequest = createAsyncThunk(
  'friends/respondToFriendRequest',
  async ({ requestId, accept }: { requestId: string; accept: boolean }) => {
    await friendService.respondToFriendRequest(requestId, accept);
    return { requestId, accept };
  }
);

export const fetchFriendRequests = createAsyncThunk(
  'friends/fetchFriendRequests',
  async () => {
    return await friendService.getFriendRequests();
  }
);

export const fetchFriendSuggestions = createAsyncThunk(
  'friends/fetchFriendSuggestions',
  async () => {
    return await friendService.getFriendSuggestions();
  }
);

export const fetchFriendActivities = createAsyncThunk(
  'friends/fetchFriendActivities',
  async ({ cursor }: { cursor?: string } = {}) => {
    return await friendService.getFriendActivities(cursor);
  }
);

export const likeFriendActivity = createAsyncThunk(
  'friends/likeFriendActivity',
  async (activityId: string) => {
    await friendService.likeFriendActivity(activityId);
    return activityId;
  }
);

export const fetchChatRooms = createAsyncThunk(
  'friends/fetchChatRooms',
  async () => {
    return await friendService.getChatRooms();
  }
);

export const fetchChatMessages = createAsyncThunk(
  'friends/fetchChatMessages',
  async ({ roomId, cursor }: { roomId: string; cursor?: string }) => {
    return await friendService.getChatMessages(roomId, cursor);
  }
);

export const sendChatMessage = createAsyncThunk(
  'friends/sendChatMessage',
  async ({ roomId, content, type, metadata }: { 
    roomId: string; 
    content: string; 
    type?: string; 
    metadata?: any 
  }) => {
    return await friendService.sendMessage(roomId, content, type, metadata);
  }
);

export const fetchGuilds = createAsyncThunk(
  'friends/fetchGuilds',
  async (filters?: GuildSearchFilters) => {
    return await friendService.getGuilds(filters);
  }
);

export const joinGuild = createAsyncThunk(
  'friends/joinGuild',
  async ({ guildId, message }: { guildId: string; message?: string }) => {
    await friendService.joinGuild(guildId, message);
    return guildId;
  }
);

export const fetchStudyGroups = createAsyncThunk(
  'friends/fetchStudyGroups',
  async () => {
    return await friendService.getStudyGroups();
  }
);

export const joinStudyGroup = createAsyncThunk(
  'friends/joinStudyGroup',
  async (groupId: string) => {
    await friendService.joinStudyGroup(groupId);
    return groupId;
  }
);

export const fetchSocialSettings = createAsyncThunk(
  'friends/fetchSocialSettings',
  async () => {
    return await friendService.getSocialSettings();
  }
);

export const updateSocialSettings = createAsyncThunk(
  'friends/updateSocialSettings',
  async (settings: Partial<SocialSettings>) => {
    return await friendService.updateSocialSettings(settings);
  }
);

export const fetchFriendshipStats = createAsyncThunk(
  'friends/fetchFriendshipStats',
  async () => {
    return await friendService.getFriendshipStats();
  }
);

export const searchUsers = createAsyncThunk(
  'friends/searchUsers',
  async ({ query, filters }: { query: string; filters?: any }) => {
    return await friendService.searchUsers(query, filters);
  }
);

const friendSlice = createSlice({
  name: 'friends',
  initialState,
  reducers: {
    // UI State Management
    setSelectedTab: (state, action: PayloadAction<typeof state.selectedTab>) => {
      state.selectedTab = action.payload;
    },
    
    setFriendsPanelOpen: (state, action: PayloadAction<boolean>) => {
      state.friendsPanelOpen = action.payload;
    },
    
    setChatPanelOpen: (state, action: PayloadAction<boolean>) => {
      state.chatPanelOpen = action.payload;
    },
    
    setSelectedFriend: (state, action: PayloadAction<string | null>) => {
      state.selectedFriendId = action.payload;
    },
    
    setActiveRoom: (state, action: PayloadAction<string | null>) => {
      state.activeRoomId = action.payload;
    },
    
    // Search and Filters
    setSearchQuery: (state, action: PayloadAction<string>) => {
      state.searchQuery = action.payload;
    },
    
    setFriendFilters: (state, action: PayloadAction<FriendSearchFilters>) => {
      state.friendFilters = action.payload;
    },
    
    setGuildFilters: (state, action: PayloadAction<GuildSearchFilters>) => {
      state.guildFilters = action.payload;
    },
    
    clearSearchResults: (state) => {
      state.searchResults = [];
      state.searchQuery = '';
    },
    
    // Real-time Updates
    updateFriendOnlineStatus: (state, action: PayloadAction<{ userId: string; status: OnlineStatus; activity?: string; location?: string }>) => {
      const { userId, status, activity, location } = action.payload;
      
      // Update friend in friends list
      const friendIndex = state.friends.findIndex(f => f.friend_user_id === userId);
      if (friendIndex !== -1) {
        state.friends[friendIndex].online_status = status;
        state.friends[friendIndex].last_seen = new Date().toISOString();
        if (activity) {
          state.friends[friendIndex].current_activity = activity as any;
        }
        if (location) {
          state.friends[friendIndex].location = location;
        }
      }
      
      // Update online friends set
      if (status === OnlineStatus.ONLINE) {
        state.onlineFriends.add(userId);
      } else {
        state.onlineFriends.delete(userId);
      }
      
      // Update user activities
      if (activity && location) {
        state.userActivities[userId] = {
          activity,
          location,
          timestamp: new Date().toISOString()
        };
      }
    },
    
    addChatMessage: (state, action: PayloadAction<ChatMessage>) => {
      const message = action.payload;
      const roomId = message.room_id;
      
      if (!state.chatMessages[roomId]) {
        state.chatMessages[roomId] = [];
      }
      
      // Add message if not already exists
      const existingIndex = state.chatMessages[roomId].findIndex(m => m.id === message.id);
      if (existingIndex === -1) {
        state.chatMessages[roomId].push(message);
        
        // Update room's last message
        const roomIndex = state.chatRooms.findIndex(r => r.id === roomId);
        if (roomIndex !== -1) {
          state.chatRooms[roomIndex].last_message = message;
          state.chatRooms[roomIndex].last_activity = message.created_at;
          state.chatRooms[roomIndex].unread_count += 1;
        }
      }
    },
    
    updateTypingUsers: (state, action: PayloadAction<{ roomId: string; users: string[] }>) => {
      const { roomId, users } = action.payload;
      state.typingUsers[roomId] = users;
    },
    
    markMessagesAsRead: (state, action: PayloadAction<{ roomId: string; messageIds: string[] }>) => {
      const { roomId, messageIds } = action.payload;
      
      if (state.chatMessages[roomId]) {
        state.chatMessages[roomId].forEach(message => {
          if (messageIds.includes(message.id)) {
            // Add current user to read_by if not already there
            const currentUserId = 'user1'; // This should come from auth state
            if (!message.read_by.includes(currentUserId)) {
              message.read_by.push(currentUserId);
            }
          }
        });
      }
      
      // Reset unread count for room
      const roomIndex = state.chatRooms.findIndex(r => r.id === roomId);
      if (roomIndex !== -1) {
        state.chatRooms[roomIndex].unread_count = 0;
      }
    },
    
    // Friend Management
    removeFriend: (state, action: PayloadAction<string>) => {
      const friendId = action.payload;
      state.friends = state.friends.filter(f => f.id !== friendId);
    },
    
    updateFriendship: (state, action: PayloadAction<{ friendId: string; updates: Partial<Friend> }>) => {
      const { friendId, updates } = action.payload;
      const friendIndex = state.friends.findIndex(f => f.id === friendId);
      if (friendIndex !== -1) {
        state.friends[friendIndex] = { ...state.friends[friendIndex], ...updates };
      }
    },
    
    // Activities
    updateActivityLike: (state, action: PayloadAction<{ activityId: string; liked: boolean }>) => {
      const { activityId, liked } = action.payload;
      const activityIndex = state.activities.findIndex(a => a.id === activityId);
      if (activityIndex !== -1) {
        const activity = state.activities[activityIndex];
        if (liked) {
          activity.likes_count += 1;
          activity.user_liked = true;
        } else {
          activity.likes_count = Math.max(0, activity.likes_count - 1);
          activity.user_liked = false;
        }
      }
    },
    
    addNewActivity: (state, action: PayloadAction<FriendActivity>) => {
      state.activities.unshift(action.payload);
    },
    
    // Suggestions
    dismissSuggestion: (state, action: PayloadAction<string>) => {
      const suggestionId = action.payload;
      state.suggestions = state.suggestions.filter(s => s.id !== suggestionId);
    },
    
    // Reset state
    resetFriendData: (state) => {
      return { ...initialState, socialSettings: state.socialSettings };
    },
    
    // Load mock data
    loadMockData: (state) => {
      // This will be replaced with real data loading
      state.friends = [];
      state.receivedRequests = [];
      state.chatRooms = [];
      state.studyGroups = [];
    }
  },
  
  extraReducers: (builder) => {
    // Fetch Friends
    builder.addCase(fetchFriends.pending, (state) => {
      state.friendsLoading = true;
      state.friendsError = null;
    });
    
    builder.addCase(fetchFriends.fulfilled, (state, action) => {
      state.friendsLoading = false;
      const response = action.payload;
      
      if (state.friendsCursor) {
        // Append to existing friends (pagination)
        state.friends.push(...response.friends);
      } else {
        // Replace friends (initial load)
        state.friends = response.friends;
      }
      
      state.friendsHasMore = response.has_more;
      state.friendsCursor = response.next_cursor || null;
      
      // Update online friends set
      response.friends.forEach(friend => {
        if (friend.online_status === OnlineStatus.ONLINE) {
          state.onlineFriends.add(friend.friend_user_id);
        }
      });
    });
    
    builder.addCase(fetchFriends.rejected, (state, action) => {
      state.friendsLoading = false;
      state.friendsError = action.error.message || 'Failed to fetch friends';
    });
    
    // Send Friend Request
    builder.addCase(sendFriendRequest.fulfilled, (state, action) => {
      state.sentRequests.push(action.payload);
    });
    
    // Respond to Friend Request
    builder.addCase(respondToFriendRequest.fulfilled, (state, action) => {
      const { requestId, accept } = action.payload;
      
      // Remove from received requests
      state.receivedRequests = state.receivedRequests.filter(r => r.id !== requestId);
      
      if (accept) {
        // Friend will be added via real-time update or next friends fetch
      }
    });
    
    // Fetch Friend Requests
    builder.addCase(fetchFriendRequests.pending, (state) => {
      state.requestsLoading = true;
      state.requestsError = null;
    });
    
    builder.addCase(fetchFriendRequests.fulfilled, (state, action) => {
      state.requestsLoading = false;
      state.sentRequests = action.payload.sent_requests;
      state.receivedRequests = action.payload.received_requests;
    });
    
    builder.addCase(fetchFriendRequests.rejected, (state, action) => {
      state.requestsLoading = false;
      state.requestsError = action.error.message || 'Failed to fetch friend requests';
    });
    
    // Fetch Friend Suggestions
    builder.addCase(fetchFriendSuggestions.pending, (state) => {
      state.suggestionsLoading = true;
      state.suggestionsError = null;
    });
    
    builder.addCase(fetchFriendSuggestions.fulfilled, (state, action) => {
      state.suggestionsLoading = false;
      state.suggestions = action.payload.suggestions;
    });
    
    builder.addCase(fetchFriendSuggestions.rejected, (state, action) => {
      state.suggestionsLoading = false;
      state.suggestionsError = action.error.message || 'Failed to fetch friend suggestions';
    });
    
    // Fetch Friend Activities
    builder.addCase(fetchFriendActivities.pending, (state) => {
      state.activitiesLoading = true;
      state.activitiesError = null;
    });
    
    builder.addCase(fetchFriendActivities.fulfilled, (state, action) => {
      state.activitiesLoading = false;
      const response = action.payload;
      
      if (state.activitiesCursor) {
        state.activities.push(...response.activities);
      } else {
        state.activities = response.activities;
      }
      
      state.activitiesHasMore = response.has_more;
      state.activitiesCursor = response.next_cursor || null;
    });
    
    builder.addCase(fetchFriendActivities.rejected, (state, action) => {
      state.activitiesLoading = false;
      state.activitiesError = action.error.message || 'Failed to fetch friend activities';
    });
    
    // Like Friend Activity
    builder.addCase(likeFriendActivity.fulfilled, (state, action) => {
      const activityId = action.payload;
      const activityIndex = state.activities.findIndex(a => a.id === activityId);
      if (activityIndex !== -1) {
        const activity = state.activities[activityIndex];
        activity.likes_count += 1;
        activity.user_liked = true;
      }
    });
    
    // Fetch Chat Rooms
    builder.addCase(fetchChatRooms.pending, (state) => {
      state.chatLoading = true;
      state.chatError = null;
    });
    
    builder.addCase(fetchChatRooms.fulfilled, (state, action) => {
      state.chatLoading = false;
      state.chatRooms = action.payload.rooms;
    });
    
    builder.addCase(fetchChatRooms.rejected, (state, action) => {
      state.chatLoading = false;
      state.chatError = action.error.message || 'Failed to fetch chat rooms';
    });
    
    // Fetch Chat Messages
    builder.addCase(fetchChatMessages.fulfilled, (state, action) => {
      const response = action.payload;
      const roomId = action.meta.arg.roomId;
      
      if (!state.chatMessages[roomId]) {
        state.chatMessages[roomId] = [];
      }
      
      if (action.meta.arg.cursor) {
        // Prepend older messages (pagination)
        state.chatMessages[roomId] = [...response.messages, ...state.chatMessages[roomId]];
      } else {
        // Replace messages (initial load)
        state.chatMessages[roomId] = response.messages;
      }
    });
    
    // Send Chat Message
    builder.addCase(sendChatMessage.fulfilled, (state, action) => {
      const message = action.payload;
      const roomId = message.room_id;
      
      if (!state.chatMessages[roomId]) {
        state.chatMessages[roomId] = [];
      }
      
      state.chatMessages[roomId].push(message);
      
      // Update room's last message
      const roomIndex = state.chatRooms.findIndex(r => r.id === roomId);
      if (roomIndex !== -1) {
        state.chatRooms[roomIndex].last_message = message;
        state.chatRooms[roomIndex].last_activity = message.created_at;
      }
    });
    
    // Fetch Guilds
    builder.addCase(fetchGuilds.pending, (state) => {
      state.guildsLoading = true;
      state.guildsError = null;
    });
    
    builder.addCase(fetchGuilds.fulfilled, (state, action) => {
      state.guildsLoading = false;
      state.guilds = action.payload.guilds;
      state.myGuilds = action.payload.my_guilds;
      state.recommendedGuilds = action.payload.recommended_guilds;
    });
    
    builder.addCase(fetchGuilds.rejected, (state, action) => {
      state.guildsLoading = false;
      state.guildsError = action.error.message || 'Failed to fetch guilds';
    });
    
    // Fetch Study Groups
    builder.addCase(fetchStudyGroups.pending, (state) => {
      state.studyGroupsLoading = true;
      state.studyGroupsError = null;
    });
    
    builder.addCase(fetchStudyGroups.fulfilled, (state, action) => {
      state.studyGroupsLoading = false;
      state.studyGroups = action.payload.study_groups;
      state.myStudyGroups = action.payload.my_groups;
      state.recommendedStudyGroups = action.payload.recommended_groups;
    });
    
    builder.addCase(fetchStudyGroups.rejected, (state, action) => {
      state.studyGroupsLoading = false;
      state.studyGroupsError = action.error.message || 'Failed to fetch study groups';
    });
    
    // Fetch Social Settings
    builder.addCase(fetchSocialSettings.pending, (state) => {
      state.settingsLoading = true;
      state.settingsError = null;
    });
    
    builder.addCase(fetchSocialSettings.fulfilled, (state, action) => {
      state.settingsLoading = false;
      state.socialSettings = action.payload;
    });
    
    builder.addCase(fetchSocialSettings.rejected, (state, action) => {
      state.settingsLoading = false;
      state.settingsError = action.error.message || 'Failed to fetch social settings';
    });
    
    // Update Social Settings
    builder.addCase(updateSocialSettings.fulfilled, (state, action) => {
      if (state.socialSettings) {
        state.socialSettings = { ...state.socialSettings, ...action.payload };
      }
    });
    
    // Fetch Friendship Stats
    builder.addCase(fetchFriendshipStats.pending, (state) => {
      state.statsLoading = true;
    });
    
    builder.addCase(fetchFriendshipStats.fulfilled, (state, action) => {
      state.statsLoading = false;
      state.friendshipStats = action.payload;
    });
    
    builder.addCase(fetchFriendshipStats.rejected, (state) => {
      state.statsLoading = false;
    });
    
    // Search Users
    builder.addCase(searchUsers.pending, (state) => {
      state.searchLoading = true;
    });
    
    builder.addCase(searchUsers.fulfilled, (state, action) => {
      state.searchLoading = false;
      state.searchResults = action.payload;
    });
    
    builder.addCase(searchUsers.rejected, (state) => {
      state.searchLoading = false;
      state.searchResults = [];
    });
  }
});

export const {
  setSelectedTab,
  setFriendsPanelOpen,
  setChatPanelOpen,
  setSelectedFriend,
  setActiveRoom,
  setSearchQuery,
  setFriendFilters,
  setGuildFilters,
  clearSearchResults,
  updateFriendOnlineStatus,
  addChatMessage,
  updateTypingUsers,
  markMessagesAsRead,
  removeFriend,
  updateFriendship,
  updateActivityLike,
  addNewActivity,
  dismissSuggestion,
  resetFriendData,
  loadMockData,
} = friendSlice.actions;

export default friendSlice.reducer;