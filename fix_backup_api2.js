const fs = require('fs');

// Ler o arquivo
let content = fs.readFileSync('/home/vancim/whats_agent/nextjs_dashboard/app/(dashboard)/admin/backup/page.tsx', 'utf8');

// Corrigir todas as chamadas fetch que precisam de method e body
const patterns = [
  // POST calls
  {
    pattern: /const response = await fetch\('([^']+)', \{\s*backup_type: ([^,]+),\s*cloud_upload: ([^}]+)\s*\}\);/g,
    replacement: (match, url, backupType, cloudUpload) => {
      return `const response = await fetch('${url}', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({
          backup_type: ${backupType},
          cloud_upload: ${cloudUpload}
        })
      });`;
    }
  },
  // DELETE calls
  {
    pattern: /const response = await fetch\('([^']+)', \{\s*method: 'DELETE'\s*\}\);/g,
    replacement: (match, url) => {
      return `const response = await fetch('${url}', {
        method: 'DELETE',
        credentials: 'include'
      });`;
    }
  }
];

patterns.forEach(({ pattern, replacement }) => {
  content = content.replace(pattern, replacement);
});

// Escrever o arquivo corrigido
fs.writeFileSync('/home/vancim/whats_agent/nextjs_dashboard/app/(dashboard)/admin/backup/page.tsx', content);

console.log('Arquivo corrigido!');
