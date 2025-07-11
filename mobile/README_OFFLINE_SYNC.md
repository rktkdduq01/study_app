# Offline Sync Implementation Guide

## Overview
I've implemented a comprehensive offline synchronization system for the mobile app that handles Character, Quest, and Achievement data synchronization when the device is offline.

## Installation Requirements

Before using the offline sync features, you need to install the required dependency:

```bash
npm install @react-native-community/netinfo
# or
yarn add @react-native-community/netinfo

# For iOS, you also need to run:
cd ios && pod install
```

## Features Implemented

### 1. Offline Service (`/mobile/src/services/offlineService.ts`)
- **Queue Management**: Stores offline actions in AsyncStorage
- **Auto-sync**: Automatically processes queued actions when network is restored
- **Network Monitoring**: Listens for network state changes
- **Data Persistence**: Caches data locally for offline access

### 2. Character Service Updates
- **Offline Support**: All character operations now work offline
- **Local Caching**: Character data is cached for offline access
- **Sync Methods**:
  - `updateStats()`: Stats updates are queued for sync
  - `gainExperience()`: Experience gains calculated locally
  - `equipItem()`/`unequipItem()`: Equipment changes queued
  - `getCharacter()`: Returns cached data when offline

### 3. Quest Service (`/mobile/src/services/questService.ts`)
- **Full Offline Support**: All quest operations work offline
- **Quest Management**:
  - Start quests offline
  - Update progress offline
  - Complete quests offline
- **Local Cache**: Quest list cached for offline browsing

### 4. Achievement Service (`/mobile/src/services/achievementService.ts`)
- **Offline Achievement Tracking**: 
  - Unlock achievements offline
  - Track progress offline
  - Auto-unlock when progress reaches max
- **Progress Persistence**: Achievement progress saved locally

## Usage Examples

### Check if Device is Offline
```typescript
import { isOffline } from './services/offlineService';

const checkConnection = async () => {
  const offline = await isOffline();
  if (offline) {
    console.log('Device is offline');
  }
};
```

### Manual Offline Data Save
```typescript
import { saveCharacterOffline, saveQuestProgressOffline, saveAchievementOffline } from './services/offlineService';

// Save character updates
await saveCharacterOffline(characterId, {
  stats: { strength: 10, intelligence: 15 },
  experience: { amount: 100, source: 'quest_completion' }
});

// Save quest progress
await saveQuestProgressOffline(questId, {
  progress: 50,
  updatedAt: Date.now()
});

// Save achievement unlock
await saveAchievementOffline(achievementId, {
  unlock: true,
  unlockedAt: new Date().toISOString()
});
```

### Redux Integration
The Redux slices have been updated to use the new services:

```typescript
// Fetch quests (works offline)
dispatch(fetchQuests());

// Update quest progress (queued if offline)
dispatch(updateQuestProgress({ questId: '123', progress: 75 }));

// Unlock achievement (queued if offline)
dispatch(unlockAchievement('achievement_id'));
```

## How It Works

1. **Network Detection**: The app monitors network connectivity using NetInfo
2. **Action Queuing**: When offline, actions are stored in a queue
3. **Local Updates**: UI is updated immediately using local data
4. **Auto Sync**: When network is restored, queued actions are processed
5. **Conflict Resolution**: Server response overwrites local data on sync

## Data Flow

```
User Action → Check Network
                ↓
         [If Online] → API Call → Update UI
                ↓
         [If Offline] → Queue Action → Update Local Cache → Update UI
                              ↓
                     [Network Restored] → Process Queue → Sync with Server
```

## Testing Offline Mode

1. **Android**: Enable airplane mode or disable WiFi/Mobile data
2. **iOS**: Enable airplane mode in settings
3. **Development**: Use React Native Debugger to simulate offline conditions

## Important Notes

1. **Token Storage**: Auth tokens are stored in AsyncStorage
2. **Cache Expiry**: Currently no cache expiry implemented (consider adding)
3. **Queue Persistence**: Queue survives app restarts
4. **Error Handling**: Failed sync attempts keep items in queue for retry

## Future Improvements

1. **Conflict Resolution**: Implement proper conflict resolution strategies
2. **Cache Expiry**: Add timestamp-based cache invalidation
3. **Selective Sync**: Allow users to choose what to sync
4. **Sync Status UI**: Show sync progress to users
5. **Data Compression**: Compress cached data to save storage

## Troubleshooting

### Common Issues

1. **NetInfo not found**: Make sure to install `@react-native-community/netinfo`
2. **iOS Build Failed**: Run `cd ios && pod install` after installing NetInfo
3. **Sync Not Working**: Check if auth token is valid and stored
4. **Data Not Persisting**: Verify AsyncStorage is working properly

### Debug Commands

```typescript
// View offline queue
const queue = await offlineService.getQueue();
console.log('Offline queue:', queue);

// Clear offline queue (use with caution)
await offlineService.clearQueue();

// Force sync
await offlineService.processQueue();
```