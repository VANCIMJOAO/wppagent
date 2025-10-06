'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Shield, ArrowLeft, AlertTriangle } from 'lucide-react';
import { debugLog } from '@/lib/debug';

interface RoleGuardProps {
  children: React.ReactNode;
  requiredRole: 'admin' | 'atendente' | 'visualizador';
  fallback?: React.ReactNode;
}

export function RoleGuard({ children, requiredRole, fallback }: RoleGuardProps) {
  const [isAuthorized, setIsAuthorized] = useState<boolean | null>(null);
  const [userRole, setUserRole] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    checkUserRole();
  }, []);

  const checkUserRole = async () => {
    try {
      // Simular verificação de role do usuário
      // Em um app real, isso viria de um contexto de autenticação ou API
      const mockUserRole = 'admin'; // Simular usuário admin
      
      setUserRole(mockUserRole);
      
      // Verificar se o usuário tem permissão
      const hasPermission = checkPermission(mockUserRole, requiredRole);
      setIsAuthorized(hasPermission);
    } catch (error) {
      debugLog.error('Erro ao verificar role do usuário:', error);
      setIsAuthorized(false);
    } finally {
      setLoading(false);
    }
  };

  const checkPermission = (userRole: string, requiredRole: string): boolean => {
    const roleHierarchy = {
      'visualizador': 1,
      'atendente': 2,
      'admin': 3
    };

    const userLevel = roleHierarchy[userRole as keyof typeof roleHierarchy] || 0;
    const requiredLevel = roleHierarchy[requiredRole as keyof typeof roleHierarchy] || 0;

    return userLevel >= requiredLevel;
  };

  const handleGoBack = () => {
    router.back();
  };

  const handleGoHome = () => {
    router.push('/dashboard');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!isAuthorized) {
    if (fallback) {
      return <>{fallback}</>;
    }

    return (
      <div className="flex items-center justify-center min-h-[400px] p-4">
        <Card className="max-w-md w-full">
          <CardHeader className="text-center">
            <div className="mx-auto w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mb-4">
              <Shield className="h-6 w-6 text-red-600" />
            </div>
            <CardTitle className="text-xl text-red-600">Acesso Negado</CardTitle>
          </CardHeader>
          <CardContent className="text-center space-y-4">
            <div className="flex items-center justify-center gap-2 text-yellow-600">
              <AlertTriangle className="h-5 w-5" />
              <span className="font-medium">Permissão Insuficiente</span>
            </div>
            
            <p className="text-gray-600">
              Você não tem permissão para acessar esta página.
            </p>
            
            <div className="bg-gray-50 p-3 rounded-lg text-sm">
              <p><strong>Role necessária:</strong> {requiredRole}</p>
              <p><strong>Sua role:</strong> {userRole || 'Não identificada'}</p>
            </div>

            <div className="flex gap-3 justify-center">
              <Button variant="outline" onClick={handleGoBack}>
                <ArrowLeft className="h-4 w-4 mr-2" />
                Voltar
              </Button>
              <Button onClick={handleGoHome}>
                Ir para Dashboard
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return <>{children}</>;
}
