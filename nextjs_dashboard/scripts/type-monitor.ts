#!/usr/bin/env tsx

/**
 * 🔧 Monitor de Tipos em Desenvolvimento
 * =====================================
 * 
 * Monitora mudanças no backend e regenera tipos automaticamente.
 * Executa durante desenvolvimento para manter sincronização.
 */

import { execSync } from 'child_process';
import * as fs from 'fs/promises';
import { generateTypes } from './generate-types';

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const CHECK_INTERVAL = 30000; // 30 segundos

interface BackendHealth {
  status: string;
  timestamp: string;
  service: string;
  version?: string;
}

async function checkBackendHealth(): Promise<BackendHealth | null> {
  try {
    const fetch = (await import('node-fetch')).default;
    const response = await fetch(`${BACKEND_URL}/health`);
    
    if (response.ok) {
      return await response.json() as BackendHealth;
    }
    return null;
  } catch (error) {
    return null;
  }
}

async function getOpenAPIChecksum(): Promise<string | null> {
  try {
    const fetch = (await import('node-fetch')).default;
    const response = await fetch(`${BACKEND_URL}/openapi.json`);
    
    if (response.ok) {
      const schema = await response.text();
      // Simples checksum usando length + primeiro/último caracteres
      return `${schema.length}-${schema.slice(0, 100)}-${schema.slice(-100)}`;
    }
    return null;
  } catch (error) {
    return null;
  }
}

async function saveChecksum(checksum: string) {
  await fs.writeFile('.api-checksum', checksum);
}

async function loadChecksum(): Promise<string | null> {
  try {
    return await fs.readFile('.api-checksum', 'utf-8');
  } catch (error) {
    return null;
  }
}

async function monitorAndRegenerate() {
  console.log('🔍 Iniciando monitor de tipos TypeScript...');
  console.log(`📡 Backend: ${BACKEND_URL}`);
  console.log(`⏱️  Intervalo: ${CHECK_INTERVAL / 1000}s`);
  console.log('');
  
  let lastChecksum = await loadChecksum();
  let isFirstRun = !lastChecksum;
  
  while (true) {
    try {
      // Verificar se backend está online
      const health = await checkBackendHealth();
      
      if (!health) {
        console.log('⚠️ Backend offline - aguardando...');
        await sleep(CHECK_INTERVAL);
        continue;
      }
      
      if (isFirstRun) {
        console.log(`✅ Backend online: ${health.service} ${health.version || ''}`);
        isFirstRun = false;
      }
      
      // Verificar mudanças no schema
      const currentChecksum = await getOpenAPIChecksum();
      
      if (!currentChecksum) {
        console.log('⚠️ Erro ao obter schema - tentando novamente...');
        await sleep(CHECK_INTERVAL);
        continue;
      }
      
      // Se mudou, regenerar tipos
      if (currentChecksum !== lastChecksum) {
        console.log('🔄 Schema OpenAPI mudou - regenerando tipos...');
        
        try {
          await generateTypes({
            validate: false // Não validar durante desenvolvimento
          });
          
          await saveChecksum(currentChecksum);
          lastChecksum = currentChecksum;
          
          console.log('✅ Tipos regenerados com sucesso!');
          
          // Executar type-check
          try {
            execSync('npm run type-check', { stdio: 'pipe' });
            console.log('✅ Type-check passou');
          } catch (error) {
            console.log('⚠️ Type-check falhou - verifique o código');
          }
          
        } catch (error) {
          console.error('❌ Erro na regeneração:', error);
        }
      }
      
      // Aguardar próxima verificação
      await sleep(CHECK_INTERVAL);
      
    } catch (error) {
      console.error('❌ Erro no monitor:', error);
      await sleep(CHECK_INTERVAL);
    }
  }
}

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Executar se chamado diretamente
if (require.main === module) {
  // Gerar tipos inicialmente
  generateTypes({ validate: false })
    .then(() => {
      console.log('📋 Tipos iniciais gerados');
      return monitorAndRegenerate();
    })
    .catch(error => {
      console.error('❌ Erro fatal:', error);
      process.exit(1);
    });
}

export { monitorAndRegenerate };
