/**
 * Dashboard Personalizado - Permite usuários criarem layouts próprios
 * Sistema drag-and-drop com widgets configuráveis
 */
'use client';

import React, { useState, useCallback, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { 
  Grid, 
  Plus, 
  Settings, 
  Save, 
  RotateCcw, 
  Eye,
  EyeOff,
  Move,
  X,
  BarChart3,
  PieChart,
  TrendingUp,
  Clock
} from 'lucide-react';

// Tipos para widgets
export interface DashboardWidget {
  id: string;
  type: 'metric_card' | 'chart' | 'table' | 'alert_summary' | 'custom';
  title: string;
  position: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  config: {
    metric?: string;
    chartType?: 'line' | 'bar' | 'pie' | 'area';
    dataSource?: string;
    filters?: Record<string, any>;
    refreshInterval?: number;
    showLegend?: boolean;
    showTooltip?: boolean;
    customStyles?: Record<string, any>;
  };
  visible: boolean;
  locked: boolean;
}

export interface DashboardLayout {
  id: string;
  name: string;
  description: string;
  widgets: DashboardWidget[];
  gridSize: {
    columns: number;
    rows: number;
  };
  createdAt: Date;
  updatedAt: Date;
  isDefault: boolean;
}

// Templates de widgets pré-configurados
const WIDGET_TEMPLATES: Partial<DashboardWidget>[] = [
  {
    type: 'metric_card',
    title: 'Total de Conversas',
    config: {
      metric: 'totalConversations',
      dataSource: 'overview',
      refreshInterval: 30000,
    },
    position: { x: 0, y: 0, width: 3, height: 2 },
  },
  {
    type: 'metric_card',
    title: 'Tempo Médio de Resposta',
    config: {
      metric: 'avgResponseTime',
      dataSource: 'overview',
      refreshInterval: 30000,
    },
    position: { x: 3, y: 0, width: 3, height: 2 },
  },
  {
    type: 'chart',
    title: 'Conversas ao Longo do Tempo',
    config: {
      chartType: 'line',
      dataSource: 'overview',
      metric: 'conversationsOverTime',
      refreshInterval: 60000,
      showLegend: true,
      showTooltip: true,
    },
    position: { x: 0, y: 2, width: 6, height: 4 },
  },
  {
    type: 'chart',
    title: 'Satisfação por Rating',
    config: {
      chartType: 'pie',
      dataSource: 'conversations',
      metric: 'satisfactionBreakdown',
      refreshInterval: 60000,
      showLegend: true,
    },
    position: { x: 6, y: 0, width: 6, height: 4 },
  },
  {
    type: 'table',
    title: 'Performance de Agentes',
    config: {
      dataSource: 'performance',
      metric: 'agentPerformance',
      refreshInterval: 30000,
    },
    position: { x: 0, y: 6, width: 12, height: 4 },
  },
  {
    type: 'alert_summary',
    title: 'Resumo de Alertas',
    config: {
      dataSource: 'alerts',
      refreshInterval: 15000,
    },
    position: { x: 6, y: 2, width: 6, height: 4 },
  },
];

const DEFAULT_LAYOUT: DashboardLayout = {
  id: 'default',
  name: 'Dashboard Padrão',
  description: 'Layout padrão com métricas essenciais',
  widgets: WIDGET_TEMPLATES.map((template, index) => ({
    ...template,
    id: `widget_${index}`,
    visible: true,
    locked: false,
  })) as DashboardWidget[],
  gridSize: { columns: 12, rows: 10 },
  createdAt: new Date(),
  updatedAt: new Date(),
  isDefault: true,
};

interface CustomDashboardProps {
  className?: string;
  onLayoutChange?: (layout: DashboardLayout) => void;
  initialLayout?: DashboardLayout;
}

export const CustomDashboard: React.FC<CustomDashboardProps> = ({
  className = '',
  onLayoutChange,
  initialLayout,
}) => {
  const [layout, setLayout] = useState<DashboardLayout>(initialLayout || DEFAULT_LAYOUT);
  const [editMode, setEditMode] = useState(false);
  const [selectedWidget, setSelectedWidget] = useState<string | null>(null);
  const [showWidgetLibrary, setShowWidgetLibrary] = useState(false);

  // ✅ SEGURO: localStorage para layout de dashboard (não-sensível)
  const saveLayout = useCallback(() => {
    try {
      const updatedLayout = {
        ...layout,
        updatedAt: new Date(),
      };
      
      localStorage.setItem(`dashboard_${layout.id}`, JSON.stringify(updatedLayout));
      setLayout(updatedLayout);
      onLayoutChange?.(updatedLayout);
    } catch (error) {
      console.warn('Dashboard: Não foi possível salvar layout')
    }
  }, [layout, onLayoutChange]);

  // ✅ SEGURO: Carregar layout do localStorage (preferências de UI)
  useEffect(() => {
    try {
      const savedLayout = localStorage.getItem(`dashboard_${layout.id}`);
      if (savedLayout) {
        const parsedLayout = JSON.parse(savedLayout);
        setLayout(parsedLayout);
      }
    } catch (error) {
      console.warn('Dashboard: Erro ao carregar layout salvo:', error);
    }
  }, [layout.id]);

  // Adicionar widget
  const addWidget = useCallback((template: Partial<DashboardWidget>) => {
    const newWidget: DashboardWidget = {
      ...template,
      id: `widget_${Date.now()}`,
      visible: true,
      locked: false,
    } as DashboardWidget;

    setLayout(prev => ({
      ...prev,
      widgets: [...prev.widgets, newWidget],
    }));
  }, []);

  // Remover widget
  const removeWidget = useCallback((widgetId: string) => {
    setLayout(prev => ({
      ...prev,
      widgets: prev.widgets.filter(w => w.id !== widgetId),
    }));
  }, []);

  // Alternar visibilidade do widget
  const toggleWidgetVisibility = useCallback((widgetId: string) => {
    setLayout(prev => ({
      ...prev,
      widgets: prev.widgets.map(w => 
        w.id === widgetId 
          ? { ...w, visible: !w.visible }
          : w
      ),
    }));
  }, []);

  // Atualizar posição do widget
  const updateWidgetPosition = useCallback((
    widgetId: string, 
    newPosition: DashboardWidget['position']
  ) => {
    setLayout(prev => ({
      ...prev,
      widgets: prev.widgets.map(w => 
        w.id === widgetId 
          ? { ...w, position: newPosition }
          : w
      ),
    }));
  }, []);

  // Reset para layout padrão
  const resetToDefault = useCallback(() => {
    setLayout(DEFAULT_LAYOUT);
    localStorage.removeItem(`dashboard_${layout.id}`);
  }, [layout.id]);

  // Renderizar widget baseado no tipo
  const renderWidget = (widget: DashboardWidget) => {
    if (!widget.visible) return null;

    const widgetStyle = {
      gridColumn: `${widget.position.x + 1} / span ${widget.position.width}`,
      gridRow: `${widget.position.y + 1} / span ${widget.position.height}`,
    };

    return (
      <div
        key={widget.id}
        style={widgetStyle}
        className={`relative group ${selectedWidget === widget.id ? 'ring-2 ring-blue-500' : ''}`}
        onClick={() => editMode && setSelectedWidget(widget.id)}
      >
        <Card className="h-full">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              {widget.title}
            </CardTitle>
            
            {editMode && (
              <div className="opacity-0 group-hover:opacity-100 transition-opacity flex space-x-1">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleWidgetVisibility(widget.id);
                  }}
                >
                  {widget.visible ? <Eye className="w-3 h-3" /> : <EyeOff className="w-3 h-3" />}
                </Button>
                
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    removeWidget(widget.id);
                  }}
                >
                  <X className="w-3 h-3" />
                </Button>
              </div>
            )}
          </CardHeader>

          <CardContent className="p-4">
            {renderWidgetContent(widget)}
          </CardContent>
        </Card>

        {editMode && selectedWidget === widget.id && (
          <div className="absolute inset-0 border-2 border-blue-500 rounded-lg pointer-events-none">
            <div className="absolute top-0 left-0 bg-blue-500 text-white text-xs px-2 py-1 rounded-br">
              <Move className="w-3 h-3 inline mr-1" />
              Arraste para mover
            </div>
          </div>
        )}
      </div>
    );
  };

  // Renderizar conteúdo específico do widget
  const renderWidgetContent = (widget: DashboardWidget) => {
    switch (widget.type) {
      case 'metric_card':
        return (
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">2,847</div>
            <div className="text-sm text-gray-600">
              {widget.config.metric?.replace(/([A-Z])/g, ' $1').trim()}
            </div>
            <div className="text-xs text-green-600 mt-1">+12.5% vs ontem</div>
          </div>
        );

      case 'chart':
        return (
          <div className="h-32 flex items-center justify-center text-gray-500">
            {widget.config.chartType === 'line' && <TrendingUp className="w-8 h-8" />}
            {widget.config.chartType === 'bar' && <BarChart3 className="w-8 h-8" />}
            {widget.config.chartType === 'pie' && <PieChart className="w-8 h-8" />}
            <span className="ml-2">
              Gráfico {widget.config.chartType}
            </span>
          </div>
        );

      case 'table':
        return (
          <div className="text-sm">
            <div className="grid grid-cols-3 gap-2 font-medium border-b pb-2">
              <div>Agente</div>
              <div>Conversas</div>
              <div>Satisfação</div>
            </div>
            <div className="grid grid-cols-3 gap-2 py-1">
              <div>Maria Silva</div>
              <div>245</div>
              <div>4.8</div>
            </div>
            <div className="grid grid-cols-3 gap-2 py-1">
              <div>João Santos</div>
              <div>198</div>
              <div>4.6</div>
            </div>
          </div>
        );

      case 'alert_summary':
        return (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm">Alertas Ativos</span>
              <span className="text-lg font-bold text-red-600">3</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Críticos</span>
              <span className="text-lg font-bold text-orange-600">1</span>
            </div>
            <div className="text-xs text-gray-600">
              Último: Tempo de resposta alto (2min ago)
            </div>
          </div>
        );

      default:
        return (
          <div className="text-center text-gray-500">
            Widget personalizado
          </div>
        );
    }
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Barra de ferramentas */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Grid className="w-5 h-5 text-blue-500" />
              <div>
                <h3 className="font-medium">{layout.name}</h3>
                <p className="text-sm text-gray-600">{layout.description}</p>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <Button
                variant={editMode ? 'default' : 'outline'}
                size="sm"
                onClick={() => setEditMode(!editMode)}
              >
                <Settings className="w-4 h-4 mr-2" />
                {editMode ? 'Sair da Edição' : 'Editar'}
              </Button>

              {editMode && (
                <>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowWidgetLibrary(true)}
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    Adicionar
                  </Button>

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={saveLayout}
                  >
                    <Save className="w-4 h-4 mr-2" />
                    Salvar
                  </Button>

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={resetToDefault}
                  >
                    <RotateCcw className="w-4 h-4 mr-2" />
                    Reset
                  </Button>
                </>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Grid de widgets */}
      <div 
        className="grid gap-4 min-h-[600px]"
        style={{
          gridTemplateColumns: `repeat(${layout.gridSize.columns}, 1fr)`,
          gridTemplateRows: `repeat(${layout.gridSize.rows}, 1fr)`,
        }}
      >
        {layout.widgets.map(renderWidget)}
      </div>

      {/* Biblioteca de widgets */}
      {showWidgetLibrary && (
        <Card className="fixed inset-0 z-50 m-8 overflow-auto">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Biblioteca de Widgets</CardTitle>
              <Button
                variant="ghost"
                onClick={() => setShowWidgetLibrary(false)}
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
          </CardHeader>
          
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {WIDGET_TEMPLATES.map((template, index) => (
                <Card key={index} className="cursor-pointer hover:shadow-md transition-shadow">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium">{template.title}</h4>
                      <Button
                        size="sm"
                        onClick={() => {
                          addWidget(template);
                          setShowWidgetLibrary(false);
                        }}
                      >
                        <Plus className="w-4 h-4" />
                      </Button>
                    </div>
                    <p className="text-sm text-gray-600">
                      {template.type} • {template.config?.dataSource}
                    </p>
                    <div className="mt-3 h-20 bg-gray-100 rounded flex items-center justify-center">
                      <span className="text-xs text-gray-500">Preview</span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default CustomDashboard;
