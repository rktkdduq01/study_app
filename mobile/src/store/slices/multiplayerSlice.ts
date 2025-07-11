import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';

interface Friend {
  id: number;
  username: string;
  level: number;
  character_class: string;
  status: 'online' | 'offline' | 'away';
  last_seen: string;
}

interface Guild {
  id: number;
  name: string;
  description: string;
  level: number;
  member_count: number;
  max_members: number;
  created_at: string;
}

interface ChatMessage {
  id: number;
  sender_id: number;
  sender_username: string;
  content: string;
  timestamp: string;
  type: 'text' | 'system' | 'achievement';
}

interface MultiplayerState {
  friends: Friend[];
  guild: Guild | null;
  chatMessages: ChatMessage[];
  onlineUsers: number;
  isConnected: boolean;
  isLoading: boolean;
  error: string | null;
}

const initialState: MultiplayerState = {
  friends: [],
  guild: null,
  chatMessages: [],
  onlineUsers: 0,
  isConnected: false,
  isLoading: false,
  error: null,
};

// Async thunks
export const fetchFriends = createAsyncThunk(
  'multiplayer/fetchFriends',
  async (_, { rejectWithValue }) => {
    try {
      // Mock API call
      const response = await fetch('/api/friends');
      const data = await response.json();
      return data;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to fetch friends');
    }
  }
);

export const joinGuild = createAsyncThunk(
  'multiplayer/joinGuild',
  async (guildId: number, { rejectWithValue }) => {
    try {
      // Mock API call
      const response = await fetch(`/api/guilds/${guildId}/join`, {
        method: 'POST',
      });
      const data = await response.json();
      return data;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to join guild');
    }
  }
);

export const sendChatMessage = createAsyncThunk(
  'multiplayer/sendChatMessage',
  async (message: string, { rejectWithValue }) => {
    try {
      // Mock API call
      const response = await fetch('/api/chat/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
      });
      const data = await response.json();
      return data;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to send message');
    }
  }
);

const multiplayerSlice = createSlice({
  name: 'multiplayer',
  initialState,
  reducers: {
    setConnectionStatus: (state, action: PayloadAction<boolean>) => {
      state.isConnected = action.payload;
    },
    setOnlineUsers: (state, action: PayloadAction<number>) => {
      state.onlineUsers = action.payload;
    },
    addChatMessage: (state, action: PayloadAction<ChatMessage>) => {
      state.chatMessages.push(action.payload);
      // Keep only last 100 messages
      if (state.chatMessages.length > 100) {
        state.chatMessages = state.chatMessages.slice(-100);
      }
    },
    updateFriendStatus: (
      state,
      action: PayloadAction<{ friendId: number; status: 'online' | 'offline' | 'away' }>
    ) => {
      const { friendId, status } = action.payload;
      const friend = state.friends.find(f => f.id === friendId);
      if (friend) {
        friend.status = status;
      }
    },
    clearChatMessages: (state) => {
      state.chatMessages = [];
    },
    clearError: (state) => {
      state.error = null;
    },
    resetMultiplayerState: (state) => {
      state.friends = [];
      state.guild = null;
      state.chatMessages = [];
      state.onlineUsers = 0;
      state.isConnected = false;
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch friends
      .addCase(fetchFriends.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchFriends.fulfilled, (state, action) => {
        state.isLoading = false;
        state.friends = action.payload.friends;
      })
      .addCase(fetchFriends.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      
      // Join guild
      .addCase(joinGuild.fulfilled, (state, action) => {
        state.guild = action.payload.guild;
      })
      
      // Send chat message
      .addCase(sendChatMessage.fulfilled, (state, action) => {
        state.chatMessages.push(action.payload.message);
      });
  },
});

export const {
  setConnectionStatus,
  setOnlineUsers,
  addChatMessage,
  updateFriendStatus,
  clearChatMessages,
  clearError,
  resetMultiplayerState,
} = multiplayerSlice.actions;

export default multiplayerSlice.reducer;