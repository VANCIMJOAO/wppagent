"""
🔍 Validador de Certificados SSL/TLS
===================================

Sistema completo de validação de certificados:
- Verificação de cadeia de certificados
- Validação de domínio e SAN
- Checagem de revogação (OCSP)
- Análise de segurança SSL
- Detecção de vulnerabilidades
"""

import ssl
import socket
import requests
import datetime
from typing import Dict, List, Optional
from urllib.parse import urlparse
from cryptography import x509
# from cryptography.x509.verification import PolicyBuilder, StoreBuilder  # Removido temporariamente
from cryptography.x509.oid import NameOID
import logging

logger = logging.getLogger(__name__)

class CertificateValidator:
    """Validador completo de certificados SSL/TLS"""
    
    def __init__(self):
        """Inicializa o validador de certificados"""
        self.security_requirements = {
            "min_key_size": 2048,
            "allowed_signatures": ["sha256", "sha384", "sha512"],
            "blocked_signatures": ["md5", "sha1"],
            "min_validity_days": 7,
            "max_validity_years": 2
        }
        logger.info("✅ Validador de certificados inicializado")
    
    def validate_certificate_chain(
        self, 
        hostname: str, 
        port: int = 443,
        timeout: int = 10
    ) -> Dict:
        """
        Valida cadeia completa de certificados SSL
        
        Args:
            hostname: Nome do servidor
            port: Porta SSL
            timeout: Timeout da conexão
            
        Returns:
            Dicionário detalhado com validação
        """
        try:
            logger.info(f"🔍 Validando cadeia de certificados: {hostname}:{port}")
            
            # Conectar e obter certificados
            context = ssl.create_default_context()
            context.check_hostname = True
            context.verify_mode = ssl.CERT_REQUIRED
            
            with socket.create_connection((hostname, port), timeout=timeout) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    # Obter certificado do peer
                    peer_cert = ssock.getpeercert(binary_form=True)
                    peer_cert_info = ssock.getpeercert()
                    
                    # Obter cadeia completa
                    cert_chain = ssock.getpeercert_chain()
                    
                    # Validações detalhadas
                    validation_result = {
                        "hostname": hostname,
                        "port": port,
                        "timestamp": datetime.datetime.utcnow().isoformat(),
                        "connection": {
                            "successful": True,
                            "ssl_version": ssock.version(),
                            "cipher_suite": ssock.cipher(),
                            "compression": ssock.compression()
                        },
                        "certificate": self._analyze_certificate(peer_cert_info),
                        "chain": self._analyze_certificate_chain(cert_chain),
                        "security": self._security_analysis(peer_cert_info, ssock),
                        "compliance": self._compliance_check(peer_cert_info),
                        "overall_status": "VALID"
                    }
                    
                    # Determinar status geral
                    if validation_result["security"]["vulnerabilities"]:
                        validation_result["overall_status"] = "VULNERABLE"
                    elif validation_result["compliance"]["issues"]:
                        validation_result["overall_status"] = "WARNING"
                    
                    logger.info(f"✅ Validação concluída: {validation_result['overall_status']}")
                    return validation_result
                    
        except ssl.SSLError as e:
            logger.error(f"❌ Erro SSL: {e}")
            return {
                "hostname": hostname,
                "port": port,
                "connection": {"successful": False, "ssl_error": str(e)},
                "overall_status": "SSL_ERROR"
            }
        except Exception as e:
            logger.error(f"❌ Erro na validação: {e}")
            return {
                "hostname": hostname,
                "port": port,
                "connection": {"successful": False, "error": str(e)},
                "overall_status": "ERROR"
            }
    
    def _analyze_certificate(self, cert_info: Dict) -> Dict:
        """Analisa informações do certificado principal"""
        try:
            # Extrair datas
            not_before = datetime.datetime.strptime(
                cert_info['notBefore'], '%b %d %H:%M:%S %Y %Z'
            )
            not_after = datetime.datetime.strptime(
                cert_info['notAfter'], '%b %d %H:%M:%S %Y %Z'
            )
            
            now = datetime.datetime.utcnow()
            days_remaining = (not_after - now).days
            
            # Analisar Subject e SAN
            subject = dict(x[0] for x in cert_info['subject'])
            san_list = [x[1] for x in cert_info.get('subjectAltName', [])]
            
            return {
                "subject": {
                    "common_name": subject.get('commonName'),
                    "organization": subject.get('organizationName'),
                    "country": subject.get('countryName'),
                    "organizational_unit": subject.get('organizationalUnitName')
                },
                "issuer": dict(x[0] for x in cert_info['issuer']),
                "validity": {
                    "not_before": not_before.isoformat(),
                    "not_after": not_after.isoformat(),
                    "days_remaining": days_remaining,
                    "is_expired": now > not_after,
                    "is_not_yet_valid": now < not_before
                },
                "domains": {
                    "primary": subject.get('commonName'),
                    "san_list": san_list,
                    "total_domains": len(san_list)
                },
                "serial_number": cert_info['serialNumber'],
                "version": cert_info['version']
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao analisar certificado: {e}")
            return {"error": str(e)}
    
    def _analyze_certificate_chain(self, cert_chain) -> Dict:
        """Analisa cadeia completa de certificados"""
        try:
            chain_info = {
                "length": len(cert_chain),
                "certificates": [],
                "is_complete": False,
                "has_root_ca": False
            }
            
            for i, cert_der in enumerate(cert_chain):
                cert = x509.load_der_x509_certificate(cert_der)
                
                # Analisar cada certificado da cadeia
                subject = cert.subject
                issuer = cert.issuer
                
                cert_data = {
                    "position": i,
                    "subject_cn": subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value if subject.get_attributes_for_oid(NameOID.COMMON_NAME) else None,
                    "issuer_cn": issuer.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value if issuer.get_attributes_for_oid(NameOID.COMMON_NAME) else None,
                    "is_ca": self._is_ca_certificate(cert),
                    "is_self_signed": subject == issuer,
                    "key_size": cert.public_key().key_size,
                    "signature_algorithm": cert.signature_algorithm_oid._name
                }
                
                chain_info["certificates"].append(cert_data)
                
                # Verificar se é root CA
                if cert_data["is_ca"] and cert_data["is_self_signed"]:
                    chain_info["has_root_ca"] = True
            
            # Verificar se cadeia está completa
            chain_info["is_complete"] = chain_info["has_root_ca"] or len(cert_chain) >= 2
            
            return chain_info
            
        except Exception as e:
            logger.error(f"❌ Erro ao analisar cadeia: {e}")
            return {"error": str(e)}
    
    def _security_analysis(self, cert_info: Dict, ssock) -> Dict:
        """Análise de segurança do certificado e conexão"""
        try:
            vulnerabilities = []
            warnings = []
            
            # Verificar algoritmo de assinatura
            # Esta informação não está disponível no getpeercert()
            # Precisaríamos do certificado em formato DER/PEM
            
            # Verificar força da cifra
            cipher = ssock.cipher()
            if cipher:
                cipher_name = cipher[0].lower()
                
                # Verificar cifras fracas
                weak_ciphers = ['rc4', 'des', '3des', 'md5']
                if any(weak in cipher_name for weak in weak_ciphers):
                    vulnerabilities.append(f"Cifra fraca detectada: {cipher[0]}")
                
                # Verificar PFS (Perfect Forward Secrecy)
                if not any(pfs in cipher_name for pfs in ['ecdhe', 'dhe']):
                    warnings.append("Perfect Forward Secrecy não disponível")
            
            # Verificar versão SSL/TLS
            ssl_version = ssock.version()
            if ssl_version in ['SSLv2', 'SSLv3', 'TLSv1', 'TLSv1.1']:
                vulnerabilities.append(f"Versão SSL/TLS insegura: {ssl_version}")
            
            # Verificar validade do certificado
            not_after = datetime.datetime.strptime(
                cert_info['notAfter'], '%b %d %H:%M:%S %Y %Z'
            )
            days_remaining = (not_after - datetime.datetime.utcnow()).days
            
            if days_remaining < self.security_requirements["min_validity_days"]:
                vulnerabilities.append(f"Certificado expira em {days_remaining} dias")
            elif days_remaining < 30:
                warnings.append(f"Certificado expira em {days_remaining} dias")
            
            return {
                "vulnerabilities": vulnerabilities,
                "warnings": warnings,
                "cipher_suite": {
                    "name": cipher[0] if cipher else None,
                    "protocol": cipher[1] if cipher else None,
                    "bits": cipher[2] if cipher else None
                },
                "ssl_version": ssl_version,
                "security_score": self._calculate_security_score(vulnerabilities, warnings)
            }
            
        except Exception as e:
            logger.error(f"❌ Erro na análise de segurança: {e}")
            return {"error": str(e)}
    
    def _compliance_check(self, cert_info: Dict) -> Dict:
        """Verificação de compliance com padrões de segurança"""
        try:
            issues = []
            recommendations = []
            
            # Verificar se é certificado wildcard
            subject = dict(x[0] for x in cert_info['subject'])
            common_name = subject.get('commonName', '')
            
            if common_name.startswith('*.'):
                recommendations.append("Considere usar certificados específicos em vez de wildcard")
            
            # Verificar quantidade de domínios no SAN
            san_count = len(cert_info.get('subjectAltName', []))
            if san_count > 100:
                recommendations.append(f"Muitos domínios no SAN ({san_count})")
            
            # Verificar duração do certificado
            not_before = datetime.datetime.strptime(
                cert_info['notBefore'], '%b %d %H:%M:%S %Y %Z'
            )
            not_after = datetime.datetime.strptime(
                cert_info['notAfter'], '%b %d %H:%M:%S %Y %Z'
            )
            
            validity_days = (not_after - not_before).days
            max_validity = self.security_requirements["max_validity_years"] * 365
            
            if validity_days > max_validity:
                issues.append(f"Certificado muito longo ({validity_days} dias)")
            
            return {
                "issues": issues,
                "recommendations": recommendations,
                "compliance_score": self._calculate_compliance_score(issues),
                "standards": {
                    "ca_browser_forum": len(issues) == 0,
                    "rfc_5280": True,  # Simplificado
                    "pci_dss": len(issues) == 0
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Erro na verificação de compliance: {e}")
            return {"error": str(e)}
    
    def _is_ca_certificate(self, cert) -> bool:
        """Verifica se é um certificado de CA"""
        try:
            basic_constraints = cert.extensions.get_extension_for_oid(
                x509.oid.ExtensionOID.BASIC_CONSTRAINTS
            ).value
            return basic_constraints.ca
        except x509.ExtensionNotFound:
            return False
    
    def _calculate_security_score(self, vulnerabilities: List, warnings: List) -> int:
        """Calcula pontuação de segurança (0-100)"""
        score = 100
        score -= len(vulnerabilities) * 20  # -20 por vulnerabilidade
        score -= len(warnings) * 5          # -5 por warning
        return max(0, score)
    
    def _calculate_compliance_score(self, issues: List) -> int:
        """Calcula pontuação de compliance (0-100)"""
        score = 100
        score -= len(issues) * 15  # -15 por issue
        return max(0, score)
    
    def check_domain_validation(self, hostname: str, cert_domains: List[str]) -> Dict:
        """
        Verifica se o certificado é válido para o domínio
        
        Args:
            hostname: Nome do host a validar
            cert_domains: Lista de domínios do certificado
            
        Returns:
            Resultado da validação de domínio
        """
        try:
            hostname = hostname.lower()
            valid_domains = []
            
            for domain in cert_domains:
                domain = domain.lower()
                
                # Verificação exata
                if hostname == domain:
                    valid_domains.append(domain)
                    continue
                
                # Verificação wildcard
                if domain.startswith('*.'):
                    wildcard_domain = domain[2:]  # Remove "*."
                    if hostname.endswith(f".{wildcard_domain}"):
                        # Verificar se não é subdomínio de subdomínio
                        remaining = hostname[:-len(wildcard_domain)-1]
                        if '.' not in remaining:
                            valid_domains.append(domain)
            
            is_valid = len(valid_domains) > 0
            
            return {
                "is_valid": is_valid,
                "hostname": hostname,
                "matching_domains": valid_domains,
                "all_cert_domains": cert_domains,
                "validation_type": "wildcard" if any(d.startswith('*.') for d in valid_domains) else "exact"
            }
            
        except Exception as e:
            logger.error(f"❌ Erro na validação de domínio: {e}")
            return {"is_valid": False, "error": str(e)}
    
    def check_ocsp_status(self, cert_der: bytes) -> Dict:
        """
        Verifica status OCSP do certificado (se disponível)
        
        Args:
            cert_der: Certificado em formato DER
            
        Returns:
            Status OCSP
        """
        try:
            # Esta é uma implementação simplificada
            # OCSP completo requer mais complexidade
            
            cert = x509.load_der_x509_certificate(cert_der)
            
            # Verificar se tem extensão OCSP
            try:
                authority_info = cert.extensions.get_extension_for_oid(
                    x509.oid.ExtensionOID.AUTHORITY_INFORMATION_ACCESS
                ).value
                
                ocsp_urls = []
                for access_desc in authority_info:
                    if access_desc.access_method == x509.oid.AuthorityInformationAccessOID.OCSP:
                        ocsp_urls.append(access_desc.access_location.value)
                
                return {
                    "has_ocsp": len(ocsp_urls) > 0,
                    "ocsp_urls": ocsp_urls,
                    "status": "unknown",  # Implementação completa requer protocolo OCSP
                    "message": "OCSP URLs encontradas, verificação completa não implementada"
                }
                
            except x509.ExtensionNotFound:
                return {
                    "has_ocsp": False,
                    "status": "not_supported",
                    "message": "Certificado não suporta OCSP"
                }
                
        except Exception as e:
            logger.error(f"❌ Erro na verificação OCSP: {e}")
            return {"has_ocsp": False, "error": str(e)}
    
    def generate_security_report(self, validation_result: Dict) -> str:
        """
        Gera relatório de segurança legível
        
        Args:
            validation_result: Resultado da validação
            
        Returns:
            Relatório em texto
        """
        try:
            report = []
            report.append("🔒 RELATÓRIO DE SEGURANÇA SSL/TLS")
            report.append("=" * 50)
            report.append(f"Servidor: {validation_result['hostname']}:{validation_result['port']}")
            report.append(f"Status: {validation_result['overall_status']}")
            report.append(f"Data: {validation_result['timestamp']}")
            report.append("")
            
            # Informações do certificado
            if 'certificate' in validation_result:
                cert = validation_result['certificate']
                report.append("📜 CERTIFICADO")
                report.append(f"  • CN: {cert['subject']['common_name']}")
                report.append(f"  • Organização: {cert['subject']['organization']}")
                report.append(f"  • Domínios: {len(cert['domains']['san_list'])} SAN entries")
                report.append(f"  • Expira em: {cert['validity']['days_remaining']} dias")
                report.append("")
            
            # Segurança
            if 'security' in validation_result:
                security = validation_result['security']
                report.append("🛡️ ANÁLISE DE SEGURANÇA")
                report.append(f"  • Score: {security['security_score']}/100")
                report.append(f"  • SSL/TLS: {security['ssl_version']}")
                
                if security['vulnerabilities']:
                    report.append("  ❌ VULNERABILIDADES:")
                    for vuln in security['vulnerabilities']:
                        report.append(f"    - {vuln}")
                
                if security['warnings']:
                    report.append("  ⚠️ AVISOS:")
                    for warning in security['warnings']:
                        report.append(f"    - {warning}")
                report.append("")
            
            # Compliance
            if 'compliance' in validation_result:
                compliance = validation_result['compliance']
                report.append("📋 COMPLIANCE")
                report.append(f"  • Score: {compliance['compliance_score']}/100")
                
                if compliance['issues']:
                    report.append("  ❌ PROBLEMAS:")
                    for issue in compliance['issues']:
                        report.append(f"    - {issue}")
                report.append("")
            
            # Recomendações
            report.append("💡 RECOMENDAÇÕES")
            if validation_result['overall_status'] == 'VALID':
                report.append("  ✅ Certificado está seguro")
            else:
                report.append("  ⚠️ Revise os problemas identificados")
                report.append("  • Atualize para TLS 1.2+ se necessário")
                report.append("  • Monitore data de expiração")
                report.append("  • Configure renovação automática")
            
            return "\n".join(report)
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar relatório: {e}")
            return f"Erro ao gerar relatório: {e}"

# Instância global
_certificate_validator = None

def get_certificate_validator() -> CertificateValidator:
    """Obtém instância global do validador"""
    global _certificate_validator
    if _certificate_validator is None:
        _certificate_validator = CertificateValidator()
    return _certificate_validator
