import { useState, useCallback } from 'react'
import { ZodSchema, ZodError } from 'zod'

/**
 * 🛡️ Hook para Validação de Formulários
 * =====================================
 * 
 * Hook customizado para validação de formulários usando Zod.
 * Gerencia erros, estado de validação e fornece utilitários.
 * 
 * Autor: Desenvolvedor
 * Data: 2025-09-08
 */

export interface FormValidationReturn<T> {
  errors: Record<string, string>
  isValid: boolean
  validate: (data: unknown) => data is T
  validateField: (fieldName: keyof T, value: unknown) => boolean
  clearErrors: () => void
  clearFieldError: (fieldName: keyof T) => void
  getFieldError: (fieldName: keyof T) => string | undefined
  hasError: (fieldName: keyof T) => boolean
  getAllErrors: () => string[]
  isFieldValid: (fieldName: keyof T) => boolean
}

export function useFormValidation<T>(schema: ZodSchema<T>): FormValidationReturn<T> {
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [isValid, setIsValid] = useState(false)
  
  // ✅ Validação completa do formulário
  const validate = useCallback((data: unknown): data is T => {
    try {
      schema.parse(data)
      setErrors({})
      setIsValid(true)
      return true
    } catch (error) {
      if (error instanceof ZodError) {
        const fieldErrors: Record<string, string> = {}
        error.issues.forEach((err) => {
          if (err.path.length > 0) {
            fieldErrors[err.path[0] as string] = err.message
          }
        })
        setErrors(fieldErrors)
      }
      setIsValid(false)
      return false
    }
  }, [schema])
  
  // ✅ Validação de campo individual
  const validateField = useCallback((fieldName: keyof T, value: unknown): boolean => {
    try {
      // Cria um objeto parcial para validação do campo
      const partialData = { [fieldName]: value } as Partial<T>
      
      // Usa safeParse para validação não-destrutiva
      const result = schema.safeParse(partialData)
      
      if (result.success) {
        // Remove erro do campo se validação passou
        setErrors(prev => {
          const newErrors = { ...prev }
          delete newErrors[fieldName as string]
          return newErrors
        })
        return true
      } else {
        // Procura erro específico para este campo
        const fieldError = result.error.issues.find(
          (issue) => issue.path.includes(fieldName as string | number)
        )
        
        if (fieldError) {
          setErrors(prev => ({
            ...prev,
            [fieldName as string]: fieldError.message
          }))
        }
        return false
      }
    } catch (error) {
      return false
    }
  }, [schema])
  
  // ✅ Limpar todos os erros
  const clearErrors = useCallback(() => {
    setErrors({})
    setIsValid(false)
  }, [])
  
  // ✅ Limpar erro de campo específico
  const clearFieldError = useCallback((fieldName: keyof T) => {
    setErrors(prev => {
      const newErrors = { ...prev }
      delete newErrors[fieldName as string]
      return newErrors
    })
  }, [])
  
  // ✅ Obter erro de campo específico
  const getFieldError = useCallback((fieldName: keyof T) => {
    return errors[fieldName as string]
  }, [errors])
  
  // ✅ Verificar se campo tem erro
  const hasError = useCallback((fieldName: keyof T): boolean => {
    return Boolean(errors[fieldName as string])
  }, [errors])
  
  // ✅ Obter todos os erros como array
  const getAllErrors = useCallback((): string[] => {
    return Object.values(errors).filter(Boolean)
  }, [errors])
  
  // ✅ Verificar se campo é válido
  const isFieldValid = useCallback((fieldName: keyof T): boolean => {
    return !hasError(fieldName)
  }, [hasError])
  
  return {
    errors,
    isValid,
    validate,
    validateField,
    clearErrors,
    clearFieldError,
    getFieldError,
    hasError,
    getAllErrors,
    isFieldValid
  }
}

// ✅ Hook especializado para validação em tempo real
export function useRealTimeValidation<T>(
  schema: ZodSchema<T>,
  data: Partial<T>,
  debounceMs: number = 300
) {
  const validation = useFormValidation(schema)
  const [isValidating, setIsValidating] = useState(false)
  
  // Validação com debounce
  const debouncedValidate = useCallback(
    debounce((dataToValidate: Partial<T>) => {
      setIsValidating(true)
      validation.validate(dataToValidate)
      setIsValidating(false)
    }, debounceMs),
    [validation, debounceMs]
  )
  
  // Dispara validação quando dados mudam
  useState(() => {
    if (Object.keys(data).length > 0) {
      debouncedValidate(data)
    }
  })
  
  return {
    ...validation,
    isValidating
  }
}

// ✅ Utilitário de debounce
function debounce<T extends (...args: any[]) => any>(
  func: T,
  waitFor: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeout)
    timeout = setTimeout(() => func(...args), waitFor)
  }
}

// ✅ Hook para validação de formulário multi-step
export function useMultiStepValidation<T extends Record<string, any>>(
  schemas: { [K in keyof T]: ZodSchema<T[K]> }
) {
  const [currentStep, setCurrentStep] = useState<keyof T>(Object.keys(schemas)[0] as keyof T)
  const [stepData, setStepData] = useState<Partial<T>>({} as Partial<T>)
  const [stepErrors, setStepErrors] = useState<{ [K in keyof T]?: Record<string, string> }>({})
  
  // Validação do step atual
  const validateCurrentStep = useCallback(() => {
    const schema = schemas[currentStep]
    const data = stepData[currentStep]
    
    try {
      schema.parse(data)
      setStepErrors(prev => ({ ...prev, [currentStep]: {} }))
      return true
    } catch (error) {
      if (error instanceof ZodError) {
        const fieldErrors: Record<string, string> = {}
        error.issues.forEach((err) => {
          if (err.path.length > 0) {
            fieldErrors[err.path[0] as string] = err.message
          }
        })
        setStepErrors(prev => ({ ...prev, [currentStep]: fieldErrors }))
      }
      return false
    }
  }, [schemas, currentStep, stepData])
  
  // Avançar para próximo step
  const nextStep = useCallback(() => {
    if (validateCurrentStep()) {
      const steps = Object.keys(schemas) as (keyof T)[]
      const currentIndex = steps.indexOf(currentStep)
      if (currentIndex < steps.length - 1) {
        setCurrentStep(steps[currentIndex + 1])
      }
    }
  }, [validateCurrentStep, schemas, currentStep])
  
  // Voltar para step anterior
  const previousStep = useCallback(() => {
    const steps = Object.keys(schemas) as (keyof T)[]
    const currentIndex = steps.indexOf(currentStep)
    if (currentIndex > 0) {
      setCurrentStep(steps[currentIndex - 1])
    }
  }, [schemas, currentStep])
  
  // Atualizar dados do step
  const updateStepData = useCallback((data: Partial<T[keyof T]>) => {
    setStepData(prev => ({
      ...prev,
      [currentStep]: { ...prev[currentStep], ...data }
    }))
  }, [currentStep])
  
  // Validação final de todos os steps
  const validateAllSteps = useCallback(() => {
    let allValid = true
    const allErrors: { [K in keyof T]?: Record<string, string> } = {}
    
    Object.keys(schemas).forEach(step => {
      const schema = schemas[step as keyof T]
      const data = stepData[step as keyof T]
      
      try {
        schema.parse(data)
        allErrors[step as keyof T] = {}
      } catch (error) {
        allValid = false
        if (error instanceof ZodError) {
          const fieldErrors: Record<string, string> = {}
          error.issues.forEach((err) => {
            if (err.path.length > 0) {
              fieldErrors[err.path[0] as string] = err.message
            }
          })
          allErrors[step as keyof T] = fieldErrors
        }
      }
    })
    
    setStepErrors(allErrors)
    return allValid
  }, [schemas, stepData])
  
  return {
    currentStep,
    stepData,
    stepErrors,
    setCurrentStep,
    updateStepData,
    validateCurrentStep,
    validateAllSteps,
    nextStep,
    previousStep,
    isFirstStep: currentStep === Object.keys(schemas)[0],
    isLastStep: currentStep === Object.keys(schemas)[Object.keys(schemas).length - 1],
    currentStepErrors: stepErrors[currentStep] || {},
    hasCurrentStepErrors: Object.keys(stepErrors[currentStep] || {}).length > 0
  }
}
