"""
Agent cryptographic identity verification service.

This module implements certificate-based agent authentication with
cryptographic signature verification, certificate management, and
agent impersonation detection.
"""

import asyncio
import base64
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

import boto3
from botocore.exceptions import ClientError
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key
import structlog

from src.models.security import AgentCertificate, SecurityEventType, SecuritySeverity
from src.utils.config import ConfigManager
from src.utils.exceptions import SecurityError, AuthenticationError


logger = structlog.get_logger(__name__)


class AgentAuthenticator:
    """
    Agent cryptographic identity verification service.
    
    Features:
    - Certificate-based agent identity verification
    - Agent certificate management and revocation list handling
    - Cryptographic signature verification for all agent communications
    - Agent impersonation detection and prevention mechanisms
    - Secure agent key rotation and certificate lifecycle management
    """
    
    def __init__(self, config: ConfigManager, audit_logger=None):
        self.config = config
        self.audit_logger = audit_logger
        
        # AWS services
        self.dynamodb = boto3.resource('dynamodb', region_name=config.aws.region)
        self.secrets_manager = boto3.client('secretsmanager', region_name=config.aws.region)
        
        # Certificate storage
        self.cert_table_name = config.get('agent_certificates_table', 'incident-commander-agent-certificates')
        self.ca_secret_name = config.get('ca_secret_name', 'incident-commander-ca-key')
        
        # Certificate configuration
        self.default_cert_lifetime_days = config.get('cert_lifetime_days', 90)
        self.cert_renewal_threshold_days = config.get('cert_renewal_threshold_days', 30)
        
        # In-memory certificate cache for performance
        self._cert_cache: Dict[str, AgentCertificate] = {}
        self._cache_ttl = timedelta(minutes=15)
        self._cache_timestamps: Dict[str, datetime] = {}
        
        # Revocation list cache
        self._revocation_list: set = set()
        self._revocation_list_updated: Optional[datetime] = None
    
    async def generate_agent_certificate(
        self,
        agent_id: str,
        lifetime_days: Optional[int] = None
    ) -> AgentCertificate:
        """
        Generate a new certificate for an agent.
        
        Args:
            agent_id: Unique agent identifier
            lifetime_days: Certificate lifetime in days (default: 90)
            
        Returns:
            AgentCertificate: Generated certificate
        """
        try:
            lifetime_days = lifetime_days or self.default_cert_lifetime_days
            
            # Generate RSA key pair
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            public_key = private_key.public_key()
            
            # Serialize public key
            public_key_pem = public_key.serialize(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode('utf-8')
            
            # Create certificate
            certificate = AgentCertificate(
                agent_id=agent_id,
                certificate_id=str(uuid4()),
                public_key=public_key_pem,
                expires_at=datetime.utcnow() + timedelta(days=lifetime_days)
            )
            
            # Store certificate
            await self._store_certificate(certificate)
            
            # Store private key securely
            private_key_pem = private_key.serialize(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode('utf-8')
            
            await self._store_private_key(agent_id, certificate.certificate_id, private_key_pem)
            
            # Update cache
            self._cert_cache[agent_id] = certificate
            self._cache_timestamps[agent_id] = datetime.utcnow()
            
            # Log certificate generation
            if self.audit_logger:
                await self.audit_logger.log_security_event(
                    event_type=SecurityEventType.AGENT_AUTHENTICATION,
                    severity=SecuritySeverity.MEDIUM,
                    action="generate_certificate",
                    outcome="success",
                    agent_id=agent_id,
                    details={
                        "certificate_id": certificate.certificate_id,
                        "expires_at": certificate.expires_at.isoformat(),
                        "lifetime_days": lifetime_days
                    }
                )
            
            await logger.ainfo(
                "Agent certificate generated",
                agent_id=agent_id,
                certificate_id=certificate.certificate_id,
                expires_at=certificate.expires_at
            )
            
            return certificate
            
        except Exception as e:
            await logger.aerror(
                "Failed to generate agent certificate",
                agent_id=agent_id,
                error=str(e)
            )
            raise SecurityError(f"Certificate generation failed: {e}")
    
    async def verify_agent_signature(
        self,
        agent_id: str,
        message: str,
        signature: str
    ) -> bool:
        """
        Verify cryptographic signature from an agent.
        
        Args:
            agent_id: Agent identifier
            message: Original message that was signed
            signature: Base64-encoded signature
            
        Returns:
            bool: True if signature is valid
        """
        try:
            # Get agent certificate
            certificate = await self.get_agent_certificate(agent_id)
            if not certificate or not certificate.is_valid():
                await logger.awarning(
                    "Invalid or missing certificate for signature verification",
                    agent_id=agent_id
                )
                return False
            
            # Load public key
            public_key = load_pem_public_key(certificate.public_key.encode('utf-8'))
            
            # Decode signature
            signature_bytes = base64.b64decode(signature)
            
            # Verify signature
            try:
                public_key.verify(
                    signature_bytes,
                    message.encode('utf-8'),
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    hashes.SHA256()
                )
                
                # Log successful verification
                if self.audit_logger:
                    await self.audit_logger.log_security_event(
                        event_type=SecurityEventType.AGENT_AUTHENTICATION,
                        severity=SecuritySeverity.LOW,
                        action="verify_signature",
                        outcome="success",
                        agent_id=agent_id,
                        details={
                            "certificate_id": certificate.certificate_id,
                            "message_length": len(message)
                        }
                    )
                
                return True
                
            except Exception as verify_error:
                # Log failed verification
                if self.audit_logger:
                    await self.audit_logger.log_security_event(
                        event_type=SecurityEventType.SECURITY_VIOLATION,
                        severity=SecuritySeverity.HIGH,
                        action="verify_signature",
                        outcome="failure",
                        agent_id=agent_id,
                        details={
                            "error": str(verify_error),
                            "certificate_id": certificate.certificate_id
                        }
                    )
                
                await logger.awarning(
                    "Signature verification failed",
                    agent_id=agent_id,
                    error=str(verify_error)
                )
                return False
                
        except Exception as e:
            await logger.aerror(
                "Error during signature verification",
                agent_id=agent_id,
                error=str(e)
            )
            return False
    
    async def sign_message(self, agent_id: str, message: str) -> str:
        """
        Sign a message with agent's private key.
        
        Args:
            agent_id: Agent identifier
            message: Message to sign
            
        Returns:
            str: Base64-encoded signature
        """
        try:
            # Get agent's private key
            private_key_pem = await self._get_private_key(agent_id)
            if not private_key_pem:
                raise AuthenticationError(f"No private key found for agent {agent_id}")
            
            # Load private key
            private_key = load_pem_private_key(
                private_key_pem.encode('utf-8'),
                password=None
            )
            
            # Sign message
            signature = private_key.sign(
                message.encode('utf-8'),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            return base64.b64encode(signature).decode('utf-8')
            
        except Exception as e:
            await logger.aerror(
                "Failed to sign message",
                agent_id=agent_id,
                error=str(e)
            )
            raise SecurityError(f"Message signing failed: {e}")
    
    async def get_agent_certificate(self, agent_id: str) -> Optional[AgentCertificate]:
        """
        Get agent certificate with caching.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            AgentCertificate: Agent certificate or None if not found
        """
        try:
            # Check cache first
            if agent_id in self._cert_cache:
                cache_time = self._cache_timestamps.get(agent_id)
                if cache_time and datetime.utcnow() - cache_time < self._cache_ttl:
                    return self._cert_cache[agent_id]
            
            # Load from database
            certificate = await self._load_certificate(agent_id)
            
            if certificate:
                # Update cache
                self._cert_cache[agent_id] = certificate
                self._cache_timestamps[agent_id] = datetime.utcnow()
            
            return certificate
            
        except Exception as e:
            await logger.aerror(
                "Failed to get agent certificate",
                agent_id=agent_id,
                error=str(e)
            )
            return None
    
    async def revoke_certificate(
        self,
        agent_id: str,
        reason: str = "unspecified"
    ) -> bool:
        """
        Revoke an agent certificate.
        
        Args:
            agent_id: Agent identifier
            reason: Revocation reason
            
        Returns:
            bool: True if revocation successful
        """
        try:
            certificate = await self.get_agent_certificate(agent_id)
            if not certificate:
                return False
            
            # Update certificate status
            certificate.status = "revoked"
            certificate.revoked_at = datetime.utcnow()
            certificate.revocation_reason = reason
            
            # Store updated certificate
            await self._store_certificate(certificate)
            
            # Update revocation list
            self._revocation_list.add(certificate.certificate_id)
            
            # Clear from cache
            if agent_id in self._cert_cache:
                del self._cert_cache[agent_id]
                del self._cache_timestamps[agent_id]
            
            # Log revocation
            if self.audit_logger:
                await self.audit_logger.log_security_event(
                    event_type=SecurityEventType.AGENT_AUTHENTICATION,
                    severity=SecuritySeverity.HIGH,
                    action="revoke_certificate",
                    outcome="success",
                    agent_id=agent_id,
                    details={
                        "certificate_id": certificate.certificate_id,
                        "reason": reason
                    }
                )
            
            await logger.ainfo(
                "Agent certificate revoked",
                agent_id=agent_id,
                certificate_id=certificate.certificate_id,
                reason=reason
            )
            
            return True
            
        except Exception as e:
            await logger.aerror(
                "Failed to revoke certificate",
                agent_id=agent_id,
                error=str(e)
            )
            return False
    
    async def rotate_agent_certificate(self, agent_id: str) -> Optional[AgentCertificate]:
        """
        Rotate an agent's certificate (generate new, revoke old).
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            AgentCertificate: New certificate or None if failed
        """
        try:
            # Get current certificate
            old_certificate = await self.get_agent_certificate(agent_id)
            
            # Generate new certificate
            new_certificate = await self.generate_agent_certificate(agent_id)
            
            # Revoke old certificate if it exists
            if old_certificate:
                await self.revoke_certificate(agent_id, "certificate_rotation")
            
            await logger.ainfo(
                "Agent certificate rotated",
                agent_id=agent_id,
                old_cert_id=old_certificate.certificate_id if old_certificate else None,
                new_cert_id=new_certificate.certificate_id
            )
            
            return new_certificate
            
        except Exception as e:
            await logger.aerror(
                "Failed to rotate certificate",
                agent_id=agent_id,
                error=str(e)
            )
            return None
    
    async def check_certificates_for_renewal(self) -> List[str]:
        """
        Check for certificates that need renewal.
        
        Returns:
            List[str]: List of agent IDs with certificates needing renewal
        """
        try:
            renewal_threshold = datetime.utcnow() + timedelta(days=self.cert_renewal_threshold_days)
            
            # Get all active certificates
            certificates = await self._get_all_certificates()
            
            agents_needing_renewal = []
            for cert in certificates:
                if (cert.status == "active" and 
                    cert.expires_at <= renewal_threshold and
                    not cert.is_expired()):
                    agents_needing_renewal.append(cert.agent_id)
            
            if agents_needing_renewal:
                await logger.ainfo(
                    "Certificates need renewal",
                    agents=agents_needing_renewal,
                    threshold_days=self.cert_renewal_threshold_days
                )
            
            return agents_needing_renewal
            
        except Exception as e:
            await logger.aerror(
                "Failed to check certificates for renewal",
                error=str(e)
            )
            return []
    
    async def detect_agent_impersonation(
        self,
        agent_id: str,
        message: str,
        signature: str,
        source_ip: Optional[str] = None
    ) -> bool:
        """
        Detect potential agent impersonation attempts.
        
        Args:
            agent_id: Claimed agent identifier
            message: Message content
            signature: Signature to verify
            source_ip: Source IP address
            
        Returns:
            bool: True if impersonation detected
        """
        try:
            # Verify signature first
            signature_valid = await self.verify_agent_signature(agent_id, message, signature)
            
            if not signature_valid:
                # Log potential impersonation
                if self.audit_logger:
                    await self.audit_logger.log_security_event(
                        event_type=SecurityEventType.SUSPICIOUS_BEHAVIOR,
                        severity=SecuritySeverity.CRITICAL,
                        action="detect_impersonation",
                        outcome="impersonation_detected",
                        agent_id=agent_id,
                        source_ip=source_ip,
                        details={
                            "reason": "invalid_signature",
                            "message_length": len(message)
                        }
                    )
                
                await logger.acritical(
                    "Potential agent impersonation detected",
                    agent_id=agent_id,
                    source_ip=source_ip,
                    reason="invalid_signature"
                )
                
                return True
            
            # Additional behavioral checks could be added here
            # - Unusual timing patterns
            # - Unexpected source IPs
            # - Message content analysis
            
            return False
            
        except Exception as e:
            await logger.aerror(
                "Error during impersonation detection",
                agent_id=agent_id,
                error=str(e)
            )
            return False
    
    # Private helper methods
    
    async def _store_certificate(self, certificate: AgentCertificate) -> None:
        """Store certificate in DynamoDB."""
        table = self.dynamodb.Table(self.cert_table_name)
        
        item = {
            'agent_id': certificate.agent_id,
            'certificate_id': certificate.certificate_id,
            'public_key': certificate.public_key,
            'issued_at': certificate.issued_at.isoformat(),
            'expires_at': certificate.expires_at.isoformat(),
            'issuer': certificate.issuer,
            'status': certificate.status,
            'revoked_at': certificate.revoked_at.isoformat() if certificate.revoked_at else None,
            'revocation_reason': certificate.revocation_reason
        }
        
        # Remove None values
        item = {k: v for k, v in item.items() if v is not None}
        
        await asyncio.to_thread(table.put_item, Item=item)
    
    async def _load_certificate(self, agent_id: str) -> Optional[AgentCertificate]:
        """Load certificate from DynamoDB."""
        table = self.dynamodb.Table(self.cert_table_name)
        
        try:
            response = await asyncio.to_thread(
                table.get_item,
                Key={'agent_id': agent_id}
            )
            
            if 'Item' not in response:
                return None
            
            item = response['Item']
            
            # Convert datetime strings back to datetime objects
            item['issued_at'] = datetime.fromisoformat(item['issued_at'])
            item['expires_at'] = datetime.fromisoformat(item['expires_at'])
            if item.get('revoked_at'):
                item['revoked_at'] = datetime.fromisoformat(item['revoked_at'])
            
            return AgentCertificate(**item)
            
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceNotFoundException':
                raise
            return None
    
    async def _get_all_certificates(self) -> List[AgentCertificate]:
        """Get all certificates from DynamoDB."""
        table = self.dynamodb.Table(self.cert_table_name)
        
        response = await asyncio.to_thread(table.scan)
        certificates = []
        
        for item in response.get('Items', []):
            # Convert datetime strings
            item['issued_at'] = datetime.fromisoformat(item['issued_at'])
            item['expires_at'] = datetime.fromisoformat(item['expires_at'])
            if item.get('revoked_at'):
                item['revoked_at'] = datetime.fromisoformat(item['revoked_at'])
            
            certificates.append(AgentCertificate(**item))
        
        return certificates
    
    async def _store_private_key(
        self,
        agent_id: str,
        certificate_id: str,
        private_key_pem: str
    ) -> None:
        """Store private key in AWS Secrets Manager."""
        secret_name = f"incident-commander-agent-{agent_id}-{certificate_id}"
        
        await asyncio.to_thread(
            self.secrets_manager.create_secret,
            Name=secret_name,
            SecretString=private_key_pem,
            Description=f"Private key for agent {agent_id} certificate {certificate_id}"
        )
    
    async def _get_private_key(self, agent_id: str) -> Optional[str]:
        """Get private key from AWS Secrets Manager."""
        # Get current certificate to find the right secret
        certificate = await self.get_agent_certificate(agent_id)
        if not certificate:
            return None
        
        secret_name = f"incident-commander-agent-{agent_id}-{certificate.certificate_id}"
        
        try:
            response = await asyncio.to_thread(
                self.secrets_manager.get_secret_value,
                SecretId=secret_name
            )
            return response['SecretString']
            
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceNotFoundException':
                await logger.aerror(
                    "Failed to retrieve private key",
                    agent_id=agent_id,
                    error=str(e)
                )
            return None