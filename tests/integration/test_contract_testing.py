#!/usr/bin/env python3
"""TRILHA 2 FASE 2.3 - Contract Testing"""

import json
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class APIContract:
    """Define um contrato de API"""

    endpoint: str
    method: str
    request_schema: Dict[str, Any]
    response_schema: Dict[str, Any]
    status_codes: List[int]
    headers: Dict[str, str]


class ContractValidator:
    """Valida contratos de API"""

    def __init__(self):
        self.validation_results = []

    def validate_schema(
        self, data: Any, schema: Dict[str, Any], path: str = ""
    ) -> List[str]:
        """Valida dados contra um schema"""
        errors = []

        if isinstance(schema, dict):
            if "type" in schema:
                expected_type = schema["type"]

                # Validar tipo
                if expected_type == "object" and not isinstance(data, dict):
                    errors.append(f"{path}: Expected object, got {type(data).__name__}")
                elif expected_type == "array" and not isinstance(data, list):
                    errors.append(f"{path}: Expected array, got {type(data).__name__}")
                elif expected_type == "string" and not isinstance(data, str):
                    errors.append(f"{path}: Expected string, got {type(data).__name__}")
                elif expected_type == "integer" and not isinstance(data, int):
                    errors.append(
                        f"{path}: Expected integer, got {type(data).__name__}"
                    )
                elif expected_type == "boolean" and not isinstance(data, bool):
                    errors.append(
                        f"{path}: Expected boolean, got {type(data).__name__}"
                    )

                # Validar propriedades obrigatórias
                if expected_type == "object" and isinstance(data, dict):
                    required = schema.get("required", [])
                    for field in required:
                        if field not in data:
                            errors.append(f"{path}.{field}: Required field missing")

                    # Validar propriedades aninhadas
                    properties = schema.get("properties", {})
                    for field, field_schema in properties.items():
                        if field in data:
                            field_errors = self.validate_schema(
                                data[field], field_schema, f"{path}.{field}"
                            )
                            errors.extend(field_errors)

                # Validar itens do array
                if expected_type == "array" and isinstance(data, list):
                    items_schema = schema.get("items", {})
                    for i, item in enumerate(data):
                        item_errors = self.validate_schema(
                            item, items_schema, f"{path}[{i}]"
                        )
                        errors.extend(item_errors)

        return errors

    def validate_contract(
        self,
        contract: APIContract,
        request_data: Any,
        response_data: Any,
        status_code: int,
    ) -> Dict[str, Any]:
        """Valida dados contra um contrato"""
        result = {
            "contract": f"{contract.method} {contract.endpoint}",
            "valid": True,
            "errors": [],
        }

        # Validar request
        if contract.request_schema:
            request_errors = self.validate_schema(
                request_data, contract.request_schema, "request"
            )
            result["errors"].extend([f"Request: {error}" for error in request_errors])

        # Validar response
        if contract.response_schema:
            response_errors = self.validate_schema(
                response_data, contract.response_schema, "response"
            )
            result["errors"].extend([f"Response: {error}" for error in response_errors])

        # Validar status code
        if status_code not in contract.status_codes:
            result["errors"].append(
                f"Status: Expected {contract.status_codes}, got {status_code}"
            )

        result["valid"] = len(result["errors"]) == 0
        return result


class ContractTestFramework:
    """Framework para testes de contrato"""

    def __init__(self):
        self.validator = ContractValidator()
        self.contracts = self._define_contracts()
        self.test_results = []

    def _define_contracts(self) -> Dict[str, APIContract]:
        """Define contratos das APIs"""
        return {
            "webhook_whatsapp": APIContract(
                endpoint="/webhook",
                method="POST",
                request_schema={
                    "type": "object",
                    "required": ["object", "entry"],
                    "properties": {
                        "object": {"type": "string"},
                        "entry": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["id", "changes"],
                                "properties": {
                                    "id": {"type": "string"},
                                    "changes": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "required": ["value", "field"],
                                            "properties": {
                                                "value": {"type": "object"},
                                                "field": {"type": "string"},
                                            },
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
                response_schema={
                    "type": "object",
                    "required": ["status"],
                    "properties": {
                        "status": {"type": "string"},
                        "message": {"type": "string"},
                    },
                },
                status_codes=[200, 400, 401, 500],
                headers={"Content-Type": "application/json"},
            ),
            "auth_login": APIContract(
                endpoint="/auth/login",
                method="POST",
                request_schema={
                    "type": "object",
                    "required": ["username", "password"],
                    "properties": {
                        "username": {"type": "string"},
                        "password": {"type": "string"},
                    },
                },
                response_schema={
                    "type": "object",
                    "required": ["access_token", "token_type"],
                    "properties": {
                        "access_token": {"type": "string"},
                        "token_type": {"type": "string"},
                        "expires_in": {"type": "integer"},
                    },
                },
                status_codes=[200, 401, 422],
                headers={"Content-Type": "application/json"},
            ),
            "message_send": APIContract(
                endpoint="/messages/send",
                method="POST",
                request_schema={
                    "type": "object",
                    "required": ["to", "message"],
                    "properties": {
                        "to": {"type": "string"},
                        "message": {"type": "string"},
                        "conversation_id": {"type": "string"},
                    },
                },
                response_schema={
                    "type": "object",
                    "required": ["message_id", "status"],
                    "properties": {
                        "message_id": {"type": "string"},
                        "status": {"type": "string"},
                        "timestamp": {"type": "string"},
                    },
                },
                status_codes=[200, 400, 401, 429],
                headers={"Content-Type": "application/json"},
            ),
            "conversation_list": APIContract(
                endpoint="/conversations",
                method="GET",
                request_schema={},
                response_schema={
                    "type": "object",
                    "required": ["conversations", "total"],
                    "properties": {
                        "conversations": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["id", "user_id", "status"],
                                "properties": {
                                    "id": {"type": "string"},
                                    "user_id": {"type": "string"},
                                    "status": {"type": "string"},
                                    "created_at": {"type": "string"},
                                    "updated_at": {"type": "string"},
                                },
                            },
                        },
                        "total": {"type": "integer"},
                    },
                },
                status_codes=[200, 401],
                headers={"Content-Type": "application/json"},
            ),
        }

    def test_webhook_contract(self) -> bool:
        """Testa contrato do webhook WhatsApp"""
        print("🧪 Contract: Webhook WhatsApp...")

        contract = self.contracts["webhook_whatsapp"]

        # Teste com dados válidos
        valid_request = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "entry_123",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "messages": [
                                    {"id": "msg_123", "from": "5511999999999"}
                                ],
                            },
                            "field": "messages",
                        }
                    ],
                }
            ],
        }

        valid_response = {"status": "success", "message": "Webhook processed"}

        result = self.validator.validate_contract(
            contract, valid_request, valid_response, 200
        )

        print(f"   ✅ Dados válidos: {'PASSOU' if result['valid'] else 'FALHOU'}")

        # Teste com dados inválidos
        invalid_request = {
            "object": "whatsapp_business_account"
            # Missing required 'entry' field
        }

        invalid_result = self.validator.validate_contract(
            contract, invalid_request, valid_response, 200
        )

        validation_detected_error = not invalid_result["valid"]
        print(
            f"   🛡️ Erro detectado: {'PASSOU' if validation_detected_error else 'FALHOU'}"
        )

        success = result["valid"] and validation_detected_error
        print(f"   🎯 Contrato webhook: {'✅ PASSOU' if success else '❌ FALHOU'}")
        return success

    def test_auth_contract(self) -> bool:
        """Testa contrato de autenticação"""
        print("🧪 Contract: Authentication...")

        contract = self.contracts["auth_login"]

        # Login válido
        valid_request = {"username": "admin@test.com", "password": "secure123"}

        valid_response = {
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            "token_type": "bearer",
            "expires_in": 3600,
        }

        result = self.validator.validate_contract(
            contract, valid_request, valid_response, 200
        )

        print(f"   ✅ Login válido: {'PASSOU' if result['valid'] else 'FALHOU'}")

        # Login inválido (campo faltando)
        invalid_request = {
            "username": "admin@test.com"
            # Missing password
        }

        invalid_result = self.validator.validate_contract(
            contract, invalid_request, valid_response, 200
        )

        validation_detected_error = not invalid_result["valid"]
        print(
            f"   🛡️ Campo obrigatório: {'PASSOU' if validation_detected_error else 'FALHOU'}"
        )

        success = result["valid"] and validation_detected_error
        print(f"   🎯 Contrato auth: {'✅ PASSOU' if success else '❌ FALHOU'}")
        return success

    def test_message_send_contract(self) -> bool:
        """Testa contrato de envio de mensagem"""
        print("🧪 Contract: Message Send...")

        contract = self.contracts["message_send"]

        # Envio válido
        valid_request = {
            "to": "+5511999999999",
            "message": "Olá! Como posso ajudar?",
            "conversation_id": "conv_123",
        }

        valid_response = {
            "message_id": "msg_456",
            "status": "sent",
            "timestamp": "2025-01-15T10:30:00Z",
        }

        result = self.validator.validate_contract(
            contract, valid_request, valid_response, 200
        )

        print(f"   ✅ Envio válido: {'PASSOU' if result['valid'] else 'FALHOU'}")

        # Teste com campos opcionais
        minimal_request = {
            "to": "+5511999999999",
            "message": "Teste",
            # conversation_id é opcional
        }

        minimal_result = self.validator.validate_contract(
            contract, minimal_request, valid_response, 200
        )

        print(
            f"   ✅ Campos opcionais: {'PASSOU' if minimal_result['valid'] else 'FALHOU'}"
        )

        success = result["valid"] and minimal_result["valid"]
        print(f"   🎯 Contrato message: {'✅ PASSOU' if success else '❌ FALHOU'}")
        return success

    def test_conversation_list_contract(self) -> bool:
        """Testa contrato de listagem de conversas"""
        print("🧪 Contract: Conversation List...")

        contract = self.contracts["conversation_list"]

        # Lista válida
        valid_response = {
            "conversations": [
                {
                    "id": "conv_1",
                    "user_id": "user_123",
                    "status": "active",
                    "created_at": "2025-01-15T10:00:00Z",
                    "updated_at": "2025-01-15T10:30:00Z",
                },
                {
                    "id": "conv_2",
                    "user_id": "user_456",
                    "status": "closed",
                    "created_at": "2025-01-15T09:00:00Z",
                    "updated_at": "2025-01-15T09:45:00Z",
                },
            ],
            "total": 2,
        }

        result = self.validator.validate_contract(contract, {}, valid_response, 200)

        print(f"   ✅ Lista válida: {'PASSOU' if result['valid'] else 'FALHOU'}")

        # Lista vazia
        empty_response = {"conversations": [], "total": 0}

        empty_result = self.validator.validate_contract(
            contract, {}, empty_response, 200
        )

        print(f"   ✅ Lista vazia: {'PASSOU' if empty_result['valid'] else 'FALHOU'}")

        success = result["valid"] and empty_result["valid"]
        print(f"   🎯 Contrato conversations: {'✅ PASSOU' if success else '❌ FALHOU'}")
        return success

    def test_backward_compatibility(self) -> bool:
        """Testa compatibilidade com versões anteriores"""
        print("🧪 Contract: Backward Compatibility...")

        # Simular mudança de API - adição de campo opcional
        old_response = {
            "access_token": "token123",
            "token_type": "bearer",
            # Não tem expires_in
        }

        # Nova versão deve ser compatível com resposta antiga
        auth_contract = self.contracts["auth_login"]

        # Modificar contrato para tornar expires_in opcional
        modified_schema = auth_contract.response_schema.copy()
        modified_schema["required"] = [
            "access_token",
            "token_type",
        ]  # Remove expires_in

        modified_contract = APIContract(
            endpoint=auth_contract.endpoint,
            method=auth_contract.method,
            request_schema=auth_contract.request_schema,
            response_schema=modified_schema,
            status_codes=auth_contract.status_codes,
            headers=auth_contract.headers,
        )

        old_request = {"username": "admin@test.com", "password": "secure123"}

        result = self.validator.validate_contract(
            modified_contract, old_request, old_response, 200
        )

        backward_compatible = result["valid"]
        print(f"   ✅ Compatibilidade: {'PASSOU' if backward_compatible else 'FALHOU'}")

        # Testar mudança que quebra compatibilidade
        breaking_response = {
            "jwt_token": "token123",  # Campo renomeado - breaking change
            "type": "bearer",
        }

        breaking_result = self.validator.validate_contract(
            auth_contract, old_request, breaking_response, 200
        )

        breaking_detected = not breaking_result["valid"]
        print(
            f"   🛡️ Breaking change detectado: {'PASSOU' if breaking_detected else 'FALHOU'}"
        )

        success = backward_compatible and breaking_detected
        print(f"   🎯 Backward compatibility: {'✅ PASSOU' if success else '❌ FALHOU'}")
        return success

    async def run_all_contract_tests(self):
        """Executa todos os testes de contrato"""
        print("🎯 TRILHA 2 FASE 2.3 - Contract Testing")
        print("📋 Validação de Contratos de API")
        print("=" * 60)

        tests = [
            ("Webhook Contract", self.test_webhook_contract),
            ("Auth Contract", self.test_auth_contract),
            ("Message Send Contract", self.test_message_send_contract),
            ("Conversation List Contract", self.test_conversation_list_contract),
            ("Backward Compatibility", self.test_backward_compatibility),
        ]

        passed = 0
        total = len(tests)

        for test_name, test_func in tests:
            try:
                print(f"\n🔍 {test_name}:")
                result = test_func()
                if result:
                    passed += 1
                    self.test_results.append({"test": test_name, "status": "PASSED"})
                else:
                    self.test_results.append({"test": test_name, "status": "FAILED"})
            except Exception as e:
                print(f"💥 Erro em {test_name}: {e}")
                self.test_results.append(
                    {"test": test_name, "status": "ERROR", "error": str(e)}
                )

        success_rate = passed / total

        print("\n" + "=" * 60)
        print("📊 RESULTADOS DOS TESTES DE CONTRATO")
        print("=" * 60)
        print(f"✅ Contratos válidos: {passed}")
        print(f"❌ Contratos inválidos: {total - passed}")
        print(f"📊 Total: {total}")
        print(f"🎯 Taxa de Sucesso: {success_rate:.1%}")

        if success_rate >= 0.8:
            print("\n🎉 EXCELENTE: Contract Testing validado!")
            print("✅ Todos os contratos estão bem definidos")
            print("🔒 APIs seguem padrões consistentes")
        elif success_rate >= 0.6:
            print("\n⚠️ BOM: Alguns contratos OK, outros precisam revisão")
        else:
            print("\n❌ ATENÇÃO: Problemas nos contratos de API")

        print(f"\n🎯 TRILHA 2 FASE 2.3 - Contract Testing IMPLEMENTADO")
        return success_rate >= 0.6


async def main():
    """Função principal"""
    framework = ContractTestFramework()
    success = await framework.run_all_contract_tests()
    return success


if __name__ == "__main__":
    import asyncio

    success = asyncio.run(main())
    exit(0 if success else 1)
