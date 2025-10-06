'use client'

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { debugLog } from '@/lib/debug';
import {
  Clock,
  Calendar,
  Ban,
  Search,
  Filter,
  UserX,
  CalendarX,
  Repeat,
  AlertTriangle,
  RefreshCw
} from "lucide-react"

interface BlockedTime {
  id: string;
  business_id?: string;
  business_name?: string;
  start_time: string;
  end_time: string;
  start_date: string;
  end_date: string;
  reason: string;
  notes: string;
  block_type: string;
  is_recurring: boolean;
  recurrence_pattern?: any;
  created_at: string;
  created_by: string;
}

export default function BloqueadosPage() {
  const [blockedTimes, setBlockedTimes] = useState<BlockedTime[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState("all");

  // Carregar dados reais da API
  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams();
      if (searchTerm) params.append('search', searchTerm);
      if (filterType !== 'all') params.append('filterType', filterType);
      params.append('limit', '100');
      params.append('offset', '0');

      const response = await fetch(`/api/blocked-times?${params.toString()}`);
      const data = await response.json();

      if (data.success) {
        setBlockedTimes(data.data || data.blockedTimes || []);
      } else {
        setError(data.error || 'Erro ao carregar horários bloqueados');
        setBlockedTimes([]);
      }
    } catch (err) {
      debugLog.error('Erro ao carregar horários bloqueados:', err);
      setError(err instanceof Error ? err.message : 'Erro de rede ou servidor');
      setBlockedTimes([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [searchTerm, filterType]);

  // Usar dados diretamente da API (já filtrados)
  const filteredData = blockedTimes;

  // Calcular métricas
  const totalBlocked = blockedTimes.length;
  const recurring = blockedTimes.filter(item => item.is_recurring).length;
  const oneTime = totalBlocked - recurring;

  // Próximos 7 dias
  const nextWeek = new Date();
  nextWeek.setDate(nextWeek.getDate() + 7);
  const upcoming = blockedTimes.filter(item => {
    const startDate = new Date(item.start_time);
    return startDate >= new Date() && startDate <= nextWeek;
  }).length;

  if (loading) {
    return (
      <div className="space-y-6">
        {/* Loading Header */}
        <div className="bg-gradient-to-r from-red-600 via-orange-600 to-red-800 text-white rounded-lg p-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold mb-2">Horários Bloqueados</h1>
              <p className="text-red-100 opacity-90">Carregando dados...</p>
            </div>
            <div className="bg-white/20 backdrop-blur-sm rounded-lg p-3">
              <Clock className="h-6 w-6" />
            </div>
          </div>
        </div>

        {/* Loading State */}
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600"></div>
          <span className="ml-3 text-gray-600 text-lg">Carregando horários bloqueados...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 p-6 bg-gradient-to-br from-gray-50 to-white min-h-screen">
      {/* Header */}
      <div className="bg-gradient-to-r from-red-600 via-orange-600 to-red-800 text-white rounded-xl shadow-2xl p-10">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-4xl font-bold mb-3 tracking-tight">Horários Bloqueados</h1>
            <p className="text-red-100 text-lg">
              Gerenciamento de indisponibilidades e bloqueios
            </p>
            <div className="mt-4">
              <span className="inline-flex items-center px-4 py-2 rounded-full text-sm font-semibold bg-white/20 backdrop-blur-sm border border-white/30">
                {totalBlocked} registros
              </span>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <Button 
              variant="outline" 
              onClick={loadData} 
              disabled={loading}
              className="h-11 bg-white/20 border-white/30 text-white hover:bg-white/30 shadow-lg hover:shadow-xl transition-all hover:scale-105"
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Atualizar
            </Button>
            <div className="bg-white/20 backdrop-blur-sm rounded-xl p-4 shadow-lg">
              <Clock className="h-7 w-7" />
            </div>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-4">
            <div className="flex items-center space-x-2 text-red-800">
              <AlertTriangle className="h-5 w-5" />
              <span className="font-medium">Erro ao carregar horários bloqueados:</span>
              <span>{error}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Métricas */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="border-0 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.02] overflow-hidden">
          <CardHeader className="bg-gradient-to-r from-red-500 to-red-600 text-white pb-6">
            <div className="flex items-center justify-between">
              <div className="p-4 bg-white/20 rounded-xl backdrop-blur-sm border border-white/30 shadow-lg">
                <Ban size={28} />
              </div>
              <div className="text-right">
                <CardTitle className="text-4xl font-bold text-white mb-2">
                  {totalBlocked}
                </CardTitle>
                <p className="text-white/90 text-sm font-semibold">Total Bloqueados</p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-5 bg-gradient-to-br from-white to-gray-50">
            <p className="text-sm text-gray-600 font-medium">Todos os horários indisponíveis</p>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.02] overflow-hidden">
          <CardHeader className="bg-gradient-to-r from-orange-500 to-orange-600 text-white pb-6">
            <div className="flex items-center justify-between">
              <div className="p-4 bg-white/20 rounded-xl backdrop-blur-sm border border-white/30 shadow-lg">
                <Repeat size={28} />
              </div>
              <div className="text-right">
                <CardTitle className="text-4xl font-bold text-white mb-2">
                  {recurring}
                </CardTitle>
                <p className="text-white/90 text-sm font-semibold">Recorrentes</p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-5 bg-gradient-to-br from-white to-gray-50">
            <p className="text-sm text-gray-600 font-medium">Bloqueios que se repetem</p>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.02] overflow-hidden">
          <CardHeader className="bg-gradient-to-r from-yellow-500 to-yellow-600 text-white pb-6">
            <div className="flex items-center justify-between">
              <div className="p-4 bg-white/20 rounded-xl backdrop-blur-sm border border-white/30 shadow-lg">
                <CalendarX size={28} />
              </div>
              <div className="text-right">
                <CardTitle className="text-4xl font-bold text-white mb-2">
                  {oneTime}
                </CardTitle>
                <p className="text-white/90 text-sm font-semibold">Únicos</p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-5 bg-gradient-to-br from-white to-gray-50">
            <p className="text-sm text-gray-600 font-medium">Bloqueios pontuais</p>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.02] overflow-hidden">
          <CardHeader className="bg-gradient-to-r from-blue-500 to-blue-600 text-white pb-6">
            <div className="flex items-center justify-between">
              <div className="p-4 bg-white/20 rounded-xl backdrop-blur-sm border border-white/30 shadow-lg">
                <Calendar size={28} />
              </div>
              <div className="text-right">
                <CardTitle className="text-4xl font-bold text-white mb-2">
                  {upcoming}
                </CardTitle>
                <p className="text-white/90 text-sm font-semibold">Próximos 7 Dias</p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-5 bg-gradient-to-br from-white to-gray-50">
            <p className="text-sm text-gray-600 font-medium">Bloqueios iminentes</p>
          </CardContent>
        </Card>
      </div>

      {/* Filtros e Busca */}
      <Card className="border-0 shadow-lg bg-gradient-to-br from-white to-gray-50">
        <CardContent className="p-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-3.5 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Buscar por motivo ou observações..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 h-11 border-gray-300 focus:ring-2 focus:ring-primary/20 transition-all"
                />
              </div>
            </div>
            <div className="flex gap-3">
              <Button
                variant={filterType === "all" ? "default" : "outline"}
                onClick={() => setFilterType("all")}
                className={`flex items-center gap-2 h-11 px-4 transition-all ${
                  filterType === "all" 
                    ? 'bg-gradient-to-r from-primary to-primary/90 shadow-md' 
                    : 'hover:bg-gray-100'
                }`}
              >
                <Filter className="h-4 w-4" />
                Todos
              </Button>
              <Button
                variant={filterType === "recurring" ? "default" : "outline"}
                onClick={() => setFilterType("recurring")}
                className={`flex items-center gap-2 h-11 px-4 transition-all ${
                  filterType === "recurring" 
                    ? 'bg-gradient-to-r from-primary to-primary/90 shadow-md' 
                    : 'hover:bg-gray-100'
                }`}
              >
                <Repeat className="h-4 w-4" />
                Recorrentes
              </Button>
              <Button
                variant={filterType === "one-time" ? "default" : "outline"}
                onClick={() => setFilterType("one-time")}
                className={`flex items-center gap-2 h-11 px-4 transition-all ${
                  filterType === "one-time" 
                    ? 'bg-gradient-to-r from-primary to-primary/90 shadow-md' 
                    : 'hover:bg-gray-100'
                }`}
              >
                <CalendarX className="h-4 w-4" />
                Únicos
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabela de Horários Bloqueados */}
      <Card className="border-0 shadow-xl bg-gradient-to-br from-white to-gray-50">
        <CardHeader className="border-b bg-gradient-to-r from-gray-50 to-transparent pb-5">
          <CardTitle className="flex items-center gap-3 text-2xl font-bold">
            <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-gradient-to-br from-red-500 to-red-600 shadow-lg">
              <AlertTriangle className="h-5 w-5 text-white" />
            </div>
            Horários Bloqueados
            <span className="text-lg font-normal text-gray-500">({filteredData.length} registros)</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-6">
          {filteredData.length === 0 ? (
            <div className="text-center py-16 bg-gradient-to-br from-gray-50 to-white rounded-lg">
              <div className="flex items-center justify-center w-20 h-20 mx-auto mb-6 rounded-full bg-gradient-to-br from-gray-300 to-gray-400 shadow-lg">
                <UserX className="h-10 w-10 text-white" />
              </div>
              <p className="text-2xl font-bold text-gray-700 mb-3">Nenhum resultado encontrado</p>
              <p className="text-gray-500 text-lg">Tente ajustar os filtros ou termo de busca</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b-2 border-gray-200 bg-gradient-to-r from-gray-50 to-transparent">
                    <th className="text-left py-4 px-5 font-bold text-gray-700 text-sm">Período</th>
                    <th className="text-left py-4 px-5 font-bold text-gray-700 text-sm">Motivo</th>
                    <th className="text-left py-4 px-5 font-bold text-gray-700 text-sm">Negócio</th>
                    <th className="text-left py-4 px-5 font-bold text-gray-700 text-sm">Tipo</th>
                    <th className="text-left py-4 px-5 font-bold text-gray-700 text-sm">Criado por</th>
                    <th className="text-left py-4 px-5 font-bold text-gray-700 text-sm">Criado em</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredData.map((item, index) => (
                    <tr
                      key={item.id}
                      className={`border-b border-gray-100 hover:bg-blue-50 transition-all duration-200 ${
                        index % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'
                      }`}
                    >
                      <td className="py-5 px-5">
                        <div>
                          <div className="font-bold text-gray-900 mb-1">
                            {new Date(item.start_time).toLocaleDateString('pt-BR', {
                              day: '2-digit',
                              month: '2-digit',
                              year: 'numeric'
                            })}
                          </div>
                          <div className="text-sm text-gray-600 font-medium">
                            {new Date(item.start_time).toLocaleTimeString('pt-BR', {
                              hour: '2-digit',
                              minute: '2-digit'
                            })} - {new Date(item.end_time).toLocaleTimeString('pt-BR', {
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </div>
                        </div>
                      </td>
                      <td className="py-5 px-5">
                        <span className="font-semibold text-gray-900">{item.reason}</span>
                      </td>
                      <td className="py-5 px-5">
                        <span className="text-gray-600 font-medium">{item.business_name || 'N/A'}</span>
                      </td>
                      <td className="py-5 px-5">
                        <div className="flex flex-col gap-2">
                          <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold shadow-sm ${
                            item.is_recurring
                              ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white'
                              : 'bg-gradient-to-r from-yellow-500 to-orange-600 text-white'
                          }`}>
                            {item.is_recurring ? (
                              <>
                                <Repeat className="h-3 w-3 mr-1.5" />
                                Recorrente
                              </>
                            ) : (
                              <>
                                <CalendarX className="h-3 w-3 mr-1.5" />
                                Único
                              </>
                            )}
                          </span>
                          <span className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold ${
                            item.block_type === 'manual' 
                              ? 'bg-gray-100 text-gray-800 border border-gray-300'
                              : item.block_type === 'automatic'
                              ? 'bg-green-100 text-green-800 border border-green-300'
                              : 'bg-purple-100 text-purple-800 border border-purple-300'
                          }`}>
                            {item.block_type}
                          </span>
                        </div>
                      </td>
                      <td className="py-5 px-5">
                        <span className="text-sm text-gray-700 font-medium">{item.created_by}</span>
                      </td>
                      <td className="py-5 px-5">
                        <span className="text-sm text-gray-600 font-medium">
                          {new Date(item.created_at).toLocaleDateString('pt-BR', {
                            day: '2-digit',
                            month: '2-digit',
                            year: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
