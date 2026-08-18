# ── API Gateway REST API ──────────────────────────────────────
resource "aws_api_gateway_rest_api" "api" {
  name = "${local.prefix}-api"
  endpoint_configuration { types = ["REGIONAL"] }
}

# /iniciativas
resource "aws_api_gateway_resource" "iniciativas" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "iniciativas"
}

# /iniciativas/{id}
resource "aws_api_gateway_resource" "iniciativa_id" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_resource.iniciativas.id
  path_part   = "{id}"
}

# /iniciativas/{id}/validar
resource "aws_api_gateway_resource" "validar" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_resource.iniciativa_id.id
  path_part   = "validar"
}

# /iniciativas/{id}/procesar
resource "aws_api_gateway_resource" "procesar" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_resource.iniciativa_id.id
  path_part   = "procesar"
}

# /iniciativas/{id}/ficha
resource "aws_api_gateway_resource" "ficha" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_resource.iniciativa_id.id
  path_part   = "ficha"
}

# /iniciativas/{id}/generar
resource "aws_api_gateway_resource" "generar" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_resource.iniciativa_id.id
  path_part   = "generar"
}

# /iniciativas/{id}/generar/{tipo}
resource "aws_api_gateway_resource" "generar_tipo" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_resource.generar.id
  path_part   = "{tipo}"
}

# /iniciativas/{id}/propuesta
resource "aws_api_gateway_resource" "propuesta" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_resource.iniciativa_id.id
  path_part   = "propuesta"
}

# /iniciativas/{id}/resultados
resource "aws_api_gateway_resource" "resultados" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_resource.iniciativa_id.id
  path_part   = "resultados"
}

# /iniciativas/{id}/resultados/{tipo}
resource "aws_api_gateway_resource" "resultados_tipo" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_resource.resultados.id
  path_part   = "{tipo}"
}

# ── Methods ───────────────────────────────────────────────────

# POST /iniciativas
resource "aws_api_gateway_method" "post_iniciativas" {
  rest_api_id      = aws_api_gateway_rest_api.api.id
  resource_id      = aws_api_gateway_resource.iniciativas.id
  http_method      = "POST"
  authorization    = "NONE"
  api_key_required = true
}

resource "aws_api_gateway_integration" "post_iniciativas" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.iniciativas.id
  http_method             = aws_api_gateway_method.post_iniciativas.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.crear_iniciativa.invoke_arn
}

# GET /iniciativas
resource "aws_api_gateway_method" "get_iniciativas" {
  rest_api_id      = aws_api_gateway_rest_api.api.id
  resource_id      = aws_api_gateway_resource.iniciativas.id
  http_method      = "GET"
  authorization    = "NONE"
  api_key_required = true
}

resource "aws_api_gateway_integration" "get_iniciativas" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.iniciativas.id
  http_method             = aws_api_gateway_method.get_iniciativas.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.listar_iniciativas.invoke_arn
}

# GET /iniciativas/{id}
resource "aws_api_gateway_method" "get_iniciativa" {
  rest_api_id      = aws_api_gateway_rest_api.api.id
  resource_id      = aws_api_gateway_resource.iniciativa_id.id
  http_method      = "GET"
  authorization    = "NONE"
  api_key_required = true
}

resource "aws_api_gateway_integration" "get_iniciativa" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.iniciativa_id.id
  http_method             = aws_api_gateway_method.get_iniciativa.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.listar_iniciativas.invoke_arn
}

# POST /iniciativas/{id}/validar
resource "aws_api_gateway_method" "post_validar" {
  rest_api_id      = aws_api_gateway_rest_api.api.id
  resource_id      = aws_api_gateway_resource.validar.id
  http_method      = "POST"
  authorization    = "NONE"
  api_key_required = true
}

resource "aws_api_gateway_integration" "post_validar" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.validar.id
  http_method             = aws_api_gateway_method.post_validar.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.validar_iniciativa.invoke_arn
}

# POST /iniciativas/{id}/procesar
resource "aws_api_gateway_method" "post_procesar" {
  rest_api_id      = aws_api_gateway_rest_api.api.id
  resource_id      = aws_api_gateway_resource.procesar.id
  http_method      = "POST"
  authorization    = "NONE"
  api_key_required = true
}

resource "aws_api_gateway_integration" "post_procesar" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.procesar.id
  http_method             = aws_api_gateway_method.post_procesar.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.procesar_iniciativa.invoke_arn
}

# GET /iniciativas/{id}/ficha
resource "aws_api_gateway_method" "get_ficha" {
  rest_api_id      = aws_api_gateway_rest_api.api.id
  resource_id      = aws_api_gateway_resource.ficha.id
  http_method      = "GET"
  authorization    = "NONE"
  api_key_required = true
}

resource "aws_api_gateway_integration" "get_ficha" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.ficha.id
  http_method             = aws_api_gateway_method.get_ficha.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.ficha.invoke_arn
}

# PUT /iniciativas/{id}/ficha
resource "aws_api_gateway_method" "put_ficha" {
  rest_api_id      = aws_api_gateway_rest_api.api.id
  resource_id      = aws_api_gateway_resource.ficha.id
  http_method      = "PUT"
  authorization    = "NONE"
  api_key_required = true
}

resource "aws_api_gateway_integration" "put_ficha" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.ficha.id
  http_method             = aws_api_gateway_method.put_ficha.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.ficha.invoke_arn
}

# POST /iniciativas/{id}/generar/{tipo}
resource "aws_api_gateway_method" "post_generar" {
  rest_api_id      = aws_api_gateway_rest_api.api.id
  resource_id      = aws_api_gateway_resource.generar_tipo.id
  http_method      = "POST"
  authorization    = "NONE"
  api_key_required = true
}

resource "aws_api_gateway_integration" "post_generar" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.generar_tipo.id
  http_method             = aws_api_gateway_method.post_generar.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.generar_salidas.invoke_arn
}

# POST /iniciativas/{id}/propuesta
resource "aws_api_gateway_method" "post_propuesta" {
  rest_api_id      = aws_api_gateway_rest_api.api.id
  resource_id      = aws_api_gateway_resource.propuesta.id
  http_method      = "POST"
  authorization    = "NONE"
  api_key_required = true
}

resource "aws_api_gateway_integration" "post_propuesta" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.propuesta.id
  http_method             = aws_api_gateway_method.post_propuesta.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.generar_propuesta.invoke_arn
}

# GET /iniciativas/{id}/resultados/{tipo}
resource "aws_api_gateway_method" "get_resultados" {
  rest_api_id      = aws_api_gateway_rest_api.api.id
  resource_id      = aws_api_gateway_resource.resultados_tipo.id
  http_method      = "GET"
  authorization    = "NONE"
  api_key_required = true
}

resource "aws_api_gateway_integration" "get_resultados" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.resultados_tipo.id
  http_method             = aws_api_gateway_method.get_resultados.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.listar_iniciativas.invoke_arn
}

# ── CORS (OPTIONS) for all resources ─────────────────────────
module "cors_iniciativas" {
  source      = "./modules/cors"
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.iniciativas.id
}

module "cors_iniciativa_id" {
  source      = "./modules/cors"
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.iniciativa_id.id
}

module "cors_validar" {
  source      = "./modules/cors"
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.validar.id
}

module "cors_procesar" {
  source      = "./modules/cors"
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.procesar.id
}

module "cors_ficha" {
  source      = "./modules/cors"
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.ficha.id
}

module "cors_generar_tipo" {
  source      = "./modules/cors"
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.generar_tipo.id
}

module "cors_propuesta" {
  source      = "./modules/cors"
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.propuesta.id
}

module "cors_resultados_tipo" {
  source      = "./modules/cors"
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.resultados_tipo.id
}

# ── Gateway Responses (CORS on errors) ────────────────────────
resource "aws_api_gateway_gateway_response" "response_4xx" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  response_type = "DEFAULT_4XX"
  response_parameters = {
    "gatewayresponse.header.Access-Control-Allow-Origin"  = "'*'"
    "gatewayresponse.header.Access-Control-Allow-Headers" = "'Content-Type,x-api-key'"
    "gatewayresponse.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,OPTIONS'"
  }
}

resource "aws_api_gateway_gateway_response" "response_5xx" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  response_type = "DEFAULT_5XX"
  response_parameters = {
    "gatewayresponse.header.Access-Control-Allow-Origin"  = "'*'"
    "gatewayresponse.header.Access-Control-Allow-Headers" = "'Content-Type,x-api-key'"
    "gatewayresponse.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,OPTIONS'"
  }
}

# ── Deployment ────────────────────────────────────────────────
resource "aws_api_gateway_deployment" "deploy" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  depends_on = [
    aws_api_gateway_integration.post_validar,
    aws_api_gateway_integration.post_iniciativas,
    aws_api_gateway_integration.get_iniciativas,
    aws_api_gateway_integration.get_iniciativa,
    aws_api_gateway_integration.post_procesar,
    aws_api_gateway_integration.get_ficha,
    aws_api_gateway_integration.put_ficha,
    aws_api_gateway_integration.post_generar,
    aws_api_gateway_integration.post_propuesta,
    aws_api_gateway_integration.get_resultados,
  ]
  triggers = { redeployment = timestamp() }
  lifecycle { create_before_destroy = true }
}

resource "aws_api_gateway_stage" "prod" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  deployment_id = aws_api_gateway_deployment.deploy.id
  stage_name    = "prod"
}

# ── Lambda Permissions for API Gateway ────────────────────────
resource "aws_lambda_permission" "apigw_validar" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.validar_iniciativa.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "apigw_crear" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.crear_iniciativa.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "apigw_listar" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.listar_iniciativas.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "apigw_procesar" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.procesar_iniciativa.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "apigw_ficha" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ficha.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "apigw_generar" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.generar_salidas.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "apigw_propuesta" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.generar_propuesta.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api.execution_arn}/*/*"
}
