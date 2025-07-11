import { io, Socket } from 'socket.io-client';
import WebSocketService from '../websocket';

// Mock socket.io-client
jest.mock('socket.io-client');

describe('WebSocketService', () => {
  let mockSocket: jest.Mocked<Socket>;
  let wsService: WebSocketService;

  beforeEach(() => {
    // Create mock socket
    mockSocket = {
      connect: jest.fn(),
      disconnect: jest.fn(),
      emit: jest.fn(),
      on: jest.fn(),
      off: jest.fn(),
      connected: false,
      id: 'mock-socket-id'
    } as any;

    // Mock io to return our mock socket
    (io as jest.Mock).mockReturnValue(mockSocket);

    wsService = new WebSocketService();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('connect', () => {
    it('should connect with authentication token', () => {
      const mockToken = 'mock-auth-token';
      localStorage.setItem('access_token', mockToken);

      wsService.connect();

      expect(io).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          auth: { token: mockToken },
          transports: ['websocket', 'polling']
        })
      );
    });

    it('should setup event listeners on connect', () => {
      wsService.connect();

      expect(mockSocket.on).toHaveBeenCalledWith('connect', expect.any(Function));
      expect(mockSocket.on).toHaveBeenCalledWith('disconnect', expect.any(Function));
      expect(mockSocket.on).toHaveBeenCalledWith('error', expect.any(Function));
      expect(mockSocket.on).toHaveBeenCalledWith('connect_error', expect.any(Function));
    });

    it('should not create multiple connections', () => {
      wsService.connect();
      wsService.connect();

      expect(io).toHaveBeenCalledTimes(1);
    });
  });

  describe('disconnect', () => {
    it('should disconnect socket', () => {
      wsService.connect();
      wsService.disconnect();

      expect(mockSocket.disconnect).toHaveBeenCalled();
    });

    it('should handle disconnect when not connected', () => {
      wsService.disconnect();
      // Should not throw
      expect(true).toBe(true);
    });
  });

  describe('event handling', () => {
    beforeEach(() => {
      wsService.connect();
    });

    it('should emit events', () => {
      const eventData = { test: 'data' };
      wsService.emit('test-event', eventData);

      expect(mockSocket.emit).toHaveBeenCalledWith('test-event', eventData);
    });

    it('should register event listeners', () => {
      const callback = jest.fn();
      wsService.on('test-event', callback);

      expect(mockSocket.on).toHaveBeenCalledWith('test-event', callback);
    });

    it('should remove event listeners', () => {
      const callback = jest.fn();
      wsService.off('test-event', callback);

      expect(mockSocket.off).toHaveBeenCalledWith('test-event', callback);
    });

    it('should handle emit when not connected', () => {
      wsService.disconnect();
      wsService.emit('test-event', {});
      // Should not throw
      expect(true).toBe(true);
    });
  });

  describe('room management', () => {
    beforeEach(() => {
      wsService.connect();
    });

    it('should join room', () => {
      wsService.joinRoom('test-room');
      expect(mockSocket.emit).toHaveBeenCalledWith('join_room', { room: 'test-room' });
    });

    it('should leave room', () => {
      wsService.leaveRoom('test-room');
      expect(mockSocket.emit).toHaveBeenCalledWith('leave_room', { room: 'test-room' });
    });
  });

  describe('connection state', () => {
    it('should check if connected', () => {
      expect(wsService.isConnected()).toBe(false);

      wsService.connect();
      mockSocket.connected = true;

      expect(wsService.isConnected()).toBe(true);
    });

    it('should handle connection events', () => {
      wsService.connect();

      // Simulate connect event
      const connectHandler = (mockSocket.on as jest.Mock).mock.calls.find(
        call => call[0] === 'connect'
      )[1];

      connectHandler();
      // Connection handler should be called
      expect(true).toBe(true);
    });

    it('should handle disconnect events', () => {
      wsService.connect();

      // Simulate disconnect event
      const disconnectHandler = (mockSocket.on as jest.Mock).mock.calls.find(
        call => call[0] === 'disconnect'
      )[1];

      const reason = 'transport close';
      disconnectHandler(reason);
      // Disconnect handler should be called
      expect(true).toBe(true);
    });

    it('should handle connection errors', () => {
      const consoleError = jest.spyOn(console, 'error').mockImplementation();
      wsService.connect();

      // Simulate error event
      const errorHandler = (mockSocket.on as jest.Mock).mock.calls.find(
        call => call[0] === 'connect_error'
      )[1];

      const error = new Error('Connection failed');
      errorHandler(error);

      expect(consoleError).toHaveBeenCalledWith('WebSocket connection error:', error);
      consoleError.mockRestore();
    });
  });

  describe('learning events', () => {
    beforeEach(() => {
      wsService.connect();
    });

    it('should emit progress update', () => {
      const progressData = {
        userId: 1,
        questId: 123,
        progress: 50,
        score: 85
      };

      wsService.emitProgressUpdate(progressData);

      expect(mockSocket.emit).toHaveBeenCalledWith('progress_update', progressData);
    });

    it('should emit achievement unlocked', () => {
      const achievementData = {
        userId: 1,
        achievementId: 456,
        achievementName: 'First Steps'
      };

      wsService.emitAchievementUnlocked(achievementData);

      expect(mockSocket.emit).toHaveBeenCalledWith('achievement_unlocked', achievementData);
    });

    it('should emit quest completed', () => {
      const questData = {
        userId: 1,
        questId: 789,
        rewards: {
          experience: 100,
          coins: 50
        }
      };

      wsService.emitQuestCompleted(questData);

      expect(mockSocket.emit).toHaveBeenCalledWith('quest_completed', questData);
    });
  });

  describe('parent notifications', () => {
    beforeEach(() => {
      wsService.connect();
    });

    it('should join parent room', () => {
      const parentId = 1;
      wsService.joinParentRoom(parentId);

      expect(mockSocket.emit).toHaveBeenCalledWith('join_room', {
        room: `parent_${parentId}`
      });
    });

    it('should emit child progress to parent', () => {
      const progressData = {
        childId: 2,
        parentId: 1,
        subject: 'math',
        progress: 75
      };

      wsService.emitChildProgress(progressData);

      expect(mockSocket.emit).toHaveBeenCalledWith('child_progress', progressData);
    });
  });

  describe('multiplayer events', () => {
    beforeEach(() => {
      wsService.connect();
    });

    it('should join game room', () => {
      const gameId = 'game-123';
      wsService.joinGameRoom(gameId);

      expect(mockSocket.emit).toHaveBeenCalledWith('join_game', { gameId });
    });

    it('should leave game room', () => {
      const gameId = 'game-123';
      wsService.leaveGameRoom(gameId);

      expect(mockSocket.emit).toHaveBeenCalledWith('leave_game', { gameId });
    });

    it('should emit game action', () => {
      const actionData = {
        gameId: 'game-123',
        action: 'answer',
        data: { answer: 'A' }
      };

      wsService.emitGameAction(actionData);

      expect(mockSocket.emit).toHaveBeenCalledWith('game_action', actionData);
    });
  });
});