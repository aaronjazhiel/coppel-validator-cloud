# ── S3: Bucket de Iniciativas (datos) ─────────────────────────
resource "aws_s3_bucket" "iniciativas" {
  bucket        = "${var.project}-iniciativas"
  force_destroy = false
}

resource "aws_s3_bucket_versioning" "iniciativas" {
  bucket = aws_s3_bucket.iniciativas.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "iniciativas" {
  bucket = aws_s3_bucket.iniciativas.id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "aws:kms" }
  }
}

resource "aws_s3_bucket_cors_configuration" "iniciativas" {
  bucket = aws_s3_bucket.iniciativas.id
  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT"]
    allowed_origins = ["*"]
    max_age_seconds = 3600
  }
}

# Notificación S3 → Lambda registrar_insumo
resource "aws_s3_bucket_notification" "insumos" {
  bucket = aws_s3_bucket.iniciativas.id
  lambda_function {
    lambda_function_arn = aws_lambda_function.registrar_insumo.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "iniciativas/"
  }
  depends_on = [aws_lambda_permission.s3_invoke_registrar]
}

# ── S3: Bucket del Portal (estático) ─────────────────────────
resource "aws_s3_bucket" "portal" {
  bucket        = "${var.project}-portal"
  force_destroy = false
}

resource "aws_s3_bucket_website_configuration" "portal" {
  bucket = aws_s3_bucket.portal.id
  index_document { suffix = "index.html" }
}

resource "aws_s3_bucket_public_access_block" "portal" {
  bucket                  = aws_s3_bucket.portal.id
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "portal" {
  bucket = aws_s3_bucket.portal.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "PublicRead"
      Effect    = "Allow"
      Principal = "*"
      Action    = "s3:GetObject"
      Resource  = "${aws_s3_bucket.portal.arn}/*"
    }]
  })
  depends_on = [aws_s3_bucket_public_access_block.portal]
}
