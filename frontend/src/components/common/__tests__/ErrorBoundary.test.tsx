import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ErrorBoundary from '../ErrorBoundary';

// Component that throws an error
const ThrowError = ({ shouldThrow }: { shouldThrow: boolean }) => {
  if (shouldThrow) {
    throw new Error('Test error');
  }
  return <div>No error</div>;
};

// Mock console.error to avoid cluttering test output
const originalError = console.error;
beforeAll(() => {
  console.error = jest.fn();
});

afterAll(() => {
  console.error = originalError;
});

describe('ErrorBoundary', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  it('should render children when there is no error', () => {
    render(
      <ErrorBoundary>
        <div>Test content</div>
      </ErrorBoundary>
    );

    expect(screen.getByText('Test content')).toBeInTheDocument();
  });

  it('should render error UI when child component throws', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(screen.getByText(/문제가 발생했습니다/i)).toBeInTheDocument();
    expect(screen.getByText(/Test error/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /다시 시도/i })).toBeInTheDocument();
  });

  it('should reset error state when retry button is clicked', async () => {
    const user = userEvent.setup();
    let shouldThrow = true;

    const { rerender } = render(
      <ErrorBoundary>
        <ThrowError shouldThrow={shouldThrow} />
      </ErrorBoundary>
    );

    // Verify error UI is shown
    expect(screen.getByText(/문제가 발생했습니다/i)).toBeInTheDocument();

    // Fix the error condition
    shouldThrow = false;

    // Click retry button
    const retryButton = screen.getByRole('button', { name: /다시 시도/i });
    await user.click(retryButton);

    // Re-render with fixed condition
    rerender(
      <ErrorBoundary>
        <ThrowError shouldThrow={shouldThrow} />
      </ErrorBoundary>
    );

    // Should show normal content now
    expect(screen.getByText('No error')).toBeInTheDocument();
    expect(screen.queryByText(/문제가 발생했습니다/i)).not.toBeInTheDocument();
  });

  it('should log error details', () => {
    const testError = new Error('Test error message');
    const errorInfo = { componentStack: 'Test stack trace' };

    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(console.error).toHaveBeenCalledWith(
      'ErrorBoundary caught an error:',
      expect.any(Error),
      expect.any(Object)
    );
  });

  it('should render custom fallback if provided', () => {
    const CustomFallback = () => <div>Custom error UI</div>;

    render(
      <ErrorBoundary fallback={<CustomFallback />}>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(screen.getByText('Custom error UI')).toBeInTheDocument();
    expect(screen.queryByText(/문제가 발생했습니다/i)).not.toBeInTheDocument();
  });

  it('should handle multiple errors', async () => {
    const user = userEvent.setup();

    const { rerender } = render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    // First error
    expect(screen.getByText(/문제가 발생했습니다/i)).toBeInTheDocument();

    // Click retry
    await user.click(screen.getByRole('button', { name: /다시 시도/i }));

    // Still throwing error
    rerender(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    // Should still show error UI
    expect(screen.getByText(/문제가 발생했습니다/i)).toBeInTheDocument();
  });

  it('should pass error info to onError callback if provided', () => {
    const onError = jest.fn();

    render(
      <ErrorBoundary onError={onError}>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(onError).toHaveBeenCalledWith(
      expect.any(Error),
      expect.objectContaining({
        componentStack: expect.any(String)
      })
    );
  });

  it('should not catch errors in event handlers', () => {
    const handleClick = () => {
      throw new Error('Event handler error');
    };

    const ComponentWithEventHandler = () => (
      <button onClick={handleClick}>Click me</button>
    );

    render(
      <ErrorBoundary>
        <ComponentWithEventHandler />
      </ErrorBoundary>
    );

    // Component should render normally
    expect(screen.getByRole('button', { name: /Click me/i })).toBeInTheDocument();
    
    // ErrorBoundary should not show error UI for event handler errors
    expect(screen.queryByText(/문제가 발생했습니다/i)).not.toBeInTheDocument();
  });

  it('should handle async errors that are caught', async () => {
    const AsyncComponent = () => {
      React.useEffect(() => {
        const throwAsync = async () => {
          await Promise.reject(new Error('Async error'));
        };
        
        throwAsync().catch(() => {
          // Error is caught, ErrorBoundary should not trigger
        });
      }, []);

      return <div>Async component</div>;
    };

    render(
      <ErrorBoundary>
        <AsyncComponent />
      </ErrorBoundary>
    );

    // Should render normally since async error is caught
    expect(screen.getByText('Async component')).toBeInTheDocument();
    expect(screen.queryByText(/문제가 발생했습니다/i)).not.toBeInTheDocument();
  });
});