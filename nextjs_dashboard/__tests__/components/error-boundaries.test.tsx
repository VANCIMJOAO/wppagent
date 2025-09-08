import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { jest } from '@jest/globals';
import ErrorBoundary from '@/components/error-boundary';
import { 
  DashboardErrorBoundary, 
  ConversasErrorBoundary, 
  ComponentErrorBoundary,
  useErrorReporter 
} from '@/components/error-boundaries';

// Mock fetch globally
const mockFetch = jest.fn() as jest.MockedFunction<typeof fetch>;
global.fetch = mockFetch;

// Mock clipboard API
const mockWriteText = jest.fn();
Object.assign(navigator, {
  clipboard: {
    writeText: mockWriteText,
  },
});

// Console methods to spy on
const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
const consoleGroupSpy = jest.spyOn(console, 'group').mockImplementation(() => {});
const consoleGroupEndSpy = jest.spyOn(console, 'groupEnd').mockImplementation(() => {});

// Test component that throws an error
function ProblematicComponent({ shouldThrow = false }: { shouldThrow?: boolean }) {
  if (shouldThrow) {
    throw new Error('Test error message');
  }
  return <div>Working component</div>;
}

// Test component that throws after state change
function AsyncProblematicComponent() {
  const [shouldThrow, setShouldThrow] = React.useState(false);
  
  if (shouldThrow) {
    throw new Error('Async error message');
  }
  
  return (
    <div>
      <span>Working component</span>
      <button onClick={() => setShouldThrow(true)}>Trigger Error</button>
    </div>
  );
}

describe('Error Boundaries System', () => {
  beforeEach(() => {
    mockFetch.mockClear();
    consoleSpy.mockClear();
    consoleGroupSpy.mockClear();
    consoleGroupEndSpy.mockClear();
    
    // Mock successful error reporting
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ success: true })
    } as Response);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('Global Error Boundary', () => {
    it('should render children when no error occurs', () => {
      render(
        <ErrorBoundary level="global" name="Test">
          <ProblematicComponent shouldThrow={false} />
        </ErrorBoundary>
      );
      
      expect(screen.getByText('Working component')).toBeInTheDocument();
    });

    it('should catch error and render global fallback UI', () => {
      render(
        <ErrorBoundary level="global" name="Test">
          <ProblematicComponent shouldThrow={true} />
        </ErrorBoundary>
      );
      
      expect(screen.getByText('Ops! Algo deu errado')).toBeInTheDocument();
      expect(screen.getByText(/Ocorreu um erro inesperado na aplicação/)).toBeInTheDocument();
      expect(screen.getByText(/Nossa equipe foi notificada automaticamente/)).toBeInTheDocument();
    });

    it('should show error ID in global fallback', () => {
      render(
        <ErrorBoundary level="global" name="Test">
          <ProblematicComponent shouldThrow={true} />
        </ErrorBoundary>
      );
      
      expect(screen.getByText('ID do Erro:')).toBeInTheDocument();
      expect(screen.getByText(/err_/)).toBeInTheDocument();
    });

    it('should show retry button with count', () => {
      render(
        <ErrorBoundary level="global" name="Test">
          <ProblematicComponent shouldThrow={true} />
        </ErrorBoundary>
      );
      
      const retryButton = screen.getByText(/Tentar Novamente \(0\/3\)/);
      expect(retryButton).toBeInTheDocument();
    });

    it('should show copy details button', () => {
      render(
        <ErrorBoundary level="global" name="Test">
          <ProblematicComponent shouldThrow={true} />
        </ErrorBoundary>
      );
      
      expect(screen.getByText(/Copiar Detalhes do Erro/)).toBeInTheDocument();
    });

    it('should show technical details in development', () => {
      // Mock NODE_ENV for this test
      const originalNodeEnv = process.env.NODE_ENV;
      Object.defineProperty(process.env, 'NODE_ENV', { value: 'development', configurable: true });
      
      render(
        <ErrorBoundary level="global" name="Test">
          <ProblematicComponent shouldThrow={true} />
        </ErrorBoundary>
      );
      
      expect(screen.getByText('Detalhes técnicos')).toBeInTheDocument();
      
      // Restore original NODE_ENV
      Object.defineProperty(process.env, 'NODE_ENV', { value: originalNodeEnv, configurable: true });
    });
  });

  describe('Page Error Boundary', () => {
    it('should render page-specific fallback UI', () => {
      render(
        <ErrorBoundary level="page" name="Dashboard">
          <ProblematicComponent shouldThrow={true} />
        </ErrorBoundary>
      );
      
      expect(screen.getByText('Erro na página')).toBeInTheDocument();
      expect(screen.getByText('Test error message')).toBeInTheDocument();
    });

    it('should show home button in page error', () => {
      render(
        <ErrorBoundary level="page" name="Dashboard">
          <ProblematicComponent shouldThrow={true} />
        </ErrorBoundary>
      );
      
      expect(screen.getByText(/Voltar ao Dashboard/)).toBeInTheDocument();
    });
  });

  describe('Component Error Boundary', () => {
    it('should render compact component fallback UI', () => {
      render(
        <ErrorBoundary level="component" name="Widget">
          <ProblematicComponent shouldThrow={true} />
        </ErrorBoundary>
      );
      
      expect(screen.getByText('Erro no componente')).toBeInTheDocument();
      expect(screen.getByText('Test error message')).toBeInTheDocument();
    });
  });

  describe('Error Reporting', () => {
    it('should report error to API endpoint', async () => {
      render(
        <ErrorBoundary level="global" name="Test" onError={jest.fn()}>
          <ProblematicComponent shouldThrow={true} />
        </ErrorBoundary>
      );
      
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith('/api/errors', expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: expect.stringContaining('"message":"Test error message"')
        }));
      });
    });

    it('should include proper error details in report', async () => {
      render(
        <ErrorBoundary level="page" name="Dashboard">
          <ProblematicComponent shouldThrow={true} />
        </ErrorBoundary>
      );
      
      await waitFor(() => {
        const callArgs = mockFetch.mock.calls[0];
        const requestInit = callArgs[1] as RequestInit;
        const body = JSON.parse(requestInit.body as string);
        
        expect(body).toMatchObject({
          message: 'Test error message',
          level: 'page',
          name: 'Dashboard',
          retryCount: 0
        });
        expect(body.id).toMatch(/^err_/);
        expect(body.timestamp).toBeDefined();
      });
    });

    it('should call onError callback when provided', () => {
      const onErrorMock = jest.fn();
      
      render(
        <ErrorBoundary level="global" name="Test" onError={onErrorMock}>
          <ProblematicComponent shouldThrow={true} />
        </ErrorBoundary>
      );
      
      expect(onErrorMock).toHaveBeenCalledWith(
        expect.objectContaining({ message: 'Test error message' }),
        expect.objectContaining({ componentStack: expect.any(String) })
      );
    });

    it('should log structured error information', () => {
      render(
        <ErrorBoundary level="global" name="Test">
          <ProblematicComponent shouldThrow={true} />
        </ErrorBoundary>
      );
      
      expect(consoleGroupSpy).toHaveBeenCalledWith('🚨 Error Boundary [global - Test]');
      expect(consoleSpy).toHaveBeenCalledWith('Error:', expect.objectContaining({ 
        message: 'Test error message' 
      }));
    });
  });

  describe('Retry Functionality', () => {
    it('should show retry button', async () => {
      render(
        <ErrorBoundary level="page" name="Test">
          <AsyncProblematicComponent />
        </ErrorBoundary>
      );
      
      // Trigger error
      const triggerButton = screen.getByText('Trigger Error');
      fireEvent.click(triggerButton);
      
      // Should show error UI with retry button
      await waitFor(() => {
        expect(screen.getByText(/Tentar novamente/)).toBeInTheDocument();
      });
    });

    it('should show error fallback for component level errors', () => {
      const TestComponentWithError = () => {
        return (
          <ErrorBoundary level="component" name="Test">
            <ProblematicComponent shouldThrow={true} />
          </ErrorBoundary>
        );
      };
      
      render(<TestComponentWithError />);
      
      // Should show component error fallback
      expect(screen.getByText('Erro no componente')).toBeInTheDocument();
    });
  });

  describe('Specific Error Boundaries', () => {
    it('should render Dashboard-specific error boundary', () => {
      render(
        <DashboardErrorBoundary>
          <ProblematicComponent shouldThrow={true} />
        </DashboardErrorBoundary>
      );
      
      expect(screen.getByText('Erro no Dashboard')).toBeInTheDocument();
      expect(screen.getByText(/O dashboard encontrou um problema/)).toBeInTheDocument();
    });

    it('should render Conversas-specific error boundary', () => {
      render(
        <ConversasErrorBoundary>
          <ProblematicComponent shouldThrow={true} />
        </ConversasErrorBoundary>
      );
      
      expect(screen.getByText('Erro nas Conversas')).toBeInTheDocument();
      expect(screen.getByText(/Não foi possível carregar as conversas/)).toBeInTheDocument();
    });

    it('should render Component-specific error boundary with custom name', () => {
      render(
        <ComponentErrorBoundary name="CustomWidget">
          <ProblematicComponent shouldThrow={true} />
        </ComponentErrorBoundary>
      );
      
      expect(screen.getByText('Erro no componente')).toBeInTheDocument();
    });
  });

  describe('useErrorReporter Hook', () => {
    it('should manually report errors', async () => {
      const TestComponent = () => {
        const { reportError } = useErrorReporter();
        
        const handleClick = () => {
          const error = new Error('Manual error report');
          reportError(error, 'TestComponent');
        };
        
        return <button onClick={handleClick}>Report Error</button>;
      };
      
      render(<TestComponent />);
      
      const button = screen.getByText('Report Error');
      fireEvent.click(button);
      
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith('/api/errors', expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: expect.stringContaining('"message":"Manual error report"')
        }));
      });
    });
  });

  describe('Copy Error Details', () => {
    it('should copy error details to clipboard', async () => {
      render(
        <ErrorBoundary level="global" name="Test">
          <ProblematicComponent shouldThrow={true} />
        </ErrorBoundary>
      );
      
      const copyButton = screen.getByText(/Copiar Detalhes do Erro/);
      fireEvent.click(copyButton);
      
      await waitFor(() => {
        expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
          expect.stringContaining('Error ID:')
        );
      });
    });
  });

  describe('Navigation Actions', () => {
    it('should have dashboard navigation button', () => {
      render(
        <ErrorBoundary level="global" name="Test">
          <ProblematicComponent shouldThrow={true} />
        </ErrorBoundary>
      );
      
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
    });

    it('should have support navigation button', () => {
      render(
        <ErrorBoundary level="global" name="Test">
          <ProblematicComponent shouldThrow={true} />
        </ErrorBoundary>
      );
      
      expect(screen.getByText('Suporte')).toBeInTheDocument();
    });
  });

  describe('Error Boundary Integration', () => {
    it('should handle nested error boundaries correctly', () => {
      render(
        <ErrorBoundary level="global" name="Global">
          <ErrorBoundary level="page" name="Page">
            <ErrorBoundary level="component" name="Component">
              <ProblematicComponent shouldThrow={true} />
            </ErrorBoundary>
          </ErrorBoundary>
        </ErrorBoundary>
      );
      
      // Should catch at the lowest level (component)
      expect(screen.getByText('Erro no componente')).toBeInTheDocument();
    });

    it('should handle custom fallback components', () => {
      const CustomFallback = <div>Custom error fallback</div>;
      
      render(
        <ErrorBoundary level="global" name="Test" fallback={CustomFallback}>
          <ProblematicComponent shouldThrow={true} />
        </ErrorBoundary>
      );
      
      expect(screen.getByText('Custom error fallback')).toBeInTheDocument();
    });
  });

  describe('Error Boundary Performance', () => {
    it('should not re-render when children props change if no error', () => {
      const { rerender } = render(
        <ErrorBoundary level="global" name="Test">
          <ProblematicComponent shouldThrow={false} />
        </ErrorBoundary>
      );
      
      expect(screen.getByText('Working component')).toBeInTheDocument();
      
      rerender(
        <ErrorBoundary level="global" name="Test">
          <ProblematicComponent shouldThrow={false} />
        </ErrorBoundary>
      );
      
      expect(screen.getByText('Working component')).toBeInTheDocument();
    });
  });
});
