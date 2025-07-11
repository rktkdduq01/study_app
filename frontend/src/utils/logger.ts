/**
 * Centralized logging utility for the frontend application
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogEntry {
  level: LogLevel;
  message: string;
  timestamp: string;
  context?: any;
  stack?: string;
}

class Logger {
  private isDevelopment: boolean;
  private logBuffer: LogEntry[] = [];
  private maxBufferSize: number = 100;

  constructor() {
    this.isDevelopment = process.env.NODE_ENV === 'development';
  }

  private formatMessage(level: LogLevel, message: string, context?: any): string {
    const timestamp = new Date().toISOString();
    let formatted = `[${timestamp}] [${level.toUpperCase()}] ${message}`;
    
    if (context) {
      formatted += ` ${JSON.stringify(context)}`;
    }
    
    return formatted;
  }

  private addToBuffer(entry: LogEntry) {
    this.logBuffer.push(entry);
    
    // Keep buffer size limited
    if (this.logBuffer.length > this.maxBufferSize) {
      this.logBuffer.shift();
    }
  }

  private sendToServer(entries: LogEntry[]) {
    // In production, send logs to server
    if (!this.isDevelopment && entries.length > 0) {
      // TODO: Implement actual log shipping to server
      // Example: fetch('/api/logs', { method: 'POST', body: JSON.stringify(entries) })
    }
  }

  debug(message: string, context?: any) {
    const entry: LogEntry = {
      level: 'debug',
      message,
      timestamp: new Date().toISOString(),
      context
    };

    if (this.isDevelopment) {
      console.log(this.formatMessage('debug', message, context));
    }
    
    this.addToBuffer(entry);
  }

  info(message: string, context?: any) {
    const entry: LogEntry = {
      level: 'info',
      message,
      timestamp: new Date().toISOString(),
      context
    };

    if (this.isDevelopment) {
      console.info(this.formatMessage('info', message, context));
    }
    
    this.addToBuffer(entry);
  }

  warn(message: string, context?: any) {
    const entry: LogEntry = {
      level: 'warn',
      message,
      timestamp: new Date().toISOString(),
      context
    };

    if (this.isDevelopment) {
      console.warn(this.formatMessage('warn', message, context));
    }
    
    this.addToBuffer(entry);
    
    // Send warnings to server immediately
    this.sendToServer([entry]);
  }

  error(message: string, error?: Error | any, context?: any) {
    const entry: LogEntry = {
      level: 'error',
      message,
      timestamp: new Date().toISOString(),
      context: {
        ...context,
        errorMessage: error?.message,
        errorName: error?.name
      },
      stack: error?.stack
    };

    if (this.isDevelopment) {
      console.error(this.formatMessage('error', message, context), error);
    }
    
    this.addToBuffer(entry);
    
    // Send errors to server immediately
    this.sendToServer([entry]);
  }

  // Get recent logs for debugging
  getRecentLogs(): LogEntry[] {
    return [...this.logBuffer];
  }

  // Clear log buffer
  clearLogs() {
    this.logBuffer = [];
  }

  // Flush all logs to server
  flush() {
    if (this.logBuffer.length > 0) {
      this.sendToServer(this.logBuffer);
      this.clearLogs();
    }
  }
}

// Create singleton instance
export const logger = new Logger();

// Export convenience methods
export const logDebug = (message: string, context?: any) => logger.debug(message, context);
export const logInfo = (message: string, context?: any) => logger.info(message, context);
export const logWarn = (message: string, context?: any) => logger.warn(message, context);
export const logError = (message: string, error?: Error | any, context?: any) => logger.error(message, error, context);

// Setup global error handler
if (typeof window !== 'undefined') {
  window.addEventListener('error', (event) => {
    logger.error('Unhandled error', event.error, {
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno
    });
  });

  window.addEventListener('unhandledrejection', (event) => {
    logger.error('Unhandled promise rejection', event.reason);
  });

  // Flush logs before page unload
  window.addEventListener('beforeunload', () => {
    logger.flush();
  });
}

export default logger;