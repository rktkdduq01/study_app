export enum ErrorCategory {
  AUTHENTICATION = 'authentication',
  AUTHORIZATION = 'authorization',
  VALIDATION = 'validation',
  NETWORK = 'network',
  SERVER = 'server',
  BUSINESS = 'business',
  RATE_LIMIT = 'rate_limit',
  MAINTENANCE = 'maintenance'
}

export interface ErrorResponse {
  error: {
    code: string;
    message: string;
    user_message: string;
    action: string;
    category: ErrorCategory;
    status_code: number;
    request_id?: string;
    data?: {
      errors?: Array<{
        field: string;
        message: string;
        type: string;
      }>;
      user_errors?: Array<{
        field: string;
        message: string;
      }>;
      retry_after?: number;
      [key: string]: any;
    };
  };
}

export interface AppError extends Error {
  code: string;
  user_message: string;
  action: string;
  category: ErrorCategory;
  status_code: number;
  data?: any;
}

export class UserFriendlyError extends Error implements AppError {
  code: string;
  user_message: string;
  action: string;
  category: ErrorCategory;
  status_code: number;
  data?: any;

  constructor(errorResponse: ErrorResponse['error']) {
    super(errorResponse.message);
    this.name = 'UserFriendlyError';
    this.code = errorResponse.code;
    this.user_message = errorResponse.user_message;
    this.action = errorResponse.action;
    this.category = errorResponse.category;
    this.status_code = errorResponse.status_code;
    this.data = errorResponse.data;
  }
}