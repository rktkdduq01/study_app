import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { configureStore } from '@reduxjs/toolkit';
import LoginForm from '../LoginForm';
import authReducer from '../../../store/slices/authSlice';
import authService from '../../../services/auth';

// Mock auth service
jest.mock('../../../services/auth');

// Mock useNavigate
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate
}));

describe('LoginForm', () => {
  let store: ReturnType<typeof configureStore>;
  let user: ReturnType<typeof userEvent.setup>;

  beforeEach(() => {
    store = configureStore({
      reducer: {
        auth: authReducer
      }
    });
    user = userEvent.setup();
    jest.clearAllMocks();
  });

  const renderLoginForm = () => {
    return render(
      <Provider store={store}>
        <BrowserRouter>
          <LoginForm />
        </BrowserRouter>
      </Provider>
    );
  };

  it('should render login form elements', () => {
    renderLoginForm();

    expect(screen.getByLabelText(/사용자명 또는 이메일/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/비밀번호/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /로그인/i })).toBeInTheDocument();
    expect(screen.getByText(/계정이 없으신가요?/i)).toBeInTheDocument();
  });

  it('should show validation errors for empty fields', async () => {
    renderLoginForm();

    const submitButton = screen.getByRole('button', { name: /로그인/i });
    
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/사용자명 또는 이메일을 입력해주세요/i)).toBeInTheDocument();
      expect(screen.getByText(/비밀번호를 입력해주세요/i)).toBeInTheDocument();
    });
  });

  it('should submit form with valid data', async () => {
    const mockResponse = {
      access_token: 'mock-token',
      refresh_token: 'mock-refresh',
      token_type: 'bearer',
      user: {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        role: 'student'
      }
    };

    (authService.login as jest.Mock).mockResolvedValue(mockResponse);

    renderLoginForm();

    const usernameInput = screen.getByLabelText(/사용자명 또는 이메일/i);
    const passwordInput = screen.getByLabelText(/비밀번호/i);
    const submitButton = screen.getByRole('button', { name: /로그인/i });

    await user.type(usernameInput, 'testuser');
    await user.type(passwordInput, 'password123');
    await user.click(submitButton);

    await waitFor(() => {
      expect(authService.login).toHaveBeenCalledWith({
        username: 'testuser',
        password: 'password123'
      });
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    });
  });

  it('should display error message on login failure', async () => {
    const mockError = {
      response: {
        status: 401,
        data: {
          error: {
            code: 'AUTHENTICATION_ERROR',
            message: '잘못된 사용자명 또는 비밀번호입니다'
          }
        }
      }
    };

    (authService.login as jest.Mock).mockRejectedValue(mockError);

    renderLoginForm();

    const usernameInput = screen.getByLabelText(/사용자명 또는 이메일/i);
    const passwordInput = screen.getByLabelText(/비밀번호/i);
    const submitButton = screen.getByRole('button', { name: /로그인/i });

    await user.type(usernameInput, 'testuser');
    await user.type(passwordInput, 'wrongpassword');
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/잘못된 사용자명 또는 비밀번호입니다/i)).toBeInTheDocument();
    });
  });

  it('should toggle password visibility', async () => {
    renderLoginForm();

    const passwordInput = screen.getByLabelText(/비밀번호/i) as HTMLInputElement;
    const toggleButton = screen.getByLabelText(/비밀번호 표시/i);

    expect(passwordInput.type).toBe('password');

    await user.click(toggleButton);
    expect(passwordInput.type).toBe('text');

    await user.click(toggleButton);
    expect(passwordInput.type).toBe('password');
  });

  it('should navigate to register page when clicking register link', async () => {
    renderLoginForm();

    const registerLink = screen.getByText(/회원가입/i);
    await user.click(registerLink);

    expect(mockNavigate).toHaveBeenCalledWith('/register');
  });

  it('should disable submit button while loading', async () => {
    (authService.login as jest.Mock).mockImplementation(
      () => new Promise(resolve => setTimeout(resolve, 1000))
    );

    renderLoginForm();

    const usernameInput = screen.getByLabelText(/사용자명 또는 이메일/i);
    const passwordInput = screen.getByLabelText(/비밀번호/i);
    const submitButton = screen.getByRole('button', { name: /로그인/i });

    await user.type(usernameInput, 'testuser');
    await user.type(passwordInput, 'password123');
    await user.click(submitButton);

    expect(submitButton).toBeDisabled();
    expect(screen.getByText(/로그인 중.../i)).toBeInTheDocument();
  });

  it('should trim whitespace from inputs', async () => {
    (authService.login as jest.Mock).mockResolvedValue({
      access_token: 'token',
      refresh_token: 'refresh',
      user: { id: 1, username: 'testuser', email: 'test@example.com', role: 'student' }
    });

    renderLoginForm();

    const usernameInput = screen.getByLabelText(/사용자명 또는 이메일/i);
    const passwordInput = screen.getByLabelText(/비밀번호/i);

    await user.type(usernameInput, '  testuser  ');
    await user.type(passwordInput, '  password123  ');
    await user.click(screen.getByRole('button', { name: /로그인/i }));

    await waitFor(() => {
      expect(authService.login).toHaveBeenCalledWith({
        username: 'testuser',
        password: 'password123'
      });
    });
  });

  it('should handle Enter key submission', async () => {
    (authService.login as jest.Mock).mockResolvedValue({
      access_token: 'token',
      refresh_token: 'refresh',
      user: { id: 1, username: 'testuser', email: 'test@example.com', role: 'student' }
    });

    renderLoginForm();

    const usernameInput = screen.getByLabelText(/사용자명 또는 이메일/i);
    const passwordInput = screen.getByLabelText(/비밀번호/i);

    await user.type(usernameInput, 'testuser');
    await user.type(passwordInput, 'password123');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(authService.login).toHaveBeenCalled();
    });
  });
});