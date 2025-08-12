# RELATÓRIO OPERACIONAL DIÁRIO

**Data de Geração**: 2025-08-09 22:39:07  
**Sistema**: WhatsApp Agent  
**Ambiente**: development  
**Servidor**: vancim  
**Gerado por**: vancim

---

## 🏥 SAÚDE DO SISTEMA

### Health Checks
```
Sistema Principal:
❌ Health check principal: FALHA

Banco de Dados:
❌ PostgreSQL: FALHA

Redis:
❌ Redis: FALHA

Webhook:
❌ Webhook: FALHA
```

### Status dos Serviços
```
## 📊 MÉTRICAS DO SISTEMA

### CPU e Load Average
```
Load Average:  0,68, 0,56, 0,55
CPU Usage: % user
```

### Uso de Memória
```
               total       usada       livre    compart.  buff/cache  disponível
Mem.:           15Gi       6,6Gi       1,7Gi        86Mi       7,6Gi       8,9Gi
Swap:          4,0Gi       512Ki       4,0Gi
```

### Uso de Disco
```
/dev/nvme0n1p5   98G   90G  3,5G  97% /
tmpfs           7,8G   64M  7,7G   1% /dev/shm
/dev/nvme0n1p1   96M   37M   60M  39% /boot/efi
/dev/nvme0n1p3  831G  259G  573G  32% /media/vancim/5C64FCB264FC904E
```

### Top Processos (CPU)
```
USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
vancim      5182 18.2  5.3 1463273640 867828 ?   Rl   20:31  23:15 /snap/code/202/usr/share/code/code --type=zygote --no-sandbox
vancim      5113 11.2  1.1 34057008 178996 ?     Sl   20:31  14:19 /proc/self/exe --type=gpu-process --disable-gpu-sandbox --no-s
vancim      3199  5.9  2.8 4507172 461968 ?      Ssl  20:31   7:38 /usr/bin/gnome-shell
vancim      5405  3.4  8.1 1469704740 1332796 ?  Sl   20:31   4:20 /proc/self/exe --type=utility --utility-sub-type=node.mojom.No
vancim      6211  2.7  5.5 1485525660 895284 pts/0 Sl+ 20:32   3:30 /usr/lib/claude-desktop/node_modules/electron/dist/electron -
root        2400  2.2  0.5 3209228 89752 ?       Ssl  20:30   2:53 /usr/bin/dockerd -H fd:// --containerd=/run/containerd/contain
vancim      2984  1.9  0.6 25447832 108500 tty2  Sl+  20:31   2:25 /usr/lib/xorg/Xorg vt2 -displayfd 3 -auth /run/user/1000/gdm/X
vancim      5980  1.6  5.1 1462833672 844052 ?   Sl   20:32   2:07 /snap/code/202/usr/share/code/code /home/vancim/.vscode/extens
vancim      4959  0.5  1.2 1461345800 201436 ?   SLsl 20:31   0:43 /snap/code/202/usr/share/code/code --no-sandbox --force-user-e
```

### Top Processos (Memória)
```
USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
vancim      5405  3.4  8.1 1469704740 1332796 ?  Sl   20:31   4:20 /proc/self/exe --type=utility --utility-sub-type=node.mojom.No
vancim      6211  2.7  5.5 1485525660 895284 pts/0 Sl+ 20:32   3:30 /usr/lib/claude-desktop/node_modules/electron/dist/electron -
vancim      5182 18.2  5.3 1463273640 867956 ?   Rl   20:31  23:15 /snap/code/202/usr/share/code/code --type=zygote --no-sandbox
vancim      5980  1.6  5.1 1462833672 844052 ?   Sl   20:32   2:07 /snap/code/202/usr/share/code/code /home/vancim/.vscode/extens
vancim      3199  5.9  2.8 4507172 461968 ?      Ssl  20:31   7:38 /usr/bin/gnome-shell
vancim      3509  0.0  1.5 1452492 257800 ?      Sl   20:31   0:04 /usr/bin/gnome-software --gapplication-service
vancim      6077  0.0  1.4 1460079724 241968 pts/0 Sl+ 20:32   0:06 /usr/lib/claude-desktop/node_modules/electron/dist/electron /
vancim      6131  0.1  1.3 34564524 218608 pts/0 Sl+  20:32   0:14 /usr/lib/claude-desktop/node_modules/electron/dist/electron --
vancim      4959  0.5  1.2 1461345800 201436 ?   SLsl 20:31   0:43 /snap/code/202/usr/share/code/code --no-sandbox --force-user-e
```

## 🐳 MÉTRICAS DO DOCKER

### Status dos Containers
```
## ⚡ MÉTRICAS DE PERFORMANCE

### Métricas do Sistema de Monitoramento
```
❌ Endpoint de métricas inacessível
```

### SLA Metrics Atuais
```
SLA metrics não disponíveis via API
```

### Response Times dos Logs
```
Response times (ms) - estatísticas:
Count: 100
Min: ms
Max: ms
Avg: 0ms
P50: ms
P95: ms
P99: ms
```

### Throughput (Requisições por Minuto)
```
Últimas 60 minutos:
## 💼 MÉTRICAS DE NEGÓCIO

### Métricas Atuais via API
```
Métricas de negócio não disponíveis via API
```

### Análise dos Logs de Negócio
```
Arquivos de métricas encontrados:
total 128
drwxr-xr-x 2 vancim vancim   4096 ago  8 18:16 .
drwxr-xr-x 7 vancim vancim   4096 ago  9 20:53 ..
-rw-rw-r-- 1 vancim vancim 117430 ago  8 18:43 metrics_20250808.jsonl

Últimas métricas registradas:
```

### Atividade de Conversas (Últimos 7 dias)
```
## 📋 ANÁLISE DE LOGS DE APLICAÇÃO

**Período**: Últimos 1 dia(s)

### Estatísticas Gerais
```
Total de linhas de log:
455 /home/vancim/whats_agent/logs/test_suite.log

Logs por nível:
## 🚨 ANÁLISE DE ALERTAS

### Alertas Ativos
```
Endpoint de alertas não acessível
```

### Histórico de Alertas (Últimos 7 dias)
```
Alertas por dia:
2025-08-09: 0 arquivos de alerta
2025-08-08: 0 arquivos de alerta
2025-08-07: 0 arquivos de alerta
2025-08-06: 0 arquivos de alerta
2025-08-05: 0 arquivos de alerta
2025-08-04: 0 arquivos de alerta
2025-08-03: 0 arquivos de alerta

Últimos 10 alertas:
```

### Alertas por Severidade (Últimos 7 dias)
```
## 🎯 RECOMENDAÇÕES E AÇÕES

### Recomendações de Infraestrutura

🔴 **URGENTE**: Espaço em disco crítico (97%)
- Executar limpeza de logs: `find logs/ -name '*.log' -mtime +7 -delete`
- Executar limpeza do Docker: `docker system prune -f`
- Considerar aumentar capacidade de disco

### Recomendações de Aplicação

🔴 **CRÍTICO**: Sistema não responde a health checks
- Executar diagnóstico: `./scripts/emergency/emergency_diagnosis.sh`
- Considerar restart: `./scripts/emergency/auto_recovery.sh`
- Escalar para equipe técnica se necessário

### Recomendações de Manutenção

📅 **Manutenção Preventiva Recomendada**:
- Backup manual: `./scripts/backup_manual.sh`
- Atualização de dependências (verificar vulnerabilidades)
- Revisão de logs de segurança
- Teste de procedures de recovery

📊 **Monitoramento Contínuo**:
- Configurar alertas proativos se não configurados
- Implementar monitoramento de SLA se necessário
- Revisar thresholds de alerta baseados no histórico


---

**Relatório gerado automaticamente**  
**Próximo relatório**: 2025-08-10
**Para mais informações**: `./scripts/emergency/operational_reports.sh --help`

