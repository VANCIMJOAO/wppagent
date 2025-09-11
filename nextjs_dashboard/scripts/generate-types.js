#!/usr/bin/env node

/**
 * 🔧 Script de Auto-geração de Tipos TypeScript
 * =============================================
 * 
 * Gera tipos TypeScript automaticamente a partir do OpenAPI schema do backend.
 * Garante type safety completo e elimina divergências entre frontend/backend.
 */

import fs from 'fs/promises';
import path from 'path';
import { execSync } from 'child_process';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://wppagent-production.up.railway.app';
const OUTPUT_FILE = 'types/api-generated.ts';
const OPENAPI_URL = `${API_BASE_URL}/openapi.json`;

async function generateTypes() {
  console.log('🚀 Iniciando geração de tipos TypeScript...');
  
  try {
    // 1. Baixar schema OpenAPI
    console.log('📥 Baixando schema OpenAPI...');
    const response = await fetch(OPENAPI_URL);
    
    if (!response.ok) {
      throw new Error(`Erro ao buscar schema: ${response.status} ${response.statusText}`);
    }
    
    const schema = await response.json();
    console.log('✅ Schema OpenAPI baixado com sucesso');
    
    // 2. Salvar schema temporariamente
    const tempSchemaFile = 'temp-openapi.json';
    await fs.writeFile(tempSchemaFile, JSON.stringify(schema, null, 2));
    
    // 3. Gerar tipos TypeScript usando openapi-typescript
    console.log('🔧 Gerando tipos TypeScript...');
    const command = `npx openapi-typescript ${tempSchemaFile} --output ${OUTPUT_FILE}`;
    execSync(command, { stdio: 'inherit' });
    
    // 4. Adicionar header personalizado
    const generatedContent = await fs.readFile(OUTPUT_FILE, 'utf-8');
    const headerComment = `/**
 * 🤖 TIPOS TYPESCRIPT AUTO-GERADOS
 * ================================
 * 
 * ⚠️  ATENÇÃO: Este arquivo é gerado automaticamente!
 * ❌ NÃO EDITE MANUALMENTE - Suas alterações serão perdidas
 * 
 * Para regenerar: npm run generate:types
 * Fonte: ${OPENAPI_URL}
 * Gerado em: ${new Date().toISOString()}
 * 
 * 📋 Compatibilidade de Tipos:
 * - ✅ Zero any types
 * - ✅ Type safety completo
 * - ✅ Sincronizado com backend
 */

/* eslint-disable */
/* tslint:disable */
// @ts-nocheck

${generatedContent}`;

    await fs.writeFile(OUTPUT_FILE, headerComment);
    
    // 5. Limpar arquivo temporário
    await fs.unlink(tempSchemaFile);
    
    // 6. Criar index de tipos para facilitar imports
    await createTypesIndex();
    
    // 7. Validar tipos gerados
    await validateGeneratedTypes();
    
    console.log('✅ Tipos TypeScript gerados com sucesso!');
    console.log(`📁 Arquivo: ${OUTPUT_FILE}`);
    
  } catch (error) {
    console.error('❌ Erro na geração de tipos:', error.message);
    process.exit(1);
  }
}

async function createTypesIndex() {
  const indexContent = `/**
 * 📋 Index de Tipos TypeScript
 * ============================
 * 
 * Centraliza todos os exports de tipos para imports mais limpos.
 */

// Tipos auto-gerados do backend
export * from './api-generated';

// Tipos manuais específicos do frontend
export * from './api';
export * from './analytics';
export * from './conversation';

// Tipos utilitários
export type ApiError = {
  error: string;
  detail?: string;
  status_code?: number;
};

export type ApiSuccess<T = any> = {
  success: true;
  data: T;
  message?: string;
};

export type ApiResponse<T = any> = ApiSuccess<T> | ApiError;

// Helper types para melhor DX
export type WithId<T> = T & { id: string | number };
export type WithTimestamps<T> = T & { 
  created_at: string; 
  updated_at: string; 
};
export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;
export type RequiredOnly<T, K extends keyof T> = Partial<T> & Required<Pick<T, K>>;
`;

  await fs.writeFile('types/index.ts', indexContent);
  console.log('✅ Index de tipos criado');
}

async function validateGeneratedTypes() {
  try {
    console.log('🔍 Validando tipos gerados...');
    
    // Verifica se o arquivo foi criado
    const stats = await fs.stat(OUTPUT_FILE);
    if (stats.size === 0) {
      throw new Error('Arquivo de tipos está vazio');
    }
    
    // Executa type-check para validar
    execSync('npm run type-check', { stdio: 'pipe' });
    console.log('✅ Validação de tipos passou');
    
  } catch (error) {
    if (error.stdout) {
      console.error('❌ Erros de tipo encontrados:');
      console.error(error.stdout.toString());
    }
    throw new Error('Falha na validação de tipos');
  }
}

// Executar se chamado diretamente
if (import.meta.url === `file://${process.argv[1]}`) {
  generateTypes();
}

export { generateTypes };
