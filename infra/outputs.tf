# ── Outputs ───────────────────────────────────────────────────
output "api_url" {
  description = "URL base del API Gateway"
  value       = "${aws_api_gateway_stage.prod.invoke_url}"
}

output "iniciativas_bucket" {
  value = aws_s3_bucket.iniciativas.id
}

output "portal_url" {
  value = aws_s3_bucket_website_configuration.portal.website_endpoint
}

output "rds_endpoint" {
  description = "Host del RDS MySQL"
  value       = aws_db_instance.main.address
}

output "rds_secret_arn" {
  description = "ARN del secret con credenciales RDS"
  value       = aws_secretsmanager_secret.rds.arn
}

