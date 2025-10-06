/**
 * Redirecionamento para Página Unificada de Relatórios
 * Esta página agora redireciona para /relatorios com a tab de exportação ativa
 */
'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { FileSpreadsheet } from 'lucide-react';

const ExportarRelatoriosPage: React.FC = () => {
  const router = useRouter();

  useEffect(() => {
    // Redirecionar para a página de relatórios com a tab de exportação
    router.replace('/relatorios?tab=export');
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-white">
      <div className="text-center space-y-4">
        <div className="flex items-center justify-center w-16 h-16 mx-auto rounded-full bg-gradient-to-br from-primary to-primary/80 shadow-lg">
          <FileSpreadsheet className="w-8 h-8 text-white animate-pulse" />
        </div>
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
        <p className="text-gray-600 font-medium">Redirecionando para Relatórios...</p>
      </div>
    </div>
  );
};

export default ExportarRelatoriosPage;
