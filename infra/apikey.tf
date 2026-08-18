# ── API Key + Usage Plan ──────────────────────────────────────
# Protege los endpoints con x-api-key header

resource "aws_api_gateway_api_key" "main" {
  name    = "${local.prefix}-api-key"
  enabled = true
}

resource "aws_api_gateway_usage_plan" "main" {
  name = "${local.prefix}-usage-plan"

  api_stages {
    api_id = aws_api_gateway_rest_api.api.id
    stage  = aws_api_gateway_stage.prod.stage_name
  }

  throttle_settings {
    burst_limit = 50
    rate_limit  = 100
  }

  quota_settings {
    limit  = 10000
    period = "DAY"
  }
}

resource "aws_api_gateway_usage_plan_key" "main" {
  key_id        = aws_api_gateway_api_key.main.id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.main.id
}

# Output del API Key value
output "api_key_value" {
  value     = aws_api_gateway_api_key.main.value
  sensitive = true
}
