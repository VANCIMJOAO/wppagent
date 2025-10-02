"use client";

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { CalendarIcon, Clock, User, Phone, AlertCircle } from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';
import api from '@/lib/api-service';
import type { Appointment, AppointmentCreateRequest, AppointmentUpdateRequest, AppointmentStatus } from '@/types/api';

interface AppointmentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  appointment?: Appointment; // Se presente, é edição
  clients?: Array<{ id: number; nome: string; telefone: string }>;
  services?: Array<{ id: number; name: string; duration_minutes: number; price: number }>;
}

interface FormData {
  user_id: number;
  business_id: number;
  service_id: number;
  data_agendamento: string;
  hora_agendamento: string;
  duracao_minutos: number;
  valor: number;
  observacoes: string;
  status: AppointmentStatus;
}

const initialFormData: FormData = {
  user_id: 0,
  business_id: 3, // Business ID válido (primeiro ID disponível)
  service_id: 0,
  data_agendamento: '',
  hora_agendamento: '',
  duracao_minutos: 60,
  valor: 0,
  observacoes: '',
  status: 'agendado'
};

const statusOptions: { value: AppointmentStatus; label: string }[] = [
  { value: 'agendado', label: 'Agendado' },
  { value: 'confirmado', label: 'Confirmado' },
  { value: 'realizado', label: 'Realizado' },
  { value: 'cancelado', label: 'Cancelado' },
  { value: 'pendente', label: 'Pendente' }
];

// Horários de expediente (8h às 18h)
const timeSlots = Array.from({ length: 21 }, (_, i) => {
  const hour = 8 + Math.floor(i / 2);
  const minute = (i % 2) * 30;
  return `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
});

export default function AppointmentModal({
  isOpen,
  onClose,
  onSuccess,
  appointment,
  clients = [],
  services = []
}: AppointmentModalProps) {
  const [formData, setFormData] = useState<FormData>(initialFormData);
  const [selectedDate, setSelectedDate] = useState<Date>();
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const isEdit = !!appointment;

  // Carregar dados do agendamento para edição
  useEffect(() => {
    if (appointment && isOpen) {
      const appointmentDate = new Date(appointment.dateTime || appointment.data_agendamento || '');
      setFormData({
        user_id: appointment.user_id,
        business_id: appointment.business_id,
        service_id: appointment.service_id || 0,
        data_agendamento: appointmentDate.toISOString().split('T')[0],
        hora_agendamento: appointmentDate.toTimeString().slice(0, 5),
        duracao_minutos: appointment.durationMinutes || appointment.duracao_minutos || 60,
        valor: appointment.price || appointment.valor || 0,
        observacoes: appointment.notes || appointment.observacoes || '',
        status: appointment.status
      });
      setSelectedDate(appointmentDate);
    } else if (isOpen && !appointment) {
      // Reset para novo agendamento
      setFormData(initialFormData);
      setSelectedDate(undefined);
    }
  }, [appointment, isOpen]);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    // Validações obrigatórias
    if (!formData.user_id) {
      newErrors.user_id = 'Cliente é obrigatório';
    }
    if (!formData.service_id) {
      newErrors.service_id = 'Serviço é obrigatório';
    }
    if (!formData.data_agendamento) {
      newErrors.data_agendamento = 'Data é obrigatória';
    }
    if (!formData.hora_agendamento) {
      newErrors.hora_agendamento = 'Horário é obrigatório';
    }

    // Validação de data (não pode ser passado)
    if (formData.data_agendamento) {
      const selectedDate = new Date(formData.data_agendamento);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      
      if (selectedDate < today) {
        newErrors.data_agendamento = 'Data não pode ser no passado';
      }
    }

    // Validação de horário (dentro do expediente 8h-18h)
    if (formData.hora_agendamento) {
      const [hours, minutes] = formData.hora_agendamento.split(':').map(Number);
      const timeInMinutes = hours * 60 + minutes;
      const startTime = 8 * 60; // 8h
      const endTime = 18 * 60; // 18h
      
      if (timeInMinutes < startTime || timeInMinutes >= endTime) {
        newErrors.hora_agendamento = 'Horário deve estar entre 8h e 18h';
      }
    }

    // Validação de valor
    if (formData.valor < 0) {
      newErrors.valor = 'Valor não pode ser negativo';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      toast.error('Por favor, corrija os erros no formulário');
      return;
    }

    setIsLoading(true);

    try {
      // Combinar data e hora
      const dateTime = new Date(`${formData.data_agendamento}T${formData.hora_agendamento}:00`);
      
      console.log('📅 Data selecionada:', formData.data_agendamento);
      console.log('⏰ Hora selecionada:', formData.hora_agendamento);
      console.log('🕐 DateTime combinado:', dateTime);
      console.log('📤 FormData completo:', formData);
      
      const appointmentData: AppointmentCreateRequest | AppointmentUpdateRequest = {
        user_id: formData.user_id,
        business_id: formData.business_id,
        service_id: formData.service_id,
        data_agendamento: dateTime.toISOString(), // API espera data_agendamento
        duracao_minutos: formData.duracao_minutos,
        valor: formData.valor,
        observacoes: formData.observacoes,
        ...(isEdit && { status: formData.status })
      };

      console.log('📤 AppointmentData sendo enviado:', appointmentData);

      let response;
      if (isEdit && appointment) {
        // Atualizar agendamento
        response = await fetch(`/api/appointments/${appointment.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          body: JSON.stringify(appointmentData)
        });
      } else {
        // Criar novo agendamento
        response = await fetch('/api/appointments', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          body: JSON.stringify(appointmentData)
        });
      }

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Erro ao salvar agendamento');
      }

      const result = await response.json();
      
      toast.success(
        isEdit 
          ? 'Agendamento atualizado com sucesso!' 
          : 'Agendamento criado com sucesso!'
      );
      
      onSuccess();
      onClose();
      
    } catch (error) {
      console.error('Erro ao salvar agendamento:', error);
      toast.error(
        error instanceof Error 
          ? error.message 
          : 'Erro ao salvar agendamento'
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (field: keyof FormData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Limpar erro do campo quando usuário começar a digitar
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const handleDateSelect = (date: Date | undefined) => {
    console.log('🗓️ Data selecionada:', date);
    if (date) {
      setSelectedDate(date);
      handleInputChange('data_agendamento', format(date, 'yyyy-MM-dd'));
      console.log('✅ Data formatada:', format(date, 'yyyy-MM-dd'));
    }
  };

  const handleClose = () => {
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {isEdit ? 'Editar Agendamento' : 'Novo Agendamento'}
          </DialogTitle>
          <DialogDescription>
            {isEdit 
              ? 'Atualize as informações do agendamento' 
              : 'Preencha os dados para criar um novo agendamento'
            }
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Cliente */}
            <div className="space-y-2">
              <Label htmlFor="user_id" className="flex items-center gap-2">
                <User className="h-4 w-4" />
                Cliente *
              </Label>
              <Select
                value={formData.user_id.toString()}
                onValueChange={(value) => handleInputChange('user_id', parseInt(value))}
              >
                <SelectTrigger className={cn(errors.user_id && "border-red-500")}>
                  <SelectValue placeholder="Selecione um cliente" />
                </SelectTrigger>
                <SelectContent>
                  {clients.map((client) => (
                    <SelectItem key={client.id} value={client.id.toString()}>
                      {client.nome} - {client.telefone}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.user_id && (
                <p className="text-sm text-red-500 flex items-center gap-1">
                  <AlertCircle className="h-3 w-3" />
                  {errors.user_id}
                </p>
              )}
            </div>

            {/* Serviço */}
            <div className="space-y-2">
              <Label htmlFor="service_id" className="flex items-center gap-2">
                <Clock className="h-4 w-4" />
                Serviço *
              </Label>
              <Select
                value={formData.service_id.toString()}
                onValueChange={(value) => {
                  const serviceId = parseInt(value);
                  const service = services.find(s => s.id === serviceId);
                  handleInputChange('service_id', serviceId);
                  if (service) {
                    handleInputChange('duracao_minutos', service.duration_minutes);
                    handleInputChange('valor', service.price);
                  }
                }}
              >
                <SelectTrigger className={cn(errors.service_id && "border-red-500")}>
                  <SelectValue placeholder="Selecione um serviço" />
                </SelectTrigger>
                <SelectContent>
                  {services.map((service) => (
                    <SelectItem key={service.id} value={service.id.toString()}>
                      {service.name} - R$ {service.price.toFixed(2)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.service_id && (
                <p className="text-sm text-red-500 flex items-center gap-1">
                  <AlertCircle className="h-3 w-3" />
                  {errors.service_id}
                </p>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Data */}
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                <CalendarIcon className="h-4 w-4" />
                Data *
              </Label>
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className={cn(
                      "w-full justify-start text-left font-normal",
                      !selectedDate && "text-muted-foreground",
                      errors.data_agendamento && "border-red-500"
                    )}
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {selectedDate ? format(selectedDate, "dd/MM/yyyy", { locale: ptBR }) : "Selecione a data"}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <Calendar
                    mode="single"
                    selected={selectedDate}
                    onSelect={handleDateSelect}
                    initialFocus
                  />
                </PopoverContent>
              </Popover>
              {errors.data_agendamento && (
                <p className="text-sm text-red-500 flex items-center gap-1">
                  <AlertCircle className="h-3 w-3" />
                  {errors.data_agendamento}
                </p>
              )}
            </div>

            {/* Horário */}
            <div className="space-y-2">
              <Label htmlFor="hora_agendamento" className="flex items-center gap-2">
                <Clock className="h-4 w-4" />
                Horário *
              </Label>
              <Select
                value={formData.hora_agendamento}
                onValueChange={(value) => handleInputChange('hora_agendamento', value)}
              >
                <SelectTrigger className={cn(errors.hora_agendamento && "border-red-500")}>
                  <SelectValue placeholder="Selecione o horário" />
                </SelectTrigger>
                <SelectContent>
                  {timeSlots.map((time) => (
                    <SelectItem key={time} value={time}>
                      {time}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.hora_agendamento && (
                <p className="text-sm text-red-500 flex items-center gap-1">
                  <AlertCircle className="h-3 w-3" />
                  {errors.hora_agendamento}
                </p>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Duração */}
            <div className="space-y-2">
              <Label htmlFor="duracao_minutos">Duração (min)</Label>
              <Input
                id="duracao_minutos"
                type="number"
                min="15"
                max="480"
                value={formData.duracao_minutos}
                onChange={(e) => handleInputChange('duracao_minutos', parseInt(e.target.value) || 0)}
              />
            </div>

            {/* Valor */}
            <div className="space-y-2">
              <Label htmlFor="valor">Valor (R$)</Label>
              <Input
                id="valor"
                type="number"
                min="0"
                step="0.01"
                value={formData.valor}
                onChange={(e) => handleInputChange('valor', parseFloat(e.target.value) || 0)}
                className={cn(errors.valor && "border-red-500")}
              />
              {errors.valor && (
                <p className="text-sm text-red-500 flex items-center gap-1">
                  <AlertCircle className="h-3 w-3" />
                  {errors.valor}
                </p>
              )}
            </div>

            {/* Status (apenas para edição) */}
            {isEdit && (
              <div className="space-y-2">
                <Label htmlFor="status">Status</Label>
                <Select
                  value={formData.status}
                  onValueChange={(value) => handleInputChange('status', value as AppointmentStatus)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {statusOptions.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>

          {/* Observações */}
          <div className="space-y-2">
            <Label htmlFor="observacoes">Observações</Label>
            <Textarea
              id="observacoes"
              placeholder="Observações adicionais sobre o agendamento..."
              value={formData.observacoes}
              onChange={(e) => handleInputChange('observacoes', e.target.value)}
              rows={3}
            />
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleClose} disabled={isLoading}>
              Cancelar
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? 'Salvando...' : (isEdit ? 'Atualizar' : 'Criar')}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
