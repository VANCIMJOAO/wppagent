const fs = require('fs');

// Ler o arquivo
let content = fs.readFileSync('/home/vancim/whats_agent/nextjs_dashboard/app/(dashboard)/admin/backup/page.tsx', 'utf8');

// Padrão para encontrar chamadas fetch que precisam de correção
const fetchPattern = /const response = await fetch\(([^)]+)\);\s*setBackupLogs\(data\.logs \|\| \[\]\);/g;
const fetchPattern2 = /const response = await fetch\(([^)]+)\);\s*setBackupLogs\(data\);/g;
const fetchPattern3 = /const response = await fetch\(([^)]+)\);\s*setBackupConfig\(data\);/g;

// Substituições
content = content.replace(fetchPattern, (match, url) => {
  return `const response = await fetch(${url}, {\n        credentials: 'include'\n      });\n      const data = await response.json();\n      setBackupLogs(data.logs || []);`;
});

content = content.replace(fetchPattern2, (match, url) => {
  return `const response = await fetch(${url}, {\n        credentials: 'include'\n      });\n      const data = await response.json();\n      setBackupLogs(data);`;
});

content = content.replace(fetchPattern3, (match, url) => {
  return `const response = await fetch(${url}, {\n        credentials: 'include'\n      });\n      const data = await response.json();\n      setBackupConfig(data);`;
});

// Escrever o arquivo corrigido
fs.writeFileSync('/home/vancim/whats_agent/nextjs_dashboard/app/(dashboard)/admin/backup/page.tsx', content);

console.log('Arquivo corrigido!');
