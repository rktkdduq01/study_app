/**
 * Centralized logging utility for the mobile application
 */
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';
import DeviceInfo from 'react-native-device-info';

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogEntry {
  level: LogLevel;
  message: string;
  timestamp: string;
  context?: any;
  stack?: string;
  platform: string;
  deviceId?: string;
  appVersion?: string;
}

interface LoggerConfig {
  enableInProduction: boolean;
  logToConsole: boolean;
  logToFile: boolean;
  logToServer: boolean;
  serverEndpoint?: string;
  maxLogSize: number;
}

class Logger {
  private isDevelopment: boolean;
  private logBuffer: LogEntry[] = [];
  private config: LoggerConfig;
  private deviceId?: string;
  private appVersion?: string;

  constructor(config?: Partial<LoggerConfig>) {
    this.isDevelopment = __DEV__;
    this.config = {
      enableInProduction: false,
      logToConsole: __DEV__,
      logToFile: true,
      logToServer: !__DEV__,
      serverEndpoint: process.env.LOG_SERVER_ENDPOINT,
      maxLogSize: 200,
      ...config
    };

    this.initializeDeviceInfo();
  }

  private async initializeDeviceInfo() {
    try {
      this.deviceId = await DeviceInfo.getUniqueId();
      this.appVersion = DeviceInfo.getVersion();
    } catch (error) {
      // Silently fail device info initialization
    }
  }

  private shouldLog(level: LogLevel): boolean {
    if (this.isDevelopment) return true;
    if (!this.config.enableInProduction) return false;
    
    // In production, only log warnings and errors
    return level === 'warn' || level === 'error';
  }

  private formatMessage(level: LogLevel, message: string, context?: any): string {
    const timestamp = new Date().toISOString();
    let formatted = `[${timestamp}] [${level.toUpperCase()}] ${message}`;
    
    if (context) {
      formatted += ` ${JSON.stringify(context)}`;
    }
    
    return formatted;
  }

  private createLogEntry(level: LogLevel, message: string, context?: any, stack?: string): LogEntry {
    return {
      level,
      message,
      timestamp: new Date().toISOString(),
      context,
      stack,
      platform: Platform.OS,
      deviceId: this.deviceId,
      appVersion: this.appVersion
    };
  }

  private async addToBuffer(entry: LogEntry) {
    this.logBuffer.push(entry);
    
    // Keep buffer size limited
    if (this.logBuffer.length > this.config.maxLogSize) {
      this.logBuffer.shift();
    }

    // Save to AsyncStorage for persistence
    if (this.config.logToFile) {
      try {
        await AsyncStorage.setItem('app_logs', JSON.stringify(this.logBuffer));
      } catch (error) {
        // Silently fail storage
      }
    }
  }

  private async sendToServer(entries: LogEntry[]) {
    if (!this.config.logToServer || !this.config.serverEndpoint || entries.length === 0) {
      return;
    }

    try {
      await fetch(this.config.serverEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ logs: entries })
      });
    } catch (error) {
      // Silently fail server logging
    }
  }

  debug(message: string, context?: any) {
    if (!this.shouldLog('debug')) return;

    const entry = this.createLogEntry('debug', message, context);

    if (this.config.logToConsole && this.isDevelopment) {
      console.log(this.formatMessage('debug', message, context));
    }
    
    this.addToBuffer(entry);
  }

  info(message: string, context?: any) {
    if (!this.shouldLog('info')) return;

    const entry = this.createLogEntry('info', message, context);

    if (this.config.logToConsole && this.isDevelopment) {
      console.info(this.formatMessage('info', message, context));
    }
    
    this.addToBuffer(entry);
  }

  warn(message: string, context?: any) {
    if (!this.shouldLog('warn')) return;

    const entry = this.createLogEntry('warn', message, context);

    if (this.config.logToConsole) {
      console.warn(this.formatMessage('warn', message, context));
    }
    
    this.addToBuffer(entry);
    
    // Send warnings to server in production
    if (!this.isDevelopment) {
      this.sendToServer([entry]);
    }
  }

  error(message: string, error?: Error | any, context?: any) {
    if (!this.shouldLog('error')) return;

    const entry = this.createLogEntry(
      'error', 
      message, 
      {
        ...context,
        errorMessage: error?.message,
        errorName: error?.name
      },
      error?.stack
    );

    if (this.config.logToConsole) {
      console.error(this.formatMessage('error', message, context), error);
    }
    
    this.addToBuffer(entry);
    
    // Always send errors to server
    this.sendToServer([entry]);
  }

  // Track custom events
  track(eventName: string, properties?: any) {
    this.info(`Event: ${eventName}`, properties);
  }

  // Track screen views
  trackScreen(screenName: string, properties?: any) {
    this.info(`Screen View: ${screenName}`, properties);
  }

  // Get recent logs for debugging
  async getRecentLogs(): Promise<LogEntry[]> {
    try {
      const stored = await AsyncStorage.getItem('app_logs');
      if (stored) {
        return JSON.parse(stored);
      }
    } catch (error) {
      // Return buffer if storage fails
    }
    return [...this.logBuffer];
  }

  // Clear all logs
  async clearLogs() {
    this.logBuffer = [];
    try {
      await AsyncStorage.removeItem('app_logs');
    } catch (error) {
      // Silently fail
    }
  }

  // Flush all logs to server
  async flush() {
    if (this.logBuffer.length > 0) {
      await this.sendToServer(this.logBuffer);
      await this.clearLogs();
    }
  }

  // Configure logger at runtime
  configure(config: Partial<LoggerConfig>) {
    this.config = { ...this.config, ...config };
  }
}

// Create singleton instance
export const logger = new Logger();

// Export convenience methods
export const logDebug = (message: string, context?: any) => logger.debug(message, context);
export const logInfo = (message: string, context?: any) => logger.info(message, context);
export const logWarn = (message: string, context?: any) => logger.warn(message, context);
export const logError = (message: string, error?: Error | any, context?: any) => logger.error(message, error, context);
export const logTrack = (eventName: string, properties?: any) => logger.track(eventName, properties);
export const logScreen = (screenName: string, properties?: any) => logger.trackScreen(screenName, properties);

// Setup global error handler for React Native
if (!__DEV__) {
  const originalHandler = ErrorUtils.getGlobalHandler();
  
  ErrorUtils.setGlobalHandler((error, isFatal) => {
    logger.error(
      `${isFatal ? 'Fatal' : 'Non-fatal'} JavaScript error`, 
      error,
      { isFatal }
    );
    
    // Call original handler
    if (originalHandler) {
      originalHandler(error, isFatal);
    }
  });
}

export default logger;