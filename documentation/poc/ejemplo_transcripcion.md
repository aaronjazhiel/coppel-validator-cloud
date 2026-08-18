# Transcripción — Sesión de Levantamiento Técnico
**Fecha**: 8 de julio 2026
**Participantes**: Arquitecto Cloud, Líder Técnico, DBA, DevOps Lead

---

**Arquitecto**: Bueno, vamos a revisar los detalles técnicos del sistema de inventarios. ¿Cuántos microservicios tienen actualmente?

**Líder Técnico**: Son 12 microservicios en Spring Boot. Los más críticos son el de consulta de stock, el de movimientos y el de conciliación con SAP. Esos tres manejan el 80% del tráfico.

**Arquitecto**: ¿Qué patrones de comunicación usan entre servicios?

**Líder Técnico**: Principalmente REST síncrono, pero para los eventos de movimiento usamos RabbitMQ. Queremos migrar a algo más managed como SQS.

**Arquitecto**: Perfecto. ¿Y la base de datos? Veo que tienen Oracle 19c.

**DBA**: Sí, tenemos una instancia principal con Data Guard para HA. La base tiene 500GB, pero con índices y tablespaces llega a 800GB en disco. Queremos migrar a PostgreSQL, ya hicimos un assessment con AWS SCT y el 95% es compatible directo.

**Arquitecto**: ¿Qué tamaño de instancia necesitarían en RDS?

**DBA**: Basado en nuestro consumo actual, un db.r5.xlarge debería funcionar. En picos de fin de mes necesitamos más, así que podríamos usar auto-scaling de read replicas.

**Arquitecto**: ¿Cómo manejan el caching actualmente?

**Líder Técnico**: Redis 6 con 3 nodos en cluster. Cacheamos catálogos, sesiones y resultados de consultas frecuentes. Unos 16GB de memoria total.

**DevOps Lead**: Para el deployment, actualmente usamos Jenkins con pipelines manuales. Queremos CI/CD completo con CodePipeline o GitHub Actions.

**Arquitecto**: ¿Contenedores o serverless?

**DevOps Lead**: Ya tenemos todo dockerizado. Queremos EKS para los microservicios principales y Lambda para los procesos batch que corren de noche.

**Arquitecto**: ¿Qué procesos batch tienen?

**Líder Técnico**: Conciliación con SAP cada 15 minutos, reportes nocturnos que generan PDFs, y un proceso de limpieza de datos temporales. El de reportes es el más pesado, tarda 2 horas.

**Arquitecto**: Para el storage de PDFs, ¿cuánto volumen manejan?

**Líder Técnico**: Unos 50GB al mes de PDFs nuevos. Se retienen 5 años por auditoría. Total actual son 2TB.

**Arquitecto**: S3 con lifecycle policies sería ideal. Intelligent-Tiering para los primeros 6 meses y Glacier después.

**DBA**: Una cosa importante: necesitamos cifrado en reposo para cumplir PCI-DSS. Los datos de pago van en columnas específicas.

**Arquitecto**: KMS con customer managed keys. ¿Algo más de seguridad?

**DevOps Lead**: WAF para las APIs públicas del portal de proveedores. Y necesitamos VPN site-to-site con el datacenter de Monterrey porque SAP sigue on-premise.

**Arquitecto**: ¿Monitoreo?

**DevOps Lead**: CloudWatch para métricas y logs, pero queremos dashboards en Grafana. Ya tenemos Grafana Cloud, solo necesitamos el datasource de CloudWatch.

**Arquitecto**: Perfecto. ¿Ventana de migración?

**Líder Técnico**: Solo fines de semana. El sistema no puede tener downtime en horario laboral de 8am a 10pm. La migración de datos la haríamos con DMS en modo CDC para minimizar el corte.
