# ── Lambda Layer (dependencias) ───────────────────────────────
resource "aws_lambda_layer_version" "deps" {
  filename            = "${path.module}/../backend/layer.zip"
  layer_name          = "${local.prefix}-deps"
  compatible_runtimes = ["python3.12"]
  source_code_hash    = filebase64sha256("${path.module}/../backend/layer.zip")
}

# ── Paquete de código Lambda ──────────────────────────────────
data "archive_file" "lambda_code" {
  type        = "zip"
  source_dir  = "${path.module}/../backend"
  output_path = "${path.module}/../backend/lambda.zip"
  excludes    = ["layer.zip", "layer", "requirements.txt", "__pycache__"]
}

# ── Variables de entorno comunes ──────────────────────────────
locals {
  lambda_env = {
    BUCKET_NAME = aws_s3_bucket.iniciativas.id
    DB_HOST     = aws_db_instance.main.address
    DB_PORT     = "5432"
    DB_NAME     = "coppel_cloud"
    DB_USER     = "coppel_admin"
    DB_PASSWORD = random_password.rds.result
  }
}

# ── Lambda: crear_iniciativa ──────────────────────────────────
resource "aws_lambda_function" "crear_iniciativa" {
  function_name    = "${local.prefix}-crear-iniciativa"
  handler          = "lambdas.crear_iniciativa.handler"
  runtime          = "python3.12"
  timeout          = 30
  memory_size      = 256
  role             = aws_iam_role.lambda_crud.arn
  filename         = data.archive_file.lambda_code.output_path
  source_code_hash = data.archive_file.lambda_code.output_base64sha256
  layers           = [aws_lambda_layer_version.deps.arn]

  environment { variables = local.lambda_env }
}

# ── Lambda: registrar_insumo ──────────────────────────────────
resource "aws_lambda_function" "registrar_insumo" {
  function_name    = "${local.prefix}-registrar-insumo"
  handler          = "lambdas.registrar_insumo.handler"
  runtime          = "python3.12"
  timeout          = 30
  memory_size      = 256
  role             = aws_iam_role.lambda_registrar.arn
  filename         = data.archive_file.lambda_code.output_path
  source_code_hash = data.archive_file.lambda_code.output_base64sha256
  layers           = [aws_lambda_layer_version.deps.arn]

  environment { variables = local.lambda_env }
}

resource "aws_lambda_permission" "s3_invoke_registrar" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.registrar_insumo.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.iniciativas.arn
}

# ── Lambda: procesar_iniciativa ───────────────────────────────
resource "aws_lambda_function" "procesar_iniciativa" {
  function_name    = "${local.prefix}-procesar"
  handler          = "lambdas.procesar_iniciativa.handler"
  runtime          = "python3.12"
  timeout          = 900
  memory_size      = 1024
  role             = aws_iam_role.lambda_ai.arn
  filename         = data.archive_file.lambda_code.output_path
  source_code_hash = data.archive_file.lambda_code.output_base64sha256
  layers           = [aws_lambda_layer_version.deps.arn]

  environment { variables = local.lambda_env }
}

# ── Lambda: ficha (GET/PUT) ───────────────────────────────────
resource "aws_lambda_function" "ficha" {
  function_name    = "${local.prefix}-ficha"
  handler          = "lambdas.ficha.handler"
  runtime          = "python3.12"
  timeout          = 30
  memory_size      = 256
  role             = aws_iam_role.lambda_crud.arn
  filename         = data.archive_file.lambda_code.output_path
  source_code_hash = data.archive_file.lambda_code.output_base64sha256
  layers           = [aws_lambda_layer_version.deps.arn]

  environment { variables = local.lambda_env }
}

# ── Lambda: generar_salidas ───────────────────────────────────
resource "aws_lambda_function" "generar_salidas" {
  function_name    = "${local.prefix}-generar"
  handler          = "lambdas.generar_salidas.handler"
  runtime          = "python3.12"
  timeout          = 900
  memory_size      = 1024
  role             = aws_iam_role.lambda_ai.arn
  filename         = data.archive_file.lambda_code.output_path
  source_code_hash = data.archive_file.lambda_code.output_base64sha256
  layers           = [aws_lambda_layer_version.deps.arn]

  environment { variables = local.lambda_env }
}

# ── Lambda: validar_iniciativa ───────────────────────────────
resource "aws_lambda_function" "validar_iniciativa" {
  function_name    = "${local.prefix}-validar"
  handler          = "lambdas.validar_iniciativa.handler"
  runtime          = "python3.12"
  timeout          = 300
  memory_size      = 512
  role             = aws_iam_role.lambda_ai.arn
  filename         = data.archive_file.lambda_code.output_path
  source_code_hash = data.archive_file.lambda_code.output_base64sha256
  layers           = [aws_lambda_layer_version.deps.arn]

  environment { variables = local.lambda_env }
}

# ── Lambda: listar_iniciativas ────────────────────────────────
resource "aws_lambda_function" "listar_iniciativas" {
  function_name    = "${local.prefix}-listar"
  handler          = "lambdas.listar_iniciativas.handler"
  runtime          = "python3.12"
  timeout          = 30
  memory_size      = 256
  role             = aws_iam_role.lambda_crud.arn
  filename         = data.archive_file.lambda_code.output_path
  source_code_hash = data.archive_file.lambda_code.output_base64sha256
  layers           = [aws_lambda_layer_version.deps.arn]

  environment { variables = local.lambda_env }
}

# ── Lambda: validar_worker (async) ────────────────────────────
resource "aws_lambda_function" "validar_worker" {
  function_name    = "${local.prefix}-validar-worker"
  handler          = "lambdas.validar_worker.handler"
  runtime          = "python3.12"
  timeout          = 900
  memory_size      = 1024
  role             = aws_iam_role.lambda_ai.arn
  filename         = data.archive_file.lambda_code.output_path
  source_code_hash = data.archive_file.lambda_code.output_base64sha256
  layers           = [aws_lambda_layer_version.deps.arn]

  environment { variables = local.lambda_env }
}

# ── Lambda: generar_propuesta (dispatcher) ────────────────────
resource "aws_lambda_function" "generar_propuesta" {
  function_name    = "${local.prefix}-generar-propuesta"
  handler          = "lambdas.generar_propuesta.handler"
  runtime          = "python3.12"
  timeout          = 30
  memory_size      = 256
  role             = aws_iam_role.lambda_ai.arn
  filename         = data.archive_file.lambda_code.output_path
  source_code_hash = data.archive_file.lambda_code.output_base64sha256
  layers           = [aws_lambda_layer_version.deps.arn]

  environment { variables = local.lambda_env }
}

# ── Lambda: propuesta_worker (async — MCP pricing + Word) ─────
resource "aws_lambda_function" "propuesta_worker" {
  function_name    = "${local.prefix}-propuesta-worker"
  handler          = "lambdas.propuesta_worker.handler"
  runtime          = "python3.12"
  timeout          = 900
  memory_size      = 1024
  role             = aws_iam_role.lambda_ai.arn
  filename         = data.archive_file.lambda_code.output_path
  source_code_hash = data.archive_file.lambda_code.output_base64sha256
  layers           = [aws_lambda_layer_version.deps.arn]

  environment { variables = local.lambda_env }
}
