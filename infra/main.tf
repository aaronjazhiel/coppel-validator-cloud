terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "aws" {
  region = var.region
}

# ── Variables ─────────────────────────────────────────────────
variable "region" {
  default = "us-east-1"
}

variable "project" {
  default = "coppel-cloud"
}

variable "environment" {
  default = "prod"
}

# ── Data ──────────────────────────────────────────────────────
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
  region     = data.aws_region.current.name
  prefix     = "${var.project}-${var.environment}"
}
