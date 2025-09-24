'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function ReportsRedirect() {
  const router = useRouter();

  useEffect(() => {
    // Redirecionar para a página de exportação de relatórios dentro do dashboard
    router.replace('/exportar-relatorios');
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center space-y-4">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
        <p className="text-gray-600">Redirecionando para a página de relatórios...</p>
      </div>
    </div>
  );
}
