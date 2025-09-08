/**
 * 📝 Exemplo de Uso - Formulário de Agendamento com Validação
 * ==========================================================
 * 
 * Demonstra como usar os schemas Zod e hook de validação
 * em um formulário real de agendamento.
 * 
 * Autor: Desenvolvedor
 * Data: 2025-09-08
 */

'use client'

import { useState } from 'react'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

// Importar schemas e hooks de validação
import { appointmentSchema, AppointmentFormData } from "@/lib/validations"
import { useFormValidation } from "@/hooks/useFormValidation"
import { useApiState } from "@/hooks/useApiState"

// Dados mockados para serviços
const mockServices = [
  { id: 1, nome: 'Consulta Médica', duracao: 60, valor: 150 },
  { id: 2, nome: 'Exame Preventivo', duracao: 30, valor: 80 },
  { id: 3, nome: 'Retorno', duracao: 30, valor: 100 }
]

export function AppointmentForm() {
  // ✅ Estado do formulário
  const [formData, setFormData] = useState<Partial<AppointmentFormData>>({
    cliente_nome: '',
    cliente_telefone: '',
    cliente_email: '',
    data_agendamento: '',
    horario: '',
    servico_id: undefined,
    observacoes: ''
  })

  // ✅ Hook de validação
  const {
    errors,
    isValid,
    validate,
    validateField,
    getFieldError,
    hasError,
    clearFieldError
  } = useFormValidation(appointmentSchema)

  // ✅ Hook de estado da API
  const {
    loading,
    error: submitError,
    setLoading,
    setData,
    setError
  } = useApiState()

  // ✅ Atualizar campo e validar
  const updateField = (fieldName: keyof AppointmentFormData, value: any) => {
    const newFormData = { ...formData, [fieldName]: value }
    setFormData(newFormData)
    
    // Validação em tempo real para o campo específico
    validateField(fieldName, value)
  }

  // ✅ Submit do formulário
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // Validação completa antes do submit
    if (!validate(formData)) {
      return
    }

    setLoading(true)
    
    try {
      // Simulação de API call
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      // Simular erro ocasional
      if (Math.random() < 0.3) {
        throw new Error('Erro ao salvar agendamento')
      }
      
      setData(formData)
      
      // Reset do formulário
      setFormData({
        cliente_nome: '',
        cliente_telefone: '',
        cliente_email: '',
        data_agendamento: '',
        horario: '',
        servico_id: undefined,
        observacoes: ''
      })
      
      alert('Agendamento criado com sucesso!')
      
    } catch (error) {
      setError(error as Error)
    }
  }

  // ✅ Componente de campo com erro
  const FormField = ({ 
    name, 
    label, 
    type = 'text', 
    children 
  }: { 
    name: keyof AppointmentFormData
    label: string
    type?: string
    children?: React.ReactNode
  }) => (
    <div className="space-y-2">
      <Label htmlFor={name as string} className="text-sm font-medium">
        {label}
      </Label>
      {children || (
        <Input
          id={name as string}
          type={type}
          value={formData[name] || ''}
          onChange={(e) => updateField(name, e.target.value)}
          onFocus={() => clearFieldError(name)}
          className={hasError(name) ? 'border-red-500' : ''}
        />
      )}
      {hasError(name) && (
        <p className="text-sm text-red-600">
          {getFieldError(name)}
        </p>
      )}
    </div>
  )

  return (
    <Card className="max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle>Novo Agendamento</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          
          {/* ✅ Dados do Cliente */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Dados do Cliente</h3>
            
            <FormField name="cliente_nome" label="Nome Completo" />
            
            <FormField name="cliente_telefone" label="Telefone">
              <Input
                id="cliente_telefone"
                type="tel"
                placeholder="(11) 99999-9999"
                value={formData.cliente_telefone || ''}
                onChange={(e) => updateField('cliente_telefone', e.target.value)}
                onFocus={() => clearFieldError('cliente_telefone')}
                className={hasError('cliente_telefone') ? 'border-red-500' : ''}
              />
            </FormField>
            
            <FormField name="cliente_email" label="Email (opcional)" type="email" />
          </div>

          {/* ✅ Dados do Agendamento */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Agendamento</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FormField name="data_agendamento" label="Data" type="date" />
              
              <FormField name="horario" label="Horário">
                <Input
                  id="horario"
                  type="time"
                  value={formData.horario || ''}
                  onChange={(e) => updateField('horario', e.target.value)}
                  onFocus={() => clearFieldError('horario')}
                  className={hasError('horario') ? 'border-red-500' : ''}
                />
              </FormField>
            </div>
            
            <FormField name="servico_id" label="Serviço">
              <Select
                value={formData.servico_id?.toString() || ''}
                onValueChange={(value) => updateField('servico_id', parseInt(value))}
              >
                <SelectTrigger className={hasError('servico_id') ? 'border-red-500' : ''}>
                  <SelectValue placeholder="Selecione um serviço" />
                </SelectTrigger>
                <SelectContent>
                  {mockServices.map((service) => (
                    <SelectItem key={service.id} value={service.id.toString()}>
                      {service.nome} - {service.duracao}min - R$ {service.valor}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </FormField>
            
            <FormField name="observacoes" label="Observações (opcional)">
              <Textarea
                id="observacoes"
                placeholder="Informações adicionais sobre o agendamento..."
                value={formData.observacoes || ''}
                onChange={(e) => updateField('observacoes', e.target.value)}
                onFocus={() => clearFieldError('observacoes')}
                className={hasError('observacoes') ? 'border-red-500' : ''}
              />
            </FormField>
          </div>

          {/* ✅ Erro de submit */}
          {submitError && (
            <div className="p-4 bg-red-100 border border-red-400 text-red-700 rounded">
              <p className="font-medium">Erro ao salvar:</p>
              <p>{submitError.message}</p>
            </div>
          )}

          {/* ✅ Botões */}
          <div className="flex space-x-4">
            <Button
              type="submit"
              disabled={!isValid || loading}
              className="flex-1"
            >
              {loading ? 'Salvando...' : 'Salvar Agendamento'}
            </Button>
            
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setFormData({
                  cliente_nome: '',
                  cliente_telefone: '',
                  cliente_email: '',
                  data_agendamento: '',
                  horario: '',
                  servico_id: undefined,
                  observacoes: ''
                })
              }}
            >
              Limpar
            </Button>
          </div>

          {/* ✅ Debug info (apenas desenvolvimento) */}
          {process.env.NODE_ENV === 'development' && (
            <details className="mt-6 p-4 bg-gray-100 rounded">
              <summary className="cursor-pointer font-medium">Debug Info</summary>
              <div className="mt-2 space-y-2 text-sm">
                <div>
                  <strong>Form Valid:</strong> {isValid ? '✅' : '❌'}
                </div>
                <div>
                  <strong>Errors:</strong>
                  <pre className="mt-1 text-xs">
                    {JSON.stringify(errors, null, 2)}
                  </pre>
                </div>
                <div>
                  <strong>Form Data:</strong>
                  <pre className="mt-1 text-xs">
                    {JSON.stringify(formData, null, 2)}
                  </pre>
                </div>
              </div>
            </details>
          )}
        </form>
      </CardContent>
    </Card>
  )
}

export default AppointmentForm
