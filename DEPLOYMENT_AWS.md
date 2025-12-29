# AWS Deployment Guide - Turn-Key Setup

This guide provides step-by-step instructions for deploying MintBean on AWS with a production-ready setup using managed services.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                          Internet                            │
└───────────────────────────┬─────────────────────────────────┘
                            │
                    ┌───────▼────────┐
                    │ Application     │
                    │ Load Balancer   │
                    │ (ALB)           │
                    └───────┬────────┘
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
┌───────▼────────┐                     ┌───────▼────────┐
│ ECS Service    │                     │ ECS Service    │
│ (Frontend)     │────────────────────▶│ (Backend)      │
│ - React/Nginx  │     Internal API    │ - FastAPI      │
└────────────────┘                     └───────┬────────┘
                                               │
                    ┌──────────────────────────┼──────────────────────┐
                    │                          │                      │
            ┌───────▼────────┐        ┌───────▼────────┐    ┌───────▼────────┐
            │ RDS PostgreSQL │        │ AWS Secrets    │    │ S3 Bucket      │
            │ (Database)     │        │ Manager        │    │ (Beancount)    │
            └────────────────┘        └────────────────┘    └────────────────┘
```

## Cost Estimate

**Monthly AWS Costs (Approximate)**:
- ECS Fargate (2 tasks, 0.5 vCPU, 1GB RAM): ~$30
- RDS PostgreSQL (db.t4g.micro): ~$15-20
- Application Load Balancer: ~$20
- Secrets Manager (3 secrets): ~$1.50
- S3 + Data Transfer: ~$1-5
- **Total: ~$67-76/month**

For lower costs, consider AWS Lightsail (see Alternative Deployment Options).

## Prerequisites

1. **AWS Account** with billing enabled
2. **AWS CLI** installed and configured
   ```bash
   # Install AWS CLI
   curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
   unzip awscliv2.zip
   sudo ./aws/install

   # Configure credentials
   aws configure
   ```

3. **Docker** installed locally (for building images)
4. **Domain name** (optional, but recommended for SSL)

## Step 1: Create AWS Resources

### 1.1 Create VPC and Networking

```bash
# Create VPC
aws ec2 create-vpc \
  --cidr-block 10.0.0.0/16 \
  --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=mintbean-vpc}]'

# Note the VPC ID from output
export VPC_ID=vpc-xxxxx

# Create public subnets (for ALB)
aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.1.0/24 \
  --availability-zone us-east-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=mintbean-public-1a}]'

aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.2.0/24 \
  --availability-zone us-east-1b \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=mintbean-public-1b}]'

# Note the subnet IDs
export PUBLIC_SUBNET_1=subnet-xxxxx
export PUBLIC_SUBNET_2=subnet-yyyyy

# Create private subnets (for ECS and RDS)
aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.11.0/24 \
  --availability-zone us-east-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=mintbean-private-1a}]'

aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.12.0/24 \
  --availability-zone us-east-1b \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=mintbean-private-1b}]'

# Note the private subnet IDs
export PRIVATE_SUBNET_1=subnet-aaaaa
export PRIVATE_SUBNET_2=subnet-bbbbb

# Create Internet Gateway
aws ec2 create-internet-gateway \
  --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=mintbean-igw}]'

export IGW_ID=igw-xxxxx

# Attach to VPC
aws ec2 attach-internet-gateway --vpc-id $VPC_ID --internet-gateway-id $IGW_ID

# Create and configure route table for public subnets
aws ec2 create-route-table --vpc-id $VPC_ID \
  --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=mintbean-public-rt}]'

export PUBLIC_RT_ID=rtb-xxxxx

aws ec2 create-route --route-table-id $PUBLIC_RT_ID \
  --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW_ID

aws ec2 associate-route-table --route-table-id $PUBLIC_RT_ID --subnet-id $PUBLIC_SUBNET_1
aws ec2 associate-route-table --route-table-id $PUBLIC_RT_ID --subnet-id $PUBLIC_SUBNET_2

# Create NAT Gateway for private subnets (optional, for internet access from ECS)
aws ec2 allocate-address --domain vpc
export EIP_ALLOC_ID=eipalloc-xxxxx

aws ec2 create-nat-gateway \
  --subnet-id $PUBLIC_SUBNET_1 \
  --allocation-id $EIP_ALLOC_ID \
  --tag-specifications 'ResourceType=natgateway,Tags=[{Key=Name,Value=mintbean-nat}]'

export NAT_GW_ID=nat-xxxxx

# Create route table for private subnets
aws ec2 create-route-table --vpc-id $VPC_ID \
  --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=mintbean-private-rt}]'

export PRIVATE_RT_ID=rtb-yyyyy

aws ec2 create-route --route-table-id $PRIVATE_RT_ID \
  --destination-cidr-block 0.0.0.0/0 --nat-gateway-id $NAT_GW_ID

aws ec2 associate-route-table --route-table-id $PRIVATE_RT_ID --subnet-id $PRIVATE_SUBNET_1
aws ec2 associate-route-table --route-table-id $PRIVATE_RT_ID --subnet-id $PRIVATE_SUBNET_2
```

### 1.2 Create Security Groups

```bash
# ALB Security Group (allow HTTP/HTTPS from internet)
aws ec2 create-security-group \
  --group-name mintbean-alb-sg \
  --description "Security group for MintBean ALB" \
  --vpc-id $VPC_ID

export ALB_SG_ID=sg-xxxxx

aws ec2 authorize-security-group-ingress \
  --group-id $ALB_SG_ID \
  --protocol tcp --port 80 --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
  --group-id $ALB_SG_ID \
  --protocol tcp --port 443 --cidr 0.0.0.0/0

# ECS Security Group (allow traffic from ALB)
aws ec2 create-security-group \
  --group-name mintbean-ecs-sg \
  --description "Security group for MintBean ECS tasks" \
  --vpc-id $VPC_ID

export ECS_SG_ID=sg-yyyyy

aws ec2 authorize-security-group-ingress \
  --group-id $ECS_SG_ID \
  --protocol tcp --port 8000 \
  --source-group $ALB_SG_ID

aws ec2 authorize-security-group-ingress \
  --group-id $ECS_SG_ID \
  --protocol tcp --port 80 \
  --source-group $ALB_SG_ID

# RDS Security Group (allow traffic from ECS)
aws ec2 create-security-group \
  --group-name mintbean-rds-sg \
  --description "Security group for MintBean RDS" \
  --vpc-id $VPC_ID

export RDS_SG_ID=sg-zzzzz

aws ec2 authorize-security-group-ingress \
  --group-id $RDS_SG_ID \
  --protocol tcp --port 5432 \
  --source-group $ECS_SG_ID
```

### 1.3 Create RDS PostgreSQL Database

```bash
# Create DB subnet group
aws rds create-db-subnet-group \
  --db-subnet-group-name mintbean-db-subnet-group \
  --db-subnet-group-description "Subnet group for MintBean RDS" \
  --subnet-ids $PRIVATE_SUBNET_1 $PRIVATE_SUBNET_2

# Generate strong database password
export DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
echo "Database password: $DB_PASSWORD"
# IMPORTANT: Save this password securely!

# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier mintbean-db \
  --db-instance-class db.t4g.micro \
  --engine postgres \
  --engine-version 15.4 \
  --master-username mintbean_admin \
  --master-user-password "$DB_PASSWORD" \
  --allocated-storage 20 \
  --db-subnet-group-name mintbean-db-subnet-group \
  --vpc-security-group-ids $RDS_SG_ID \
  --backup-retention-period 7 \
  --preferred-backup-window "03:00-04:00" \
  --preferred-maintenance-window "mon:04:00-mon:05:00" \
  --publicly-accessible false \
  --storage-encrypted \
  --no-multi-az

# Wait for DB to be available (takes 5-10 minutes)
aws rds wait db-instance-available --db-instance-identifier mintbean-db

# Get database endpoint
export DB_ENDPOINT=$(aws rds describe-db-instances \
  --db-instance-identifier mintbean-db \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text)

echo "Database endpoint: $DB_ENDPOINT"
```

### 1.4 Create Secrets in AWS Secrets Manager

```bash
# Generate encryption key
export ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# Generate secret key
export SECRET_KEY=$(openssl rand -hex 32)

# Store database URL
export DATABASE_URL="postgresql://mintbean_admin:${DB_PASSWORD}@${DB_ENDPOINT}:5432/postgres"

aws secretsmanager create-secret \
  --name mintbean/database-url \
  --description "MintBean database connection string" \
  --secret-string "$DATABASE_URL"

# Store encryption key
aws secretsmanager create-secret \
  --name mintbean/encryption-key \
  --description "MintBean Fernet encryption key" \
  --secret-string "$ENCRYPTION_KEY"

# Store secret key
aws secretsmanager create-secret \
  --name mintbean/secret-key \
  --description "MintBean JWT secret key" \
  --secret-string "$SECRET_KEY"

# You'll add Plaid credentials later via the setup wizard
```

### 1.5 Create S3 Bucket for Beancount Files

```bash
# Create S3 bucket (must be globally unique)
export BUCKET_NAME="mintbean-beancount-$(openssl rand -hex 4)"

aws s3api create-bucket \
  --bucket $BUCKET_NAME \
  --region us-east-1

# Enable versioning (recommended for beancount files)
aws s3api put-bucket-versioning \
  --bucket $BUCKET_NAME \
  --versioning-configuration Status=Enabled

# Block public access
aws s3api put-public-access-block \
  --bucket $BUCKET_NAME \
  --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

echo "S3 bucket: $BUCKET_NAME"
```

## Step 2: Build and Push Docker Images

### 2.1 Create ECR Repositories

```bash
# Create repository for backend
aws ecr create-repository --repository-name mintbean-backend

# Create repository for frontend
aws ecr create-repository --repository-name mintbean-frontend

# Get repository URIs
export BACKEND_REPO=$(aws ecr describe-repositories \
  --repository-names mintbean-backend \
  --query 'repositories[0].repositoryUri' \
  --output text)

export FRONTEND_REPO=$(aws ecr describe-repositories \
  --repository-names mintbean-frontend \
  --query 'repositories[0].repositoryUri' \
  --output text)

echo "Backend repo: $BACKEND_REPO"
echo "Frontend repo: $FRONTEND_REPO"
```

### 2.2 Build and Push Images

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin $BACKEND_REPO

# Build and push backend
cd /path/to/mintbean
docker build -t $BACKEND_REPO:latest -f backend/Dockerfile backend/
docker push $BACKEND_REPO:latest

# Build and push frontend
docker build -t $FRONTEND_REPO:latest -f frontend/Dockerfile frontend/
docker push $FRONTEND_REPO:latest
```

## Step 3: Create ECS Cluster and Services

### 3.1 Create ECS Cluster

```bash
aws ecs create-cluster --cluster-name mintbean-cluster
```

### 3.2 Create IAM Role for ECS Tasks

```bash
# Create trust policy document
cat > ecs-task-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create IAM role
aws iam create-role \
  --role-name mintbean-ecs-task-role \
  --assume-role-policy-document file://ecs-task-trust-policy.json

# Create policy for accessing secrets and S3
cat > ecs-task-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": [
        "arn:aws:secretsmanager:us-east-1:*:secret:mintbean/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::${BUCKET_NAME}",
        "arn:aws:s3:::${BUCKET_NAME}/*"
      ]
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name mintbean-ecs-task-role \
  --policy-name mintbean-ecs-task-policy \
  --policy-document file://ecs-task-policy.json

# Attach managed policy for ECS task execution
aws iam attach-role-policy \
  --role-name mintbean-ecs-task-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

export TASK_ROLE_ARN=$(aws iam get-role --role-name mintbean-ecs-task-role --query 'Role.Arn' --output text)
```

### 3.3 Create CloudWatch Log Groups

```bash
aws logs create-log-group --log-group-name /ecs/mintbean-backend
aws logs create-log-group --log-group-name /ecs/mintbean-frontend
```

### 3.4 Create ECS Task Definitions

```bash
# Backend task definition
cat > backend-task-def.json <<EOF
{
  "family": "mintbean-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "taskRoleArn": "$TASK_ROLE_ARN",
  "executionRoleArn": "$TASK_ROLE_ARN",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "$BACKEND_REPO:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "DEBUG", "value": "false"},
        {"name": "LOG_LEVEL", "value": "INFO"},
        {"name": "ALLOWED_ORIGINS", "value": "https://your-domain.com"}
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:*:secret:mintbean/database-url"
        },
        {
          "name": "ENCRYPTION_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:*:secret:mintbean/encryption-key"
        },
        {
          "name": "SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:*:secret:mintbean/secret-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/mintbean-backend",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
EOF

# Register task definition
aws ecs register-task-definition --cli-input-json file://backend-task-def.json

# Frontend task definition
cat > frontend-task-def.json <<EOF
{
  "family": "mintbean-frontend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "$TASK_ROLE_ARN",
  "containerDefinitions": [
    {
      "name": "frontend",
      "image": "$FRONTEND_REPO:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 80,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "API_URL", "value": "/api/v1"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/mintbean-frontend",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
EOF

aws ecs register-task-definition --cli-input-json file://frontend-task-def.json
```

### 3.5 Create Application Load Balancer

```bash
# Create ALB
aws elbv2 create-load-balancer \
  --name mintbean-alb \
  --subnets $PUBLIC_SUBNET_1 $PUBLIC_SUBNET_2 \
  --security-groups $ALB_SG_ID \
  --scheme internet-facing \
  --type application

export ALB_ARN=$(aws elbv2 describe-load-balancers \
  --names mintbean-alb \
  --query 'LoadBalancers[0].LoadBalancerArn' \
  --output text)

export ALB_DNS=$(aws elbv2 describe-load-balancers \
  --names mintbean-alb \
  --query 'LoadBalancers[0].DNSName' \
  --output text)

echo "ALB DNS: $ALB_DNS"

# Create target groups
aws elbv2 create-target-group \
  --name mintbean-backend-tg \
  --protocol HTTP \
  --port 8000 \
  --vpc-id $VPC_ID \
  --target-type ip \
  --health-check-path /health/live \
  --health-check-interval-seconds 30

export BACKEND_TG_ARN=$(aws elbv2 describe-target-groups \
  --names mintbean-backend-tg \
  --query 'TargetGroups[0].TargetGroupArn' \
  --output text)

aws elbv2 create-target-group \
  --name mintbean-frontend-tg \
  --protocol HTTP \
  --port 80 \
  --vpc-id $VPC_ID \
  --target-type ip \
  --health-check-path / \
  --health-check-interval-seconds 30

export FRONTEND_TG_ARN=$(aws elbv2 describe-target-groups \
  --names mintbean-frontend-tg \
  --query 'TargetGroups[0].TargetGroupArn' \
  --output text)

# Create listeners
aws elbv2 create-listener \
  --load-balancer-arn $ALB_ARN \
  --protocol HTTP \
  --port 80 \
  --default-actions Type=forward,TargetGroupArn=$FRONTEND_TG_ARN

export LISTENER_ARN=$(aws elbv2 describe-listeners \
  --load-balancer-arn $ALB_ARN \
  --query 'Listeners[0].ListenerArn' \
  --output text)

# Add rule for API traffic
aws elbv2 create-rule \
  --listener-arn $LISTENER_ARN \
  --priority 10 \
  --conditions Field=path-pattern,Values='/api/*' \
  --actions Type=forward,TargetGroupArn=$BACKEND_TG_ARN
```

### 3.6 Create ECS Services

```bash
# Backend service
aws ecs create-service \
  --cluster mintbean-cluster \
  --service-name mintbean-backend \
  --task-definition mintbean-backend \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$PRIVATE_SUBNET_1,$PRIVATE_SUBNET_2],securityGroups=[$ECS_SG_ID],assignPublicIp=DISABLED}" \
  --load-balancers "targetGroupArn=$BACKEND_TG_ARN,containerName=backend,containerPort=8000"

# Frontend service
aws ecs create-service \
  --cluster mintbean-cluster \
  --service-name mintbean-frontend \
  --task-definition mintbean-frontend \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$PRIVATE_SUBNET_1,$PRIVATE_SUBNET_2],securityGroups=[$ECS_SG_ID],assignPublicIp=DISABLED}" \
  --load-balancers "targetGroupArn=$FRONTEND_TG_ARN,containerName=frontend,containerPort=80"
```

## Step 4: Configure DNS and SSL

### 4.1 Point Your Domain to ALB

In your DNS provider (e.g., Route 53, Cloudflare):

1. Create an A record (or CNAME) pointing to the ALB DNS name
2. Example: `mint.example.com` → `mintbean-alb-xxxxx.us-east-1.elb.amazonaws.com`

### 4.2 Request SSL Certificate

```bash
# Request certificate from ACM
aws acm request-certificate \
  --domain-name mint.example.com \
  --validation-method DNS \
  --region us-east-1

export CERT_ARN=$(aws acm list-certificates \
  --query 'CertificateSummaryList[?DomainName==`mint.example.com`].CertificateArn' \
  --output text)

# Get DNS validation records
aws acm describe-certificate \
  --certificate-arn $CERT_ARN \
  --query 'Certificate.DomainValidationOptions[0].ResourceRecord'

# Add the CNAME record to your DNS provider
# Wait for validation (usually 5-30 minutes)
```

### 4.3 Add HTTPS Listener

```bash
# Create HTTPS listener
aws elbv2 create-listener \
  --load-balancer-arn $ALB_ARN \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=$CERT_ARN \
  --default-actions Type=forward,TargetGroupArn=$FRONTEND_TG_ARN

export HTTPS_LISTENER_ARN=$(aws elbv2 describe-listeners \
  --load-balancer-arn $ALB_ARN \
  --query 'Listeners[?Port==`443`].ListenerArn' \
  --output text)

# Add API rule to HTTPS listener
aws elbv2 create-rule \
  --listener-arn $HTTPS_LISTENER_ARN \
  --priority 10 \
  --conditions Field=path-pattern,Values='/api/*' \
  --actions Type=forward,TargetGroupArn=$BACKEND_TG_ARN

# Modify HTTP listener to redirect to HTTPS
aws elbv2 modify-listener \
  --listener-arn $LISTENER_ARN \
  --default-actions Type=redirect,RedirectConfig="{Protocol=HTTPS,Port=443,StatusCode=HTTP_301}"
```

## Step 5: First-Time Setup Wizard

Once your deployment is running:

1. Navigate to `https://mint.example.com` (or your ALB DNS)
2. You'll see the interactive setup wizard
3. Follow the prompts to:
   - Create admin account
   - Configure Plaid credentials (optional)
   - Set up your first beancount file
   - Complete initial configuration

The setup wizard will guide you through all remaining configuration steps.

## Maintenance and Operations

### View Application Logs

```bash
# Backend logs
aws logs tail /ecs/mintbean-backend --follow

# Frontend logs
aws logs tail /ecs/mintbean-frontend --follow
```

### Update Application

```bash
# Build new images
docker build -t $BACKEND_REPO:latest -f backend/Dockerfile backend/
docker push $BACKEND_REPO:latest

# Force new deployment
aws ecs update-service \
  --cluster mintbean-cluster \
  --service mintbean-backend \
  --force-new-deployment
```

### Database Backups

RDS automated backups are enabled (7-day retention). To create manual snapshot:

```bash
aws rds create-db-snapshot \
  --db-instance-identifier mintbean-db \
  --db-snapshot-identifier mintbean-manual-$(date +%Y%m%d-%H%M%S)
```

### Scaling

```bash
# Scale backend to 2 tasks
aws ecs update-service \
  --cluster mintbean-cluster \
  --service mintbean-backend \
  --desired-count 2
```

## Cost Optimization

### Option 1: Use Fargate Spot (50-70% savings)

```bash
# Update services to use Spot capacity
aws ecs update-service \
  --cluster mintbean-cluster \
  --service mintbean-backend \
  --capacity-provider-strategy capacityProvider=FARGATE_SPOT,weight=1
```

### Option 2: Use Reserved Instances for RDS

Purchase 1-year or 3-year reserved instances for ~40% savings.

### Option 3: AWS Lightsail (Simpler, Lower Cost)

For lower traffic, consider AWS Lightsail:
- Container service: $7-40/month
- Managed database: $15/month
- **Total: ~$22-55/month** (vs $67-76 on ECS)

## Troubleshooting

### Service Won't Start

```bash
# Check service events
aws ecs describe-services \
  --cluster mintbean-cluster \
  --services mintbean-backend \
  --query 'services[0].events[0:5]'

# Check task logs
aws logs tail /ecs/mintbean-backend --follow
```

### Database Connection Issues

```bash
# Verify security group allows ECS → RDS traffic
aws ec2 describe-security-groups --group-ids $RDS_SG_ID

# Test connection from ECS task (requires exec enabled)
aws ecs execute-command \
  --cluster mintbean-cluster \
  --task <task-id> \
  --container backend \
  --interactive \
  --command "/bin/bash"

# Then: pg_isready -h $DB_ENDPOINT -p 5432
```

### Health Check Failures

```bash
# Check target health
aws elbv2 describe-target-health --target-group-arn $BACKEND_TG_ARN

# Verify health endpoint works
curl http://<ecs-task-ip>:8000/health/live
```

## Security Best Practices

- ✅ All secrets stored in AWS Secrets Manager
- ✅ Database in private subnet (no public access)
- ✅ Security groups follow least-privilege
- ✅ SSL/TLS encryption with ACM
- ✅ Automated database backups
- ✅ CloudWatch logging enabled
- ✅ IAM roles with minimal permissions

## Next Steps

After deployment:

1. **Enable monitoring**: Set up CloudWatch alarms for ECS, RDS, ALB
2. **Configure CI/CD**: Set up GitHub Actions for automated deployments
3. **Enable WAF**: Add AWS WAF for additional security
4. **Set up Route 53**: Use Route 53 for better DNS management
5. **Configure backup strategy**: Implement additional backup procedures

## Alternative: One-Click Deployment with Terraform

See [terraform/aws/README.md](terraform/aws/README.md) for infrastructure-as-code deployment using Terraform (coming soon).
