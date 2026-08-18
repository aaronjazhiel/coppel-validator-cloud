# ── VPC default data source ───────────────────────────────────
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# ── Security Group: RDS (solo acceso desde Lambdas) ───────────
resource "aws_security_group" "rds" {
  name        = "${local.prefix}-rds-sg"
  description = "Acceso MySQL desde Lambdas"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.lambda.id]
  }

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Acceso publico PostgreSQL"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ── Security Group: Lambda (para conectarse a RDS) ────────────
resource "aws_security_group" "lambda" {
  name        = "${local.prefix}-lambda-sg"
  description = "Lambdas con acceso a RDS"
  vpc_id      = data.aws_vpc.default.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ── Subnet Group para RDS ─────────────────────────────────────
resource "aws_db_subnet_group" "main" {
  name       = "${local.prefix}-subnet-group"
  subnet_ids = data.aws_subnets.default.ids
}

# ── Password RDS en Secrets Manager ──────────────────────────
resource "random_password" "rds" {
  length           = 24
  special          = true
  override_special = "!#$%&*()-_=+[]{}?"
}

resource "aws_secretsmanager_secret" "rds" {
  name                    = "${local.prefix}/rds/password"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "rds" {
  secret_id     = aws_secretsmanager_secret.rds.id
  secret_string = jsonencode({
    username = "coppel_admin"
    password = random_password.rds.result
    host     = aws_db_instance.main.address
    port     = 3306
    dbname   = "coppel_cloud"
  })
}

# ── RDS PostgreSQL — Free Tier ───────────────────────────────
resource "aws_db_instance" "main" {
  identifier              = "${local.prefix}-postgres"
  engine                  = "postgres"
  engine_version          = "16"
  instance_class          = "db.t3.micro"
  allocated_storage       = 20
  storage_type            = "gp2"
  db_name                 = "coppel_cloud"
  username                = "coppel_admin"
  password                = random_password.rds.result
  db_subnet_group_name    = aws_db_subnet_group.main.name
  vpc_security_group_ids  = [aws_security_group.rds.id]
  publicly_accessible     = true
  skip_final_snapshot     = true
  deletion_protection     = false
  backup_retention_period = 0
  multi_az                = false

  tags = {
    Name = "${local.prefix}-postgres"
  }
}
