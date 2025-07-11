import NetInfo from '@react-native-community/netinfo';

class NetworkService {
  private isListening = false;

  async getCurrentNetworkStatus() {
    const state = await NetInfo.fetch();
    return {
      isConnected: state.isConnected ?? false,
      connectionType: state.type,
      isInternetReachable: state.isInternetReachable,
    };
  }

  startListening(callback: (status: any) => void) {
    if (this.isListening) return;

    const unsubscribe = NetInfo.addEventListener(state => {
      callback({
        isConnected: state.isConnected ?? false,
        connectionType: state.type,
        isInternetReachable: state.isInternetReachable,
      });
    });

    this.isListening = true;
    return unsubscribe;
  }

  async isConnected(): Promise<boolean> {
    const state = await NetInfo.fetch();
    return state.isConnected ?? false;
  }

  async hasInternetAccess(): Promise<boolean> {
    const state = await NetInfo.fetch();
    return state.isInternetReachable ?? false;
  }
}

export const networkService = new NetworkService();

export const initializeNetworkListener = async (): Promise<void> => {
  // Network listener is initialized in the NetworkContext
  console.log('Network service initialized');
};