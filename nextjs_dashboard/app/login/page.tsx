/**
 * Página de Login com integração RBAC
 * Sistema completo de autenticação com suporte a 2FA
 */
'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useRBAC } from '../../hooks/useRBAC';
import { 
  User, 
  Lock, 
  Eye, 
  EyeOff, 
  Shield, 
  AlertCircle, 
  CheckCircle,
  Smartphone,
  Key
} from 'lucide-react';

interface LoginFormData {
  username: string;
  password: string;
}

interface TwoFactorData {
  code: string;
}

const LoginPage: React.FC = () => {
  const router = useRouter();
  const { login, isAuthenticated, isLoading } = useRBAC();
  
  const [formData, setFormData] = useState<LoginFormData>({
    username: '',
    password: ''
  });
  
  const [twoFactorData, setTwoFactorData] = useState<TwoFactorData>({
    code: ''
  });
  
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [requiresTwoFactor, setRequiresTwoFactor] = useState(false);
  const [tempToken, setTempToken] = useState<string | null>(null);

  // Redirecionar se já autenticado
  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, isLoading, router]);

  // Handler para mudanças no formulário principal
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Limpar erros ao digitar
    if (error) setError(null);
  };

  // Handler para mudanças no código 2FA
  const handleTwoFactorChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { value } = e.target;
    // Permitir apenas números e limitar a 6 dígitos
    if (/^\d{0,6}$/.test(value)) {
      setTwoFactorData({ code: value });
    }
    
    if (error) setError(null);
  };

  // Fazer login inicial
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (response.ok) {
        if (data.requires_2fa) {
          // Usuário requer 2FA
          setRequiresTwoFactor(true);
          setTempToken(data.temp_token);
          setSuccess('Código 2FA enviado. Verifique seu dispositivo.');
        } else {
          // Login completo sem 2FA
          await login(data.access_token);
          setSuccess('Login realizado com sucesso!');
          router.push('/dashboard');
        }
      } else {
        setError(data.detail || 'Credenciais inválidas');
      }
    } catch (err) {
      setError('Erro de conexão. Tente novamente.');
      console.error('Erro no login:', err);
    } finally {
      setLoading(false);
    }
  };

  // Verificar código 2FA
  const handleTwoFactorVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/auth/verify-2fa', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          temp_token: tempToken,
          code: twoFactorData.code,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        await login(data.access_token);
        setSuccess('Autenticação completa!');
        router.push('/dashboard');
      } else {
        setError(data.detail || 'Código 2FA inválido');
      }
    } catch (err) {
      setError('Erro de conexão. Tente novamente.');
      console.error('Erro na verificação 2FA:', err);
    } finally {
      setLoading(false);
    }
  };

  // Reenviar código 2FA
  const handleResendCode = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/auth/resend-2fa', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          temp_token: tempToken,
        }),
      });

      if (response.ok) {
        setSuccess('Código reenviado com sucesso!');
      } else {
        const data = await response.json();
        setError(data.detail || 'Erro ao reenviar código');
      }
    } catch (err) {
      setError('Erro de conexão.');
    } finally {
      setLoading(false);
    }
  };

  // Voltar ao formulário de login
  const handleBackToLogin = () => {
    setRequiresTwoFactor(false);
    setTempToken(null);
    setTwoFactorData({ code: '' });
    setError(null);
    setSuccess(null);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div className="text-center">
          <div className="mx-auto h-12 w-12 flex items-center justify-center rounded-full bg-blue-100">
            <Shield className="h-8 w-8 text-blue-600" />
          </div>
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
            {requiresTwoFactor ? 'Verificação 2FA' : 'Faça seu login'}
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            {requiresTwoFactor 
              ? 'Digite o código de 6 dígitos do seu dispositivo'
              : 'Acesse sua conta do sistema'
            }
          </p>
        </div>

        {/* Mensagens de feedback */}
        {error && (
          <div className="rounded-md bg-red-50 p-4">
            <div className="flex">
              <AlertCircle className="h-5 w-5 text-red-400" />
              <div className="ml-3">
                <p className="text-sm font-medium text-red-800">{error}</p>
              </div>
            </div>
          </div>
        )}

        {success && (
          <div className="rounded-md bg-green-50 p-4">
            <div className="flex">
              <CheckCircle className="h-5 w-5 text-green-400" />
              <div className="ml-3">
                <p className="text-sm font-medium text-green-800">{success}</p>
              </div>
            </div>
          </div>
        )}

        {/* Formulário principal de login */}
        {!requiresTwoFactor && (
          <form className="mt-8 space-y-6" onSubmit={handleLogin}>
            <div className="space-y-4">
              {/* Username */}
              <div>
                <label htmlFor="username" className="sr-only">
                  Usuário
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <User className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    id="username"
                    name="username"
                    type="text"
                    required
                    value={formData.username}
                    onChange={handleInputChange}
                    className="relative block w-full pl-10 pr-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                    placeholder="Nome de usuário"
                  />
                </div>
              </div>

              {/* Password */}
              <div>
                <label htmlFor="password" className="sr-only">
                  Senha
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Lock className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    id="password"
                    name="password"
                    type={showPassword ? 'text' : 'password'}
                    required
                    value={formData.password}
                    onChange={handleInputChange}
                    className="relative block w-full pl-10 pr-10 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                    placeholder="Senha"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  >
                    {showPassword ? (
                      <EyeOff className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                    ) : (
                      <Eye className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                    )}
                  </button>
                </div>
              </div>
            </div>

            {/* Botão de login */}
            <div>
              <button
                type="submit"
                disabled={loading || !formData.username || !formData.password}
                className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                ) : (
                  'Entrar'
                )}
              </button>
            </div>
          </form>
        )}

        {/* Formulário de verificação 2FA */}
        {requiresTwoFactor && (
          <div className="mt-8 space-y-6">
            <div className="text-center">
              <div className="mx-auto h-16 w-16 flex items-center justify-center rounded-full bg-blue-100">
                <Smartphone className="h-8 w-8 text-blue-600" />
              </div>
            </div>

            <form onSubmit={handleTwoFactorVerify} className="space-y-4">
              <div>
                <label htmlFor="code" className="sr-only">
                  Código 2FA
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Key className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    id="code"
                    name="code"
                    type="text"
                    inputMode="numeric"
                    pattern="\d{6}"
                    maxLength={6}
                    required
                    value={twoFactorData.code}
                    onChange={handleTwoFactorChange}
                    className="relative block w-full pl-10 pr-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm text-center text-lg font-mono tracking-widest"
                    placeholder="000000"
                    autoComplete="one-time-code"
                  />
                </div>
                <p className="mt-2 text-xs text-gray-500 text-center">
                  Digite o código de 6 dígitos do seu aplicativo autenticador
                </p>
              </div>

              <div className="space-y-3">
                <button
                  type="submit"
                  disabled={loading || twoFactorData.code.length !== 6}
                  className="w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  ) : (
                    'Verificar Código'
                  )}
                </button>

                <div className="flex space-x-2">
                  <button
                    type="button"
                    onClick={handleResendCode}
                    disabled={loading}
                    className="flex-1 text-center py-2 px-4 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                  >
                    Reenviar Código
                  </button>

                  <button
                    type="button"
                    onClick={handleBackToLogin}
                    className="flex-1 text-center py-2 px-4 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Voltar
                  </button>
                </div>
              </div>
            </form>
          </div>
        )}

        {/* Footer */}
        <div className="text-center">
          <p className="text-xs text-gray-500">
            Protegido por sistema RBAC com autenticação 2FA
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
