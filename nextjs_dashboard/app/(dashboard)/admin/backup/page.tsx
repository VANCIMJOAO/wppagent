"use client";

import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Database,
  Download,
  Play,
  Settings,
  Trash2,
  Clock,
  CheckCircle,
  AlertTriangle,
  RefreshCw,
  HardDrive,
  Cloud,
  Calendar,
  FileText,
  Activity,
  Shield,
  Zap
} from 'lucide-react';
import { toast } from 'sonner';
// import api from '@/lib/api-service'; // Removido - usar fetch diretamente

interface BackupInfo {
  filename: string;
  size: number;
  created_at: string;
  backup_type: string;
  status: string;
  cloud_uploaded: boolean;
  integrity_verified: boolean;
  error_message?: string;
}

interface BackupStatus {
  total_backups: number;
  last_backup: string;
  next_scheduled: string;
  storage_used: number;
  storage_available: number;
  backup_health: string;
  scheduler_running: boolean;
  backups: BackupInfo[];
}

interface BackupConfig {
  cron_schedule: string;
  enabled: boolean;
  max_backups: number;
  compression_enabled: boolean;
  cloud_upload_enabled: boolean;
  retention_days: number;
}

interface BackupLog {
  timestamp: string;
  level: string;
  message: string;
  backup_type?: string;
  status?: string;
}

export default function BackupManagementPage() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [loading, setLoading] = useState(true);
  const [backupStatus, setBackupStatus] = useState<BackupStatus | null>(null);
  const [backupConfig, setBackupConfig] = useState<BackupConfig | null>(null);
  const [backupLogs, setBackupLogs] = useState<BackupLog[]>([]);
  const [triggerDialog, setTriggerDialog] = useState(false);
  const [cleanupDialog, setCleanupDialog] = useState(false);
  const [selectedBackupType, setSelectedBackupType] = useState('full');
  const [cloudUpload, setCloudUpload] = useState(true);
  const [triggering, setTriggering] = useState(false);
  const [cleaning, setCleaning] = useState(false);

  // Load data on component mount
  useEffect(() => {
    loadBackupData();
  }, []);

  const loadBackupData = async () => {
    try {
      setLoading(true);
      await Promise.all([
        loadBackupStatus(),
        loadBackupConfig(),
        loadBackupLogs()
      ]);
    } catch (error) {
      console.error('Erro ao carregar dados de backup:', error);
      toast.error('Erro ao carregar dados de backup');
    } finally {
      setLoading(false);
    }
  };

  const loadBackupStatus = async () => {
    try {
      const response = await fetch('/api/admin/backup/status', {
        credentials: 'include'
      });
      const data = await response.json();
      setBackupStatus(data);
    } catch (error) {
      console.error('Erro ao carregar status de backup:', error);
    }
  };

  const loadBackupConfig = async () => {
    try {
      const response = await fetch('/api/admin/backup/config', {
        credentials: 'include'
      });
      const data = await response.json();
      setBackupConfig(data);
    } catch (error) {
      console.error('Erro ao carregar configuração de backup:', error);
    }
  };

  const loadBackupLogs = async () => {
    try {
      const response = await fetch('/api/admin/backup/logs', {
        credentials: 'include'
      });
      const data = await response.json();
      setBackupLogs(data.logs || []);
    } catch (error) {
      console.error('Erro ao carregar logs de backup:', error);
    }
  };

  const triggerBackup = async () => {
    try {
      setTriggering(true);
      const response = await fetch('/api/admin/backup/trigger', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({
          backup_type: selectedBackupType,
          cloud_upload: cloudUpload
        })
      });
      
      toast.success('Backup iniciado com sucesso!');
      setTriggerDialog(false);
      loadBackupData(); // Refresh data
    } catch (error) {
      console.error('Erro ao iniciar backup:', error);
      toast.error('Erro ao iniciar backup');
    } finally {
      setTriggering(false);
    }
  };

  const downloadBackup = async (filename: string) => {
    try {
      const response = await fetch(`/api/admin/backup/download/${filename}`, {
        credentials: 'include'
      });
      
      const data = await response.blob();
      const blob = new Blob([data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      toast.success('Download iniciado!');
    } catch (error) {
      console.error('Erro ao baixar backup:', error);
      toast.error('Erro ao baixar backup');
    }
  };

  const cleanupBackups = async () => {
    try {
      setCleaning(true);
      const response = await fetch('/api/admin/backup/cleanup');
      
      toast.success('Limpeza de backups executada!');
      setCleanupDialog(false);
      loadBackupData(); // Refresh data
    } catch (error) {
      console.error('Erro ao executar limpeza:', error);
      toast.error('Erro ao executar limpeza');
    } finally {
      setCleaning(false);
    }
  };

  const verifyBackup = async (filename: string) => {
    try {
      const response = await fetch(`/admin/backup/verify/${filename}`);
      toast.success('Verificação de integridade concluída!');
      loadBackupData(); // Refresh data
    } catch (error) {
      console.error('Erro ao verificar backup:', error);
      toast.error('Erro ao verificar backup');
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('pt-BR');
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge variant="default" className="flex items-center gap-1"><CheckCircle className="w-3 h-3" />Concluído</Badge>;
      case 'failed':
        return <Badge variant="destructive" className="flex items-center gap-1"><AlertTriangle className="w-3 h-3" />Falhou</Badge>;
      case 'running':
        return <Badge variant="secondary" className="flex items-center gap-1"><RefreshCw className="w-3 h-3" />Executando</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getHealthBadge = (health: string) => {
    switch (health) {
      case 'healthy':
        return <Badge variant="default" className="flex items-center gap-1"><CheckCircle className="w-3 h-3" />Saudável</Badge>;
      case 'warning':
        return <Badge variant="secondary" className="flex items-center gap-1"><AlertTriangle className="w-3 h-3" />Atenção</Badge>;
      case 'critical':
        return <Badge variant="destructive" className="flex items-center gap-1"><AlertTriangle className="w-3 h-3" />Crítico</Badge>;
      default:
        return <Badge variant="outline">{health}</Badge>;
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Gestão de Backups</h1>
            <p className="text-muted-foreground">Gerencie backups do sistema e banco de dados</p>
          </div>
        </div>
        <div className="grid gap-6">
          <Skeleton className="h-32" />
          <Skeleton className="h-64" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Database className="w-8 h-8 text-blue-600" />
            Gestão de Backups
          </h1>
          <p className="text-muted-foreground">
            Gerencie backups do sistema, banco de dados e arquivos
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={loadBackupData} variant="outline">
            <RefreshCw className="w-4 h-4 mr-2" />
            Atualizar
          </Button>
          <Dialog open={triggerDialog} onOpenChange={setTriggerDialog}>
            <DialogTrigger asChild>
              <Button>
                <Play className="w-4 h-4 mr-2" />
                Executar Backup
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Executar Backup Manual</DialogTitle>
                <DialogDescription>
                  Selecione o tipo de backup e configurações desejadas.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium">Tipo de Backup</label>
                  <Select value={selectedBackupType} onValueChange={setSelectedBackupType}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="full">Backup Completo</SelectItem>
                      <SelectItem value="database">Apenas Banco de Dados</SelectItem>
                      <SelectItem value="redis">Apenas Redis</SelectItem>
                      <SelectItem value="files">Apenas Arquivos</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="cloud-upload"
                    checked={cloudUpload}
                    onChange={(e) => setCloudUpload(e.target.checked)}
                  />
                  <label htmlFor="cloud-upload" className="text-sm">
                    Upload para nuvem
                  </label>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setTriggerDialog(false)}>
                  Cancelar
                </Button>
                <Button onClick={triggerBackup} disabled={triggering}>
                  {triggering ? 'Executando...' : 'Executar Backup'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Status Alert */}
      {backupStatus && (
        <Alert>
          <Activity className="h-4 w-4" />
          <AlertDescription>
            <strong>Status do Sistema:</strong> {getHealthBadge(backupStatus.backup_health)}
            {backupStatus.scheduler_running ? ' | Agendador ativo' : ' | Agendador inativo'}
            {backupStatus.last_backup && ` | Último backup: ${formatDate(backupStatus.last_backup)}`}
          </AlertDescription>
        </Alert>
      )}

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="dashboard" className="flex items-center gap-2">
            <Activity className="w-4 h-4" />
            Dashboard
          </TabsTrigger>
          <TabsTrigger value="backups" className="flex items-center gap-2">
            <Database className="w-4 h-4" />
            Backups
          </TabsTrigger>
          <TabsTrigger value="config" className="flex items-center gap-2">
            <Settings className="w-4 h-4" />
            Configuração
          </TabsTrigger>
          <TabsTrigger value="logs" className="flex items-center gap-2">
            <FileText className="w-4 h-4" />
            Logs
          </TabsTrigger>
          <TabsTrigger value="tools" className="flex items-center gap-2">
            <Shield className="w-4 h-4" />
            Ferramentas
          </TabsTrigger>
        </TabsList>

        {/* Dashboard Tab */}
        <TabsContent value="dashboard" className="space-y-6">
          {backupStatus && (
            <>
              {/* Status Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center gap-3">
                      <Database className="w-8 h-8 text-blue-600" />
                      <div>
                        <p className="text-sm font-medium">Total de Backups</p>
                        <p className="text-2xl font-bold">{backupStatus.total_backups}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center gap-3">
                      <HardDrive className="w-8 h-8 text-green-600" />
                      <div>
                        <p className="text-sm font-medium">Armazenamento</p>
                        <p className="text-2xl font-bold">{formatFileSize(backupStatus.storage_used)}</p>
                        <p className="text-xs text-muted-foreground">
                          de {formatFileSize(backupStatus.storage_available)} disponível
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center gap-3">
                      <Clock className="w-8 h-8 text-purple-600" />
                      <div>
                        <p className="text-sm font-medium">Último Backup</p>
                        <p className="text-sm font-bold">
                          {backupStatus.last_backup ? formatDate(backupStatus.last_backup) : 'Nunca'}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center gap-3">
                      <Calendar className="w-8 h-8 text-orange-600" />
                      <div>
                        <p className="text-sm font-medium">Próximo Backup</p>
                        <p className="text-sm font-bold">
                          {backupStatus.next_scheduled ? formatDate(backupStatus.next_scheduled) : 'Não agendado'}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Recent Backups */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Database className="w-5 h-5" />
                    Backups Recentes
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Arquivo</TableHead>
                        <TableHead>Tipo</TableHead>
                        <TableHead>Tamanho</TableHead>
                        <TableHead>Data</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Ações</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {backupStatus.backups.slice(0, 5).map((backup) => (
                        <TableRow key={backup.filename}>
                          <TableCell className="font-mono text-sm">{backup.filename}</TableCell>
                          <TableCell>
                            <Badge variant="outline">{backup.backup_type}</Badge>
                          </TableCell>
                          <TableCell>{formatFileSize(backup.size)}</TableCell>
                          <TableCell>{formatDate(backup.created_at)}</TableCell>
                          <TableCell>{getStatusBadge(backup.status)}</TableCell>
                          <TableCell>
                            <div className="flex gap-1">
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => downloadBackup(backup.filename)}
                              >
                                <Download className="w-3 h-3" />
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => verifyBackup(backup.filename)}
                              >
                                <Shield className="w-3 h-3" />
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>

        {/* Backups Tab */}
        <TabsContent value="backups" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <Database className="w-5 h-5" />
                  Lista de Backups
                </span>
                <div className="flex gap-2">
                  <Select>
                    <SelectTrigger className="w-40">
                      <SelectValue placeholder="Filtrar por tipo" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Todos</SelectItem>
                      <SelectItem value="full">Completo</SelectItem>
                      <SelectItem value="database">Banco</SelectItem>
                      <SelectItem value="redis">Redis</SelectItem>
                      <SelectItem value="files">Arquivos</SelectItem>
                    </SelectContent>
                  </Select>
                  <Button variant="outline" onClick={loadBackupData}>
                    <RefreshCw className="w-4 h-4" />
                  </Button>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Arquivo</TableHead>
                    <TableHead>Tipo</TableHead>
                    <TableHead>Tamanho</TableHead>
                    <TableHead>Data</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Nuvem</TableHead>
                    <TableHead>Integridade</TableHead>
                    <TableHead>Ações</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {backupStatus?.backups.map((backup) => (
                    <TableRow key={backup.filename}>
                      <TableCell className="font-mono text-sm">{backup.filename}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{backup.backup_type}</Badge>
                      </TableCell>
                      <TableCell>{formatFileSize(backup.size)}</TableCell>
                      <TableCell>{formatDate(backup.created_at)}</TableCell>
                      <TableCell>{getStatusBadge(backup.status)}</TableCell>
                      <TableCell>
                        {backup.cloud_uploaded ? (
                          <Badge variant="default" className="flex items-center gap-1 w-fit">
                            <Cloud className="w-3 h-3" />
                            Sim
                          </Badge>
                        ) : (
                          <Badge variant="outline">Não</Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        {backup.integrity_verified ? (
                          <Badge variant="default" className="flex items-center gap-1 w-fit">
                            <CheckCircle className="w-3 h-3" />
                            OK
                          </Badge>
                        ) : (
                          <Badge variant="secondary">Não verificado</Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-1">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => downloadBackup(backup.filename)}
                          >
                            <Download className="w-3 h-3" />
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => verifyBackup(backup.filename)}
                          >
                            <Shield className="w-3 h-3" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Config Tab */}
        <TabsContent value="config" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="w-5 h-5" />
                Configuração de Backups
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {backupConfig ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div>
                      <label className="text-sm font-medium">Agendamento (Cron)</label>
                      <p className="text-sm text-muted-foreground font-mono">{backupConfig.cron_schedule}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium">Status</label>
                      <p className="text-sm">
                        {backupConfig.enabled ? (
                          <Badge variant="default" className="flex items-center gap-1 w-fit">
                            <CheckCircle className="w-3 h-3" />
                            Ativo
                          </Badge>
                        ) : (
                          <Badge variant="secondary">Inativo</Badge>
                        )}
                      </p>
                    </div>
                    <div>
                      <label className="text-sm font-medium">Máximo de Backups</label>
                      <p className="text-sm">{backupConfig.max_backups}</p>
                    </div>
                  </div>
                  <div className="space-y-4">
                    <div>
                      <label className="text-sm font-medium">Compressão</label>
                      <p className="text-sm">
                        {backupConfig.compression_enabled ? (
                          <Badge variant="default" className="flex items-center gap-1 w-fit">
                            <CheckCircle className="w-3 h-3" />
                            Habilitada
                          </Badge>
                        ) : (
                          <Badge variant="secondary">Desabilitada</Badge>
                        )}
                      </p>
                    </div>
                    <div>
                      <label className="text-sm font-medium">Upload para Nuvem</label>
                      <p className="text-sm">
                        {backupConfig.cloud_upload_enabled ? (
                          <Badge variant="default" className="flex items-center gap-1 w-fit">
                            <Cloud className="w-3 h-3" />
                            Habilitado
                          </Badge>
                        ) : (
                          <Badge variant="secondary">Desabilitado</Badge>
                        )}
                      </p>
                    </div>
                    <div>
                      <label className="text-sm font-medium">Retenção (dias)</label>
                      <p className="text-sm">{backupConfig.retention_days}</p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <Settings className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">Carregando configuração...</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Logs Tab */}
        <TabsContent value="logs" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="w-5 h-5" />
                Logs de Backup
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {backupLogs.map((log, index) => (
                  <div key={index} className="flex items-start gap-3 p-3 border rounded-lg">
                    <div className="flex-shrink-0">
                      {log.level === 'ERROR' ? (
                        <AlertTriangle className="w-4 h-4 text-red-500" />
                      ) : log.level === 'WARNING' ? (
                        <AlertTriangle className="w-4 h-4 text-yellow-500" />
                      ) : (
                        <CheckCircle className="w-4 h-4 text-green-500" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-mono text-muted-foreground">
                          {formatDate(log.timestamp)}
                        </span>
                        <Badge variant="outline" className="text-xs">
                          {log.level}
                        </Badge>
                        {log.backup_type && (
                          <Badge variant="secondary" className="text-xs">
                            {log.backup_type}
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm">{log.message}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tools Tab */}
        <TabsContent value="tools" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Trash2 className="w-5 h-5" />
                  Limpeza de Backups
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  Remove backups antigos conforme a política de retenção configurada.
                </p>
                <Dialog open={cleanupDialog} onOpenChange={setCleanupDialog}>
                  <DialogTrigger asChild>
                    <Button variant="destructive">
                      <Trash2 className="w-4 h-4 mr-2" />
                      Executar Limpeza
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Confirmar Limpeza</DialogTitle>
                      <DialogDescription>
                        Esta ação irá remover backups antigos conforme a política de retenção. 
                        Esta ação não pode ser desfeita.
                      </DialogDescription>
                    </DialogHeader>
                    <DialogFooter>
                      <Button variant="outline" onClick={() => setCleanupDialog(false)}>
                        Cancelar
                      </Button>
                      <Button variant="destructive" onClick={cleanupBackups} disabled={cleaning}>
                        {cleaning ? 'Executando...' : 'Confirmar Limpeza'}
                      </Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="w-5 h-5" />
                  Verificação de Integridade
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  Verifica a integridade de todos os backups disponíveis.
                </p>
                <Button variant="outline" onClick={() => {
                  backupStatus?.backups.forEach(backup => {
                    if (backup.status === 'completed') {
                      verifyBackup(backup.filename);
                    }
                  });
                }}>
                  <Shield className="w-4 h-4 mr-2" />
                  Verificar Todos
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
