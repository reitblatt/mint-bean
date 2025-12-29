# MintBean AWS Terraform Deployment

This directory contains Terraform infrastructure-as-code to deploy MintBean on AWS with a single command.

## What Gets Created

This Terraform configuration creates a complete production-ready environment:

### Networking
- **VPC** with public and private subnets across 2 availability zones
- **Internet Gateway** for public internet access
- **NAT Gateway** for private subnet internet access
- **Route Tables** for public and private subnets

### Compute
- **ECS Fargate Cluster** for container orchestration
- **ECS Services** for backend and frontend
- **Application Load Balancer** with SSL/TLS support
- **Auto Scaling** (optional)

### Database
- **RDS PostgreSQL** instance in private subnet
- **Automated backups** (7-day retention)
- **Encryption at rest**

### Security
- **Security Groups** with least-privilege access
- **AWS Secrets Manager** for sensitive credentials
- **IAM Roles** with minimal permissions

### Storage
- **S3 Bucket** for beancount files (versioned, encrypted)
- **ECR Repositories** for Docker images

### Monitoring
- **CloudWatch Log Groups** for application logs
- **CloudWatch Metrics** (via Prometheus)

## Prerequisites

1. **AWS Account** with administrative access
2. **AWS CLI** configured with credentials
   ```bash
   aws configure
   ```

3. **Terraform** installed (>= 1.0)
   ```bash
   # macOS
   brew install terraform

   # Linux
   wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
   unzip terraform_1.6.0_linux_amd64.zip
   sudo mv terraform /usr/local/bin/
   ```

4. **Domain name** (optional, but recommended for SSL)

5. **ACM Certificate** (if using HTTPS)
   ```bash
   # Request certificate
   aws acm request-certificate \
     --domain-name mint.example.com \
     --validation-method DNS \
     --region us-east-1

   # Note the certificate ARN for terraform.tfvars
   ```

## Quick Start

### 1. Configure Variables

Create a `terraform.tfvars` file:

```hcl
# Required
aws_region  = "us-east-1"
domain_name = "mint.example.com"

# Optional - customize as needed
environment         = "production"
project_name        = "mintbean"
db_instance_class   = "db.t4g.micro"
certificate_arn     = "arn:aws:acm:us-east-1:xxxxx:certificate/xxxxx"  # For HTTPS

# Advanced (optional)
vpc_cidr            = "10.0.0.0/16"
availability_zones  = ["us-east-1a", "us-east-1b"]
backend_cpu         = 512
backend_memory      = 1024
frontend_cpu        = 256
frontend_memory     = 512
desired_count       = 1
```

### 2. Deploy Infrastructure

```bash
# Initialize Terraform
terraform init

# Review the plan
terraform plan

# Apply the configuration
terraform apply
```

This will create all AWS resources in **~15-20 minutes**.

### 3. Build and Push Docker Images

After Terraform completes, get the ECR repository URLs:

```bash
# Get repository URLs
BACKEND_REPO=$(terraform output -raw backend_ecr_repository_url)
FRONTEND_REPO=$(terraform output -raw frontend_ecr_repository_url)
AWS_REGION=$(terraform output -raw aws_region || echo "us-east-1")

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $BACKEND_REPO

# Build and push backend
docker build -t $BACKEND_REPO:latest -f ../../backend/Dockerfile ../../backend/
docker push $BACKEND_REPO:latest

# Build and push frontend
docker build -t $FRONTEND_REPO:latest -f ../../frontend/Dockerfile ../../frontend/
docker push $FRONTEND_REPO:latest
```

### 4. Deploy ECS Services

```bash
# Get cluster and service names
CLUSTER=$(terraform output -raw ecs_cluster_name)
BACKEND_SERVICE=$(terraform output -raw backend_service_name)
FRONTEND_SERVICE=$(terraform output -raw frontend_service_name)

# Force new deployment
aws ecs update-service --cluster $CLUSTER --service $BACKEND_SERVICE --force-new-deployment
aws ecs update-service --cluster $CLUSTER --service $FRONTEND_SERVICE --force-new-deployment
```

### 5. Configure DNS

Point your domain to the ALB:

```bash
# Get ALB DNS name
terraform output alb_dns_name

# Create DNS record (Route 53 example)
# A Record (ALIAS): mint.example.com → alb-dns-name

# Or use CloudFlare, etc.
```

### 6. Access Setup Wizard

Navigate to your domain (or ALB DNS) and complete the interactive setup:

```bash
# Get application URL
terraform output application_url

# Open in browser and follow setup wizard
```

## Cost Estimate

Monthly costs (approximate):

| Service | Configuration | Cost |
|---------|--------------|------|
| ECS Fargate | 2 tasks (0.75 vCPU, 1.5GB RAM) | $30 |
| RDS PostgreSQL | db.t4g.micro | $15-20 |
| Application Load Balancer | | $20 |
| NAT Gateway | | $32 |
| Secrets Manager | 3 secrets | $1.50 |
| S3 + Data Transfer | Minimal | $1-5 |
| **Total** | | **$99-108/month** |

### Cost Optimization

To reduce costs to ~$50-70/month:

1. **Remove NAT Gateway** (if ECS tasks don't need internet access):
   ```hcl
   # Comment out NAT Gateway in modules/vpc/main.tf
   # Use VPC endpoints for AWS services instead
   ```

2. **Use Fargate Spot** (50-70% discount):
   ```hcl
   # In modules/ecs/main.tf
   capacity_provider = "FARGATE_SPOT"
   ```

3. **Use smaller RDS instance**:
   ```hcl
   db_instance_class = "db.t4g.micro"  # Already the smallest
   ```

4. **Alternative**: Use AWS Lightsail for ~$22-55/month (see DEPLOYMENT_AWS.md)

## Directory Structure

```
terraform/aws/
├── main.tf                 # Main configuration
├── variables.tf            # Input variables
├── outputs.tf              # Output values
├── terraform.tfvars        # Your configuration (create this)
├── README.md               # This file
└── modules/
    ├── vpc/                # VPC and networking
    ├── security/           # Security groups
    ├── database/           # RDS PostgreSQL
    ├── secrets/            # AWS Secrets Manager
    ├── storage/            # S3 bucket
    ├── ecr/                # Container registry
    ├── ecs/                # ECS cluster and services
    └── alb/                # Application Load Balancer
```

## Module Customization

### VPC Module
- Customize CIDR blocks
- Add/remove availability zones
- Configure NAT Gateway options

### Database Module
- Change instance size
- Configure backups
- Enable Multi-AZ (for high availability)

### ECS Module
- Adjust CPU/memory allocation
- Configure auto-scaling
- Add health checks

### ALB Module
- Configure SSL policies
- Add WAF integration
- Set up custom routing rules

## Advanced Configuration

### Enable Auto Scaling

Add to `terraform.tfvars`:

```hcl
autoscaling_enabled = true
min_capacity        = 1
max_capacity        = 10
cpu_target          = 70
memory_target       = 80
```

### Enable Multi-AZ RDS

```hcl
db_multi_az = true  # Increases cost ~2x
```

### Add Custom Domain

```hcl
domain_name     = "mint.example.com"
certificate_arn = "arn:aws:acm:us-east-1:xxxxx:certificate/xxxxx"
```

## Maintenance

### Update Application

```bash
# Push new images
docker push $BACKEND_REPO:latest
docker push $FRONTEND_REPO:latest

# Force deployment
aws ecs update-service --cluster $CLUSTER --service $BACKEND_SERVICE --force-new-deployment
```

### View Logs

```bash
# Backend logs
aws logs tail /ecs/mintbean-backend-production --follow

# Frontend logs
aws logs tail /ecs/mintbean-frontend-production --follow
```

### Database Backups

```bash
# Create manual snapshot
aws rds create-db-snapshot \
  --db-instance-identifier mintbean-db-production \
  --db-snapshot-identifier mintbean-manual-$(date +%Y%m%d)
```

### Scale Services

```bash
# Scale to 2 tasks
aws ecs update-service \
  --cluster $CLUSTER \
  --service $BACKEND_SERVICE \
  --desired-count 2
```

## Destroy Infrastructure

**WARNING**: This will delete ALL resources including the database!

```bash
# Backup database first!
aws rds create-db-snapshot \
  --db-instance-identifier mintbean-db-production \
  --db-snapshot-identifier mintbean-final-backup

# Destroy all resources
terraform destroy
```

## Troubleshooting

### Terraform Init Fails

```bash
# Clear cache and reinitialize
rm -rf .terraform .terraform.lock.hcl
terraform init
```

### ECS Tasks Won't Start

```bash
# Check task logs
aws logs tail /ecs/mintbean-backend-production --follow

# Check service events
aws ecs describe-services \
  --cluster $CLUSTER \
  --services $BACKEND_SERVICE \
  --query 'services[0].events[0:5]'
```

### Database Connection Issues

```bash
# Verify security group allows ECS → RDS
aws ec2 describe-security-groups --group-ids sg-xxxxx

# Test from ECS task
aws ecs execute-command \
  --cluster $CLUSTER \
  --task <task-id> \
  --container backend \
  --interactive \
  --command "/bin/sh"
```

### SSL Certificate Issues

```bash
# Check certificate status
aws acm describe-certificate --certificate-arn arn:aws:acm:...

# Validate DNS records
dig _xxxxx.mint.example.com
```

## Security Best Practices

- ✅ All secrets in AWS Secrets Manager (encrypted)
- ✅ Database in private subnet (no public access)
- ✅ Security groups follow least-privilege
- ✅ SSL/TLS encryption with ACM
- ✅ Automated database backups (7 days)
- ✅ CloudWatch logging enabled
- ✅ IAM roles with minimal permissions
- ✅ S3 bucket encryption enabled
- ✅ Versioning enabled on S3

## Support

For issues or questions:
- Review [DEPLOYMENT_AWS.md](../../DEPLOYMENT_AWS.md) for manual steps
- Check Terraform output for helpful messages
- Review AWS CloudWatch logs
- Open an issue on GitHub

## License

Same as main project (MIT License)
