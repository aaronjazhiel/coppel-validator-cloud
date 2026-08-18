# Quick Discovery — Proyecto de Ejemplo POC

## Datos Generales
- **Proyecto**: Sistema de Gestión de Inventarios Cloud
- **Solicitante**: Dirección de Operaciones
- **Unidad de Negocio**: Retail
- **Arquitecto Asignado**: Equipo Arquitectura Cloud
- **Ambiente**: Producción
- **Fecha**: Julio 2026

## Objetivo
Migrar el sistema de gestión de inventarios on-premise a AWS, garantizando alta disponibilidad (99.9% SLA), escalabilidad automática y reducción de costos operativos en un 40%.

## Requisitos Técnicos
- **Usuarios concurrentes**: 5,000 en horario pico
- **Transacciones por segundo**: 2,000 TPS
- **Latencia máxima**: 200ms P95
- **Almacenamiento**: 500GB datos actuales, crecimiento 20% anual
- **Retención de datos**: 5 años para auditoría
- **RPO**: 1 hora
- **RTO**: 4 horas

## Infraestructura Actual (On-Premise)
- 4 servidores de aplicación (8 vCPU, 32GB RAM cada uno)
- 2 servidores de base de datos Oracle (16 vCPU, 64GB RAM)
- 1 servidor de archivos (2TB NFS)
- Balanceador F5
- Red: VLAN dedicada 10.0.0.0/24

## Componentes de Aplicación
- **Frontend**: Angular 15, servido por Nginx
- **Backend**: Java 17 (Spring Boot), 12 microservicios
- **Base de datos**: Oracle 19c (migrar a PostgreSQL)
- **Cache**: Redis 6.x
- **Mensajería**: RabbitMQ (migrar a SQS/SNS)
- **Storage**: NFS para documentos PDF

## Integraciones
- SAP (API REST, sincronización cada 15 min)
- Sistema de facturación (eventos en tiempo real)
- Portal de proveedores (API pública)
- Active Directory (autenticación LDAP)

## Seguridad
- Cifrado en tránsito y reposo
- WAF para APIs públicas
- Segmentación de red (VPC)
- Cumplimiento PCI-DSS para datos de pago
- Logs de auditoría centralizados

## Disaster Recovery
- Multi-AZ para base de datos
- Backups automáticos diarios
- Réplica cross-region para DR (us-west-2)
- Failover automático < 5 minutos

## Dependencias
- VPN site-to-site con datacenter Monterrey
- DNS interno (Route 53 private hosted zone)
- Certificados SSL (ACM)
- Monitoreo con CloudWatch + Grafana

## Restricciones
- Ventana de migración: fines de semana
- No downtime en horario laboral (8am-10pm)
- Presupuesto máximo: $15,000 USD/mes en AWS
- Equipo de 3 personas para operación
