'use client'

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { 
  Clock, 
  Calendar, 
  Ban, 
  Search,
  Filter,
  UserX,
  CalendarX,
  Repeat,
  AlertTriangle
} from "lucide-react"

interface BlockedTime {
  id: number;
  start_time: string;
  end_time: string;
  reason: string;
  notes: string;
  is_recurring: boolean;
  created_at: string;
}

export default function BloqueadosPage() {
  const [blockedTimes, setBlockedTimes] = useState<BlockedTime[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState("all");

  // Simular carregamento de dados (conectar com API depois)
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      
      // Dados simulados baseados no banco PostgreSQL
      const mockData: BlockedTime[] = [
        {
          id: 1,
          start_time: "2025-09-05T09:00:00Z",
          end_time: "2025-09-05T10:00:00Z", 
          reason: "Reunião administrativa",
          notes: "Reunião semanal de equipe",
          is_recurring: true,
          created_at: "2025-09-01T14:30:00Z"
        },
        {
          id: 2,
          start_time: "2025-09-06T12:00:00Z",
          end_time: "2025-09-06T13:00:00Z",
          reason: "Almoço",
          notes: "Horário de almoço bloqueado",
          is_recurring: true,
          created_at: "2025-09-01T08:00:00Z"
        },
        {
          id: 3,
          start_time: "2025-09-10T15:00:00Z",
          end_time: "2025-09-10T17:00:00Z",
          reason: "Manutenção do sistema",
          notes: "Atualização mensal do sistema",
          is_recurring: false,
          created_at: "2025-09-03T10:15:00Z"
        },
        {
          id: 4,
          start_time: "2025-09-07T08:00:00Z",
          end_time: "2025-09-07T09:00:00Z",
          reason: "Treinamento",
          notes: "Treinamento de novos funcionários",
          is_recurring: false,
          created_at: "2025-09-02T16:45:00Z"
        },
        {
          id: 5,
          start_time: "2025-09-11T18:00:00Z",
          end_time: "2025-09-11T19:00:00Z",
          reason: "Fechamento diário",
          notes: "Processamento de dados diário",
          is_recurring: true,
          created_at: "2025-08-28T11:20:00Z"
        }
      ];

      // Simular delay da API
      await new Promise(resolve => setTimeout(resolve, 800));
      setBlockedTimes(mockData);
      setLoading(false);
    };

    loadData();
  }, []);

  // Filtrar dados baseado na busca e filtro
  const filteredData = blockedTimes.filter(item => {
    const matchesSearch = item.reason.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         item.notes.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesFilter = filterType === "all" ||
                         (filterType === "recurring" && item.is_recurring) ||
                         (filterType === "one-time" && !item.is_recurring);
    
    return matchesSearch && matchesFilter;
  });

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
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-red-600 via-orange-600 to-red-800 text-white rounded-lg p-8">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold mb-2">Horários Bloqueados</h1>
            <p className="text-red-100 opacity-90">
              Gerenciamento de indisponibilidades e bloqueios • {totalBlocked} registros
            </p>
          </div>
          <div className="bg-white/20 backdrop-blur-sm rounded-lg p-3">
            <Clock className="h-6 w-6" />
          </div>
        </div>
      </div>

      {/* Métricas */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="overflow-hidden transition-all duration-300 hover:shadow-lg hover:-translate-y-1">
          <CardHeader className="bg-gradient-to-r from-red-500 to-red-600 text-white pb-4">
            <div className="flex items-center justify-between">
              <div className="p-3 bg-white/20 rounded-lg backdrop-blur-sm border border-white/30">
                <Ban size={24} />
              </div>
              <div className="text-right">
                <CardTitle className="text-2xl font-bold text-white mb-1">
                  {totalBlocked}
                </CardTitle>
                <p className="text-white/90 text-sm font-medium">Total Bloqueados</p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-4 bg-gray-50">
            <p className="text-sm text-gray-600">Todos os horários indisponíveis</p>
          </CardContent>
        </Card>

        <Card className="overflow-hidden transition-all duration-300 hover:shadow-lg hover:-translate-y-1">
          <CardHeader className="bg-gradient-to-r from-orange-500 to-orange-600 text-white pb-4">
            <div className="flex items-center justify-between">
              <div className="p-3 bg-white/20 rounded-lg backdrop-blur-sm border border-white/30">
                <Repeat size={24} />
              </div>
              <div className="text-right">
                <CardTitle className="text-2xl font-bold text-white mb-1">
                  {recurring}
                </CardTitle>
                <p className="text-white/90 text-sm font-medium">Recorrentes</p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-4 bg-gray-50">
            <p className="text-sm text-gray-600">Bloqueios que se repetem</p>
          </CardContent>
        </Card>

        <Card className="overflow-hidden transition-all duration-300 hover:shadow-lg hover:-translate-y-1">
          <CardHeader className="bg-gradient-to-r from-yellow-500 to-yellow-600 text-white pb-4">
            <div className="flex items-center justify-between">
              <div className="p-3 bg-white/20 rounded-lg backdrop-blur-sm border border-white/30">
                <CalendarX size={24} />
              </div>
              <div className="text-right">
                <CardTitle className="text-2xl font-bold text-white mb-1">
                  {oneTime}
                </CardTitle>
                <p className="text-white/90 text-sm font-medium">Únicos</p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-4 bg-gray-50">
            <p className="text-sm text-gray-600">Bloqueios pontuais</p>
          </CardContent>
        </Card>

        <Card className="overflow-hidden transition-all duration-300 hover:shadow-lg hover:-translate-y-1">
          <CardHeader className="bg-gradient-to-r from-blue-500 to-blue-600 text-white pb-4">
            <div className="flex items-center justify-between">
              <div className="p-3 bg-white/20 rounded-lg backdrop-blur-sm border border-white/30">
                <Calendar size={24} />
              </div>
              <div className="text-right">
                <CardTitle className="text-2xl font-bold text-white mb-1">
                  {upcoming}
                </CardTitle>
                <p className="text-white/90 text-sm font-medium">Próximos 7 Dias</p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-4 bg-gray-50">
            <p className="text-sm text-gray-600">Bloqueios iminentes</p>
          </CardContent>
        </Card>
      </div>

      {/* Filtros e Busca */}
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Buscar por motivo ou observações..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <Button
                variant={filterType === "all" ? "default" : "outline"}
                onClick={() => setFilterType("all")}
                className="flex items-center gap-2"
              >
                <Filter className="h-4 w-4" />
                Todos
              </Button>
              <Button
                variant={filterType === "recurring" ? "default" : "outline"}
                onClick={() => setFilterType("recurring")}
                className="flex items-center gap-2"
              >
                <Repeat className="h-4 w-4" />
                Recorrentes
              </Button>
              <Button
                variant={filterType === "one-time" ? "default" : "outline"}
                onClick={() => setFilterType("one-time")}
                className="flex items-center gap-2"
              >
                <CalendarX className="h-4 w-4" />
                Únicos
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabela de Horários Bloqueados */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center text-xl">
            <AlertTriangle className="h-6 w-6 mr-2 text-red-600" />
            Horários Bloqueados ({filteredData.length} registros)
          </CardTitle>
        </CardHeader>
        <CardContent>
          {filteredData.length === 0 ? (
            <div className="text-center py-12">
              <UserX className="h-16 w-16 text-gray-400 mx-auto mb-4" />
              <p className="text-xl font-semibold text-gray-600 mb-2">Nenhum resultado encontrado</p>
              <p className="text-gray-500">Tente ajustar os filtros ou termo de busca</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Período</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Motivo</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Observações</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Tipo</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Criado em</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredData.map((item, index) => (
                    <tr 
                      key={item.id}
                      className={`border-b border-gray-100 hover:bg-gray-50 transition-colors ${
                        index % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'
                      }`}
                    >
                      <td className="py-4 px-4">
                        <div>
                          <div className="font-medium text-gray-900">
                            {new Date(item.start_time).toLocaleDateString('pt-BR', {
                              day: '2-digit',
                              month: '2-digit',
                              year: 'numeric'
                            })}
                          </div>
                          <div className="text-sm text-gray-600">
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
                      <td className="py-4 px-4">
                        <span className="font-medium text-gray-900">{item.reason}</span>
                      </td>
                      <td className="py-4 px-4">
                        <span className="text-gray-600">{item.notes}</span>
                      </td>
                      <td className="py-4 px-4">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          item.is_recurring 
                            ? 'bg-blue-100 text-blue-800' 
                            : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {item.is_recurring ? (
                            <>
                              <Repeat className="h-3 w-3 mr-1" />
                              Recorrente
                            </>
                          ) : (
                            <>
                              <CalendarX className="h-3 w-3 mr-1" />
                              Único
                            </>
                          )}
                        </span>
                      </td>
                      <td className="py-4 px-4">
                        <span className="text-sm text-gray-500">
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
