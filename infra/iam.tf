# ── IAM: Rol base Lambda ──────────────────────────────────────
data "aws_iam_policy_document" "lambda_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

# Política: VPC (para conectarse a RDS)
resource "aws_iam_policy" "lambda_vpc" {
  name = "${local.prefix}-lambda-vpc"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = [
        "ec2:CreateNetworkInterface",
        "ec2:DescribeNetworkInterfaces",
        "ec2:DeleteNetworkInterface"
      ]
      Resource = "*"
    }]
  })
}

# Política: logs
resource "aws_iam_policy" "lambda_logs" {
  name = "${local.prefix}-lambda-logs"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
      Resource = "arn:aws:logs:${local.region}:${local.account_id}:*"
    }]
  })
}

# ── Rol: crear_iniciativa / listar / ficha ────────────────────
resource "aws_iam_role" "lambda_crud" {
  name               = "${local.prefix}-lambda-crud"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

resource "aws_iam_role_policy_attachment" "crud_logs" {
  role       = aws_iam_role.lambda_crud.name
  policy_arn = aws_iam_policy.lambda_logs.arn
}

resource "aws_iam_role_policy_attachment" "crud_vpc" {
  role       = aws_iam_role.lambda_crud.name
  policy_arn = aws_iam_policy.lambda_vpc.arn
}

resource "aws_iam_role_policy" "crud_dynamo_s3" {
  name = "dynamo-s3"
  role = aws_iam_role.lambda_crud.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem", "dynamodb:Query", "dynamodb:Scan"]
        Resource = [aws_dynamodb_table.iniciativas.arn, "${aws_dynamodb_table.iniciativas.arn}/index/*"]
      },
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject", "s3:ListBucket"]
        Resource = [aws_s3_bucket.iniciativas.arn, "${aws_s3_bucket.iniciativas.arn}/*"]
      }
    ]
  })
}

# ── Rol: registrar_insumo (S3 trigger) ───────────────────────
resource "aws_iam_role" "lambda_registrar" {
  name               = "${local.prefix}-lambda-registrar"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

resource "aws_iam_role_policy_attachment" "registrar_logs" {
  role       = aws_iam_role.lambda_registrar.name
  policy_arn = aws_iam_policy.lambda_logs.arn
}

resource "aws_iam_role_policy_attachment" "registrar_vpc" {
  role       = aws_iam_role.lambda_registrar.name
  policy_arn = aws_iam_policy.lambda_vpc.arn
}

resource "aws_iam_role_policy" "registrar_dynamo" {
  name = "dynamo"
  role = aws_iam_role.lambda_registrar.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem"]
      Resource = aws_dynamodb_table.iniciativas.arn
    }]
  })
}

# ── Rol: procesar / generar (Claude + self-invoke) ────────────
resource "aws_iam_role" "lambda_ai" {
  name               = "${local.prefix}-lambda-ai"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

resource "aws_iam_role_policy_attachment" "ai_logs" {
  role       = aws_iam_role.lambda_ai.name
  policy_arn = aws_iam_policy.lambda_logs.arn
}

resource "aws_iam_role_policy_attachment" "ai_vpc" {
  role       = aws_iam_role.lambda_ai.name
  policy_arn = aws_iam_policy.lambda_vpc.arn
}

resource "aws_iam_role_policy" "ai_full" {
  name = "ai-access"
  role = aws_iam_role.lambda_ai.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem", "dynamodb:Query"]
        Resource = [aws_dynamodb_table.iniciativas.arn, "${aws_dynamodb_table.iniciativas.arn}/index/*"]
      },
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject", "s3:ListBucket"]
        Resource = [aws_s3_bucket.iniciativas.arn, "${aws_s3_bucket.iniciativas.arn}/*"]
      },
      {
        Effect   = "Allow"
        Action   = "secretsmanager:GetSecretValue"
        Resource = "arn:aws:secretsmanager:${local.region}:${local.account_id}:secret:coppel-cloud/anthropic-api-key*"
      },
      {
        Effect   = "Allow"
        Action   = "lambda:InvokeFunction"
        Resource = [
          "arn:aws:lambda:${local.region}:${local.account_id}:function:${local.prefix}-procesar",
          "arn:aws:lambda:${local.region}:${local.account_id}:function:${local.prefix}-generar",
          "arn:aws:lambda:${local.region}:${local.account_id}:function:${local.prefix}-propuesta-worker",
          "arn:aws:lambda:${local.region}:${local.account_id}:function:${local.prefix}-validar-worker"
        ]
      },
      {
        Effect   = "Allow"
        Action   = ["pricing:GetProducts", "pricing:GetAttributeValues", "pricing:DescribeServices"]
        Resource = "*"
      }
    ]
  })
}
