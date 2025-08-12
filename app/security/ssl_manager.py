"""
🔐 Gerenciador de Certificados SSL/TLS
=====================================

Sistema completo para gerenciamento de certificados SSL:
- Geração de certificados auto-assinados
- Integração com Let's Encrypt  
- Validação de certificados
- Renovação automática
- Configuração HTTPS obrigatória
"""

import os
import ssl
import socket
import subprocess
import datetime
from pathlib import Path
from typing import Optional, Dict, Tuple
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import logging

logger = logging.getLogger(__name__)

class SSLManager:
    """Gerenciador completo de certificados SSL/TLS"""
    
    def __init__(self, ssl_dir: str = None):
        """
        Inicializa o gerenciador SSL
        
        Args:
            ssl_dir: Diretório para armazenar certificados
        """
        self.ssl_dir = Path(ssl_dir or "/home/vancim/whats_agent/config/nginx/ssl")
        self.ssl_dir.mkdir(parents=True, exist_ok=True)
        
        # Arquivos padrão
        self.cert_file = self.ssl_dir / "server.crt"
        self.key_file = self.ssl_dir / "server.key"
        self.ca_file = self.ssl_dir / "ca.crt"
        self.dhparam_file = self.ssl_dir / "dhparam.pem"
        
        logger.info(f"✅ SSL Manager inicializado: {self.ssl_dir}")
    
    def generate_self_signed_certificate(
        self,
        domains: list = None,
        country: str = "BR",
        state: str = "SP", 
        city: str = "São Paulo",
        organization: str = "WhatsApp Agent",
        days: int = 365
    ) -> Tuple[str, str]:
        """
        Gera certificado auto-assinado para desenvolvimento
        
        Args:
            domains: Lista de domínios (padrão: localhost, whatsapp-agent.local)
            country: Código do país
            state: Estado
            city: Cidade
            organization: Organização
            days: Validade em dias
            
        Returns:
            Tuple (caminho_certificado, caminho_chave)
        """
        try:
            domains = domains or ["localhost", "whatsapp-agent.local", "127.0.0.1"]
            
            logger.info(f"🔑 Gerando certificado auto-assinado para: {', '.join(domains)}")
            
            # Gerar chave privada RSA 2048 bits
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            
            # Criar nome do sujeito
            subject = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, country),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, state),
                x509.NameAttribute(NameOID.LOCALITY_NAME, city),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization),
                x509.NameAttribute(NameOID.COMMON_NAME, domains[0])
            ])
            
            # Configurar certificado
            builder = x509.CertificateBuilder()
            builder = builder.subject_name(subject)
            builder = builder.issuer_name(subject)  # Auto-assinado
            builder = builder.public_key(private_key.public_key())
            builder = builder.serial_number(x509.random_serial_number())
            builder = builder.not_valid_before(datetime.datetime.utcnow())
            builder = builder.not_valid_after(
                datetime.datetime.utcnow() + datetime.timedelta(days=days)
            )
            
            # Adicionar extensões de SAN (Subject Alternative Names)
            san_list = []
            for domain in domains:
                if domain.replace('.', '').replace(':', '').isdigit() or ':' in domain:
                    # É um IP
                    import ipaddress
                    try:
                        ip_addr = ipaddress.ip_address(domain.split(':')[0])
                        san_list.append(x509.IPAddress(ip_addr))
                    except ValueError:
                        # Se não conseguir converter, trata como DNS
                        san_list.append(x509.DNSName(domain))
                else:
                    # É um DNS
                    san_list.append(x509.DNSName(domain))
            
            builder = builder.add_extension(
                x509.SubjectAlternativeName(san_list),
                critical=False
            )
            
            # Extensões básicas
            builder = builder.add_extension(
                x509.BasicConstraints(ca=False, path_length=None),
                critical=True
            )
            
            builder = builder.add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    key_encipherment=True,
                    content_commitment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    key_cert_sign=False,
                    crl_sign=False,
                    encipher_only=False,
                    decipher_only=False
                ),
                critical=True
            )
            
            builder = builder.add_extension(
                x509.ExtendedKeyUsage([
                    x509.oid.ExtendedKeyUsageOID.SERVER_AUTH,
                    x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH
                ]),
                critical=True
            )
            
            # Assinar certificado
            certificate = builder.sign(private_key, hashes.SHA256())
            
            # Salvar chave privada com permissões seguras
            with open(self.key_file, "wb") as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            # Definir permissões seguras na chave
            os.chmod(self.key_file, 0o600)
            
            # Salvar certificado
            with open(self.cert_file, "wb") as f:
                f.write(certificate.public_bytes(serialization.Encoding.PEM))
            
            os.chmod(self.cert_file, 0o644)
            
            logger.info("✅ Certificado auto-assinado gerado com sucesso")
            logger.info(f"📜 Certificado: {self.cert_file}")
            logger.info(f"🔑 Chave privada: {self.key_file}")
            
            return str(self.cert_file), str(self.key_file)
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar certificado: {e}")
            raise
    
    def setup_letsencrypt(
        self,
        domain: str,
        email: str,
        webroot_path: str = "/var/www/html",
        staging: bool = False
    ) -> bool:
        """
        Configura certificado Let's Encrypt
        
        Args:
            domain: Domínio para o certificado
            email: Email para registro
            webroot_path: Caminho webroot para validação
            staging: Usar ambiente de staging (teste)
            
        Returns:
            True se bem-sucedido
        """
        try:
            logger.info(f"🔐 Configurando Let's Encrypt para: {domain}")
            
            # Verificar se certbot está instalado
            try:
                subprocess.run(["certbot", "--version"], 
                             check=True, capture_output=True)
            except subprocess.CalledProcessError:
                logger.error("❌ Certbot não está instalado")
                return False
            
            # Preparar comando certbot
            cmd = [
                "certbot", "certonly",
                "--webroot",
                "-w", webroot_path,
                "-d", domain,
                "--email", email,
                "--agree-tos",
                "--no-eff-email",
                "--non-interactive"
            ]
            
            if staging:
                cmd.append("--staging")
            
            # Executar certbot
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Copiar certificados para diretório SSL
                letsencrypt_dir = f"/etc/letsencrypt/live/{domain}"
                
                if os.path.exists(f"{letsencrypt_dir}/fullchain.pem"):
                    subprocess.run([
                        "cp", f"{letsencrypt_dir}/fullchain.pem", 
                        str(self.cert_file)
                    ])
                    subprocess.run([
                        "cp", f"{letsencrypt_dir}/privkey.pem", 
                        str(self.key_file)
                    ])
                    
                    # Definir permissões
                    os.chmod(self.key_file, 0o600)
                    os.chmod(self.cert_file, 0o644)
                    
                    logger.info("✅ Certificado Let's Encrypt configurado")
                    return True
                
            logger.error(f"❌ Erro no certbot: {result.stderr}")
            return False
            
        except Exception as e:
            logger.error(f"❌ Erro ao configurar Let's Encrypt: {e}")
            return False
    
    def validate_certificate(self, cert_path: str = None) -> Dict:
        """
        Valida certificado SSL
        
        Args:
            cert_path: Caminho do certificado (padrão: self.cert_file)
            
        Returns:
            Dicionário com informações do certificado
        """
        try:
            cert_path = cert_path or str(self.cert_file)
            
            with open(cert_path, "rb") as f:
                cert_data = f.read()
            
            certificate = x509.load_pem_x509_certificate(cert_data)
            
            # Extrair informações
            subject = certificate.subject
            issuer = certificate.issuer
            
            # Obter SAN (Subject Alternative Names)
            san_list = []
            try:
                san_ext = certificate.extensions.get_extension_for_oid(
                    x509.oid.ExtensionOID.SUBJECT_ALTERNATIVE_NAME
                ).value
                for name in san_ext:
                    san_list.append(str(name))
            except x509.ExtensionNotFound:
                pass
            
            result = {
                "valid": True,
                "subject": {
                    "common_name": subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value,
                    "organization": subject.get_attributes_for_oid(NameOID.ORGANIZATION_NAME)[0].value if subject.get_attributes_for_oid(NameOID.ORGANIZATION_NAME) else None,
                    "country": subject.get_attributes_for_oid(NameOID.COUNTRY_NAME)[0].value if subject.get_attributes_for_oid(NameOID.COUNTRY_NAME) else None
                },
                "issuer": {
                    "common_name": issuer.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value,
                    "organization": issuer.get_attributes_for_oid(NameOID.ORGANIZATION_NAME)[0].value if issuer.get_attributes_for_oid(NameOID.ORGANIZATION_NAME) else None
                },
                "validity": {
                    "not_before": certificate.not_valid_before.isoformat(),
                    "not_after": certificate.not_valid_after.isoformat(),
                    "days_remaining": (certificate.not_valid_after - datetime.datetime.utcnow()).days
                },
                "san_list": san_list,
                "self_signed": certificate.issuer == certificate.subject,
                "key_size": certificate.public_key().key_size,
                "signature_algorithm": certificate.signature_algorithm_oid._name
            }
            
            logger.info("✅ Certificado validado com sucesso")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro na validação do certificado: {e}")
            return {"valid": False, "error": str(e)}
    
    def check_certificate_expiry(self, days_ahead: int = 30) -> Dict:
        """
        Verifica se o certificado está próximo do vencimento
        
        Args:
            days_ahead: Dias de antecedência para alerta
            
        Returns:
            Dicionário com status de vencimento
        """
        try:
            cert_info = self.validate_certificate()
            
            if not cert_info.get("valid"):
                return {"needs_renewal": True, "reason": "Certificado inválido"}
            
            days_remaining = cert_info["validity"]["days_remaining"]
            
            result = {
                "needs_renewal": days_remaining <= days_ahead,
                "days_remaining": days_remaining,
                "expires_at": cert_info["validity"]["not_after"],
                "warning_threshold": days_ahead
            }
            
            if result["needs_renewal"]:
                logger.warning(f"⚠️ Certificado expira em {days_remaining} dias")
            else:
                logger.info(f"✅ Certificado válido por mais {days_remaining} dias")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro ao verificar vencimento: {e}")
            return {"needs_renewal": True, "reason": f"Erro: {e}"}
    
    def generate_dhparam(self, bits: int = 2048) -> str:
        """
        Gera parâmetros Diffie-Hellman para Perfect Forward Secrecy
        
        Args:
            bits: Tamanho da chave (2048 ou 4096)
            
        Returns:
            Caminho do arquivo gerado
        """
        try:
            logger.info(f"🔑 Gerando parâmetros DH de {bits} bits...")
            
            # Gerar dhparam
            result = subprocess.run([
                "openssl", "dhparam", "-out", str(self.dhparam_file), str(bits)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                os.chmod(self.dhparam_file, 0o644)
                logger.info("✅ Parâmetros DH gerados com sucesso")
                return str(self.dhparam_file)
            else:
                logger.error(f"❌ Erro ao gerar DH: {result.stderr}")
                raise Exception(f"Erro dhparam: {result.stderr}")
                
        except Exception as e:
            logger.error(f"❌ Erro ao gerar DH params: {e}")
            raise
    
    def test_ssl_connection(self, hostname: str, port: int = 443) -> Dict:
        """
        Testa conexão SSL com um servidor
        
        Args:
            hostname: Nome do servidor
            port: Porta SSL
            
        Returns:
            Dicionário com resultado do teste
        """
        try:
            logger.info(f"🔍 Testando conexão SSL: {hostname}:{port}")
            
            # Criar contexto SSL
            context = ssl.create_default_context()
            
            # Conectar
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    
                    result = {
                        "connected": True,
                        "version": ssock.version(),
                        "cipher": ssock.cipher(),
                        "certificate": {
                            "subject": dict(x[0] for x in cert['subject']),
                            "issuer": dict(x[0] for x in cert['issuer']),
                            "version": cert['version'],
                            "serial_number": cert['serialNumber'],
                            "not_before": cert['notBefore'],
                            "not_after": cert['notAfter'],
                            "san": cert.get('subjectAltName', [])
                        }
                    }
                    
                    logger.info("✅ Conexão SSL bem-sucedida")
                    return result
                    
        except Exception as e:
            logger.error(f"❌ Erro na conexão SSL: {e}")
            return {"connected": False, "error": str(e)}
    
    def setup_auto_renewal(self, domain: str) -> bool:
        """
        Configura renovação automática do certificado
        
        Args:
            domain: Domínio do certificado
            
        Returns:
            True se configurado com sucesso
        """
        try:
            logger.info("⚙️ Configurando renovação automática...")
            
            # Script de renovação
            renewal_script = f"""#!/bin/bash
# Renovação automática de certificado SSL
certbot renew --quiet --post-hook "nginx -s reload"

# Verificar se renovação foi bem-sucedida
if [ $? -eq 0 ]; then
    # Copiar certificados atualizados
    cp /etc/letsencrypt/live/{domain}/fullchain.pem {self.cert_file}
    cp /etc/letsencrypt/live/{domain}/privkey.pem {self.key_file}
    
    # Ajustar permissões
    chmod 644 {self.cert_file}
    chmod 600 {self.key_file}
    
    echo "✅ Certificado renovado: $(date)"
else
    echo "❌ Erro na renovação: $(date)"
fi
"""
            
            script_path = self.ssl_dir / "renew_certificate.sh"
            with open(script_path, "w") as f:
                f.write(renewal_script)
            
            os.chmod(script_path, 0o755)
            
            # Adicionar ao crontab
            cron_job = f"0 2 * * * {script_path}"
            
            # Verificar se já existe
            result = subprocess.run(["crontab", "-l"], 
                                  capture_output=True, text=True)
            existing_cron = result.stdout if result.returncode == 0 else ""
            
            if str(script_path) not in existing_cron:
                new_cron = existing_cron + f"\n{cron_job}\n"
                
                process = subprocess.Popen(["crontab", "-"], 
                                         stdin=subprocess.PIPE, text=True)
                process.communicate(new_cron)
                
                if process.returncode == 0:
                    logger.info("✅ Renovação automática configurada")
                    return True
            else:
                logger.info("✅ Renovação automática já configurada")
                return True
                
        except Exception as e:
            logger.error(f"❌ Erro ao configurar renovação: {e}")
            return False

# Instância global
_ssl_manager = None

def get_ssl_manager() -> SSLManager:
    """Obtém instância global do SSL Manager"""
    global _ssl_manager
    if _ssl_manager is None:
        _ssl_manager = SSLManager()
    return _ssl_manager
