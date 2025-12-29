terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "MintBean"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# Random suffix for unique resource names
resource "random_id" "suffix" {
  byte_length = 4
}

# VPC and Networking
module "vpc" {
  source = "./modules/vpc"

  vpc_cidr            = var.vpc_cidr
  availability_zones  = var.availability_zones
  environment         = var.environment
  project_name        = var.project_name
}

# Security Groups
module "security" {
  source = "./modules/security"

  vpc_id       = module.vpc.vpc_id
  environment  = var.environment
  project_name = var.project_name
}

# RDS PostgreSQL Database
module "database" {
  source = "./modules/database"

  vpc_id                = module.vpc.vpc_id
  private_subnet_ids    = module.vpc.private_subnet_ids
  database_sg_id        = module.security.database_sg_id
  db_instance_class     = var.db_instance_class
  db_allocated_storage  = var.db_allocated_storage
  db_name               = var.db_name
  db_username           = var.db_username
  environment           = var.environment
  project_name          = var.project_name
}

# Secrets Manager
module "secrets" {
  source = "./modules/secrets"

  database_url    = module.database.database_url
  environment     = var.environment
  project_name    = var.project_name
}

# S3 Bucket for Beancount files
module "storage" {
  source = "./modules/storage"

  environment  = var.environment
  project_name = var.project_name
  random_suffix = random_id.suffix.hex
}

# ECR Repositories
module "ecr" {
  source = "./modules/ecr"

  environment  = var.environment
  project_name = var.project_name
}

# ECS Cluster and Services
module "ecs" {
  source = "./modules/ecs"

  vpc_id               = module.vpc.vpc_id
  private_subnet_ids   = module.vpc.private_subnet_ids
  ecs_sg_id            = module.security.ecs_sg_id
  backend_ecr_url      = module.ecr.backend_repository_url
  frontend_ecr_url     = module.ecr.frontend_repository_url
  database_url_secret  = module.secrets.database_url_secret_arn
  encryption_key_secret = module.secrets.encryption_key_secret_arn
  secret_key_secret    = module.secrets.secret_key_secret_arn
  s3_bucket_name       = module.storage.bucket_name
  s3_bucket_arn        = module.storage.bucket_arn
  alb_target_group_backend_arn = module.alb.backend_target_group_arn
  alb_target_group_frontend_arn = module.alb.frontend_target_group_arn
  environment          = var.environment
  project_name         = var.project_name
  domain_name          = var.domain_name
}

# Application Load Balancer
module "alb" {
  source = "./modules/alb"

  vpc_id             = module.vpc.vpc_id
  public_subnet_ids  = module.vpc.public_subnet_ids
  alb_sg_id          = module.security.alb_sg_id
  certificate_arn    = var.certificate_arn
  environment        = var.environment
  project_name       = var.project_name
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "backend" {
  name              = "/ecs/${var.project_name}-backend-${var.environment}"
  retention_in_days = 7
}

resource "aws_cloudwatch_log_group" "frontend" {
  name              = "/ecs/${var.project_name}-frontend-${var.environment}"
  retention_in_days = 7
}
