# Network Outputs
output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = module.vpc.private_subnet_ids
}

# Database Outputs
output "database_endpoint" {
  description = "RDS database endpoint"
  value       = module.database.database_endpoint
}

output "database_name" {
  description = "Database name"
  value       = module.database.database_name
}

# Secrets Outputs
output "database_url_secret_arn" {
  description = "ARN of database URL secret in Secrets Manager"
  value       = module.secrets.database_url_secret_arn
}

output "encryption_key_secret_arn" {
  description = "ARN of encryption key secret in Secrets Manager"
  value       = module.secrets.encryption_key_secret_arn
}

output "secret_key_secret_arn" {
  description = "ARN of secret key secret in Secrets Manager"
  value       = module.secrets.secret_key_secret_arn
}

# Storage Outputs
output "s3_bucket_name" {
  description = "S3 bucket name for beancount files"
  value       = module.storage.bucket_name
}

# ECR Outputs
output "backend_ecr_repository_url" {
  description = "Backend ECR repository URL"
  value       = module.ecr.backend_repository_url
}

output "frontend_ecr_repository_url" {
  description = "Frontend ECR repository URL"
  value       = module.ecr.frontend_repository_url
}

# ALB Outputs
output "alb_dns_name" {
  description = "ALB DNS name"
  value       = module.alb.alb_dns_name
}

output "alb_zone_id" {
  description = "ALB zone ID for Route53 alias records"
  value       = module.alb.alb_zone_id
}

# ECS Outputs
output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = module.ecs.cluster_name
}

output "backend_service_name" {
  description = "Backend ECS service name"
  value       = module.ecs.backend_service_name
}

output "frontend_service_name" {
  description = "Frontend ECS service name"
  value       = module.ecs.frontend_service_name
}

# Application URL
output "application_url" {
  description = "Application URL"
  value       = var.certificate_arn != "" ? "https://${var.domain_name}" : "http://${module.alb.alb_dns_name}"
}

# Setup Instructions
output "next_steps" {
  description = "Next steps to complete deployment"
  value = <<-EOT

    Deployment Complete! 🎉

    Next Steps:

    1. Point your domain to the ALB:
       DNS Record: ${var.domain_name} → ${module.alb.alb_dns_name}
       (Create an A record ALIAS to this ALB DNS name)

    2. Build and push Docker images to ECR:

       # Login to ECR
       aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${module.ecr.backend_repository_url}

       # Build and push backend
       docker build -t ${module.ecr.backend_repository_url}:latest -f backend/Dockerfile backend/
       docker push ${module.ecr.backend_repository_url}:latest

       # Build and push frontend
       docker build -t ${module.ecr.frontend_repository_url}:latest -f frontend/Dockerfile frontend/
       docker push ${module.ecr.frontend_repository_url}:latest

    3. Force ECS service update:
       aws ecs update-service --cluster ${module.ecs.cluster_name} --service ${module.ecs.backend_service_name} --force-new-deployment
       aws ecs update-service --cluster ${module.ecs.cluster_name} --service ${module.ecs.frontend_service_name} --force-new-deployment

    4. Access the setup wizard:
       URL: ${var.certificate_arn != "" ? "https://${var.domain_name}" : "http://${module.alb.alb_dns_name}"}

       The setup wizard will guide you through:
       - Admin account creation
       - Plaid credentials (optional)
       - Initial configuration

    5. Configure Plaid credentials (optional):
       After onboarding, update secrets in AWS Secrets Manager:
       aws secretsmanager update-secret --secret-id ${var.project_name}/plaid-client-id --secret-string "your_client_id"
       aws secretsmanager update-secret --secret-id ${var.project_name}/plaid-secret --secret-string "your_secret"

    Resources Created:
    - VPC: ${module.vpc.vpc_id}
    - RDS: ${module.database.database_endpoint}
    - S3 Bucket: ${module.storage.bucket_name}
    - ECS Cluster: ${module.ecs.cluster_name}
    - ALB: ${module.alb.alb_dns_name}

    Estimated Monthly Cost: $67-76 USD

    For detailed documentation, see DEPLOYMENT_AWS.md
  EOT
}
