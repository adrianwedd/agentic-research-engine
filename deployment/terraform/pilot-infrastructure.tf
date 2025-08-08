# ORCHESTRIX Pilot Integration - Terraform Infrastructure
# Classification: CRITICAL - PILOT DEPLOYMENT
# Last Updated: 2025-08-08

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
  }

  backend "s3" {
    bucket         = "orchestrix-pilot-terraform-state"
    key            = "pilot/terraform.tfstate"
    region         = var.aws_region
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}

# Variables
variable "aws_region" {
  description = "AWS region for pilot deployment"
  type        = string
  default     = "us-west-2"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "pilot"
}

variable "project" {
  description = "Project name"
  type        = string
  default     = "orchestrix-pilot"
}

# Local values
locals {
  common_tags = {
    Environment = var.environment
    Project     = var.project
    ManagedBy   = "terraform"
    Purpose     = "orchestrix-pilot-integration"
    CostCenter  = "research-development"
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

# VPC Configuration
resource "aws_vpc" "pilot_vpc" {
  cidr_block           = "10.100.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(local.common_tags, {
    Name = "${var.project}-vpc"
  })
}

# Internet Gateway
resource "aws_internet_gateway" "pilot_igw" {
  vpc_id = aws_vpc.pilot_vpc.id

  tags = merge(local.common_tags, {
    Name = "${var.project}-igw"
  })
}

# Public Subnets (DMZ)
resource "aws_subnet" "public_subnets" {
  count = 2

  vpc_id                  = aws_vpc.pilot_vpc.id
  cidr_block              = "10.100.${count.index + 1}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = merge(local.common_tags, {
    Name                     = "${var.project}-public-${count.index + 1}"
    "kubernetes.io/role/elb" = "1"
  })
}

# Private Subnets (Agent Services)
resource "aws_subnet" "private_subnets" {
  count = 2

  vpc_id            = aws_vpc.pilot_vpc.id
  cidr_block        = "10.100.${count.index + 10}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = merge(local.common_tags, {
    Name                              = "${var.project}-private-${count.index + 1}"
    "kubernetes.io/role/internal-elb" = "1"
  })
}

# Database Subnets
resource "aws_subnet" "database_subnets" {
  count = 2

  vpc_id            = aws_vpc.pilot_vpc.id
  cidr_block        = "10.100.${count.index + 20}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = merge(local.common_tags, {
    Name = "${var.project}-database-${count.index + 1}"
  })
}

# Elastic IP for NAT Gateway
resource "aws_eip" "nat_eip" {
  domain = "vpc"
  depends_on = [aws_internet_gateway.pilot_igw]

  tags = merge(local.common_tags, {
    Name = "${var.project}-nat-eip"
  })
}

# NAT Gateway
resource "aws_nat_gateway" "pilot_nat" {
  allocation_id = aws_eip.nat_eip.id
  subnet_id     = aws_subnet.public_subnets[0].id
  depends_on    = [aws_internet_gateway.pilot_igw]

  tags = merge(local.common_tags, {
    Name = "${var.project}-nat-gateway"
  })
}

# Route Tables
resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.pilot_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.pilot_igw.id
  }

  tags = merge(local.common_tags, {
    Name = "${var.project}-public-rt"
  })
}

resource "aws_route_table" "private_rt" {
  vpc_id = aws_vpc.pilot_vpc.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.pilot_nat.id
  }

  tags = merge(local.common_tags, {
    Name = "${var.project}-private-rt"
  })
}

# Route Table Associations
resource "aws_route_table_association" "public_rta" {
  count = length(aws_subnet.public_subnets)

  subnet_id      = aws_subnet.public_subnets[count.index].id
  route_table_id = aws_route_table.public_rt.id
}

resource "aws_route_table_association" "private_rta" {
  count = length(aws_subnet.private_subnets)

  subnet_id      = aws_subnet.private_subnets[count.index].id
  route_table_id = aws_route_table.private_rt.id
}

# Security Groups
resource "aws_security_group" "eks_cluster_sg" {
  name_prefix = "${var.project}-eks-cluster-"
  vpc_id      = aws_vpc.pilot_vpc.id

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.pilot_vpc.cidr_block]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${var.project}-eks-cluster-sg"
  })
}

resource "aws_security_group" "eks_node_sg" {
  name_prefix = "${var.project}-eks-node-"
  vpc_id      = aws_vpc.pilot_vpc.id

  ingress {
    description = "Node to node"
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    self        = true
  }

  ingress {
    description     = "Cluster API to node groups"
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_cluster_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${var.project}-eks-node-sg"
  })
}

resource "aws_security_group" "rds_sg" {
  name_prefix = "${var.project}-rds-"
  vpc_id      = aws_vpc.pilot_vpc.id

  ingress {
    description     = "PostgreSQL"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_node_sg.id]
  }

  tags = merge(local.common_tags, {
    Name = "${var.project}-rds-sg"
  })
}

# Database Subnet Group
resource "aws_db_subnet_group" "pilot_db_subnet_group" {
  name       = "${var.project}-db-subnet-group"
  subnet_ids = aws_subnet.database_subnets[*].id

  tags = merge(local.common_tags, {
    Name = "${var.project}-db-subnet-group"
  })
}

# RDS Instance
resource "aws_db_instance" "pilot_postgres" {
  identifier     = "${var.project}-postgres"
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.t3.micro"

  allocated_storage     = 20
  max_allocated_storage = 100
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name  = "reputation"
  username = "postgres"
  password = random_password.db_password.result

  vpc_security_group_ids = [aws_security_group.rds_sg.id]
  db_subnet_group_name   = aws_db_subnet_group.pilot_db_subnet_group.name

  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"

  skip_final_snapshot = false
  final_snapshot_identifier = "${var.project}-postgres-final-snapshot"

  tags = local.common_tags
}

resource "random_password" "db_password" {
  length  = 16
  special = true
}

# Secrets Manager
resource "aws_secretsmanager_secret" "pilot_secrets" {
  name = "${var.project}/application"
  
  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "pilot_secrets_version" {
  secret_id = aws_secretsmanager_secret.pilot_secrets.id
  secret_string = jsonencode({
    database_url = "postgresql://postgres:${random_password.db_password.result}@${aws_db_instance.pilot_postgres.endpoint}/reputation"
    reputation_api_keys = "evaluator:${random_password.evaluator_token.result},planner:${random_password.planner_token.result},admin:${random_password.admin_token.result}"
  })
}

resource "random_password" "evaluator_token" {
  length  = 32
  special = false
}

resource "random_password" "planner_token" {
  length  = 32
  special = false
}

resource "random_password" "admin_token" {
  length  = 32
  special = false
}

# EKS Cluster
resource "aws_eks_cluster" "pilot_cluster" {
  name     = "${var.project}-cluster"
  role_arn = aws_iam_role.eks_cluster_role.arn
  version  = "1.28"

  vpc_config {
    subnet_ids              = concat(aws_subnet.private_subnets[*].id, aws_subnet.public_subnets[*].id)
    security_group_ids      = [aws_security_group.eks_cluster_sg.id]
    endpoint_private_access = true
    endpoint_public_access  = true
    public_access_cidrs     = ["0.0.0.0/0"]
  }

  enabled_cluster_log_types = ["api", "audit", "authenticator", "controllerManager", "scheduler"]

  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_policy,
    aws_iam_role_policy_attachment.eks_vpc_resource_controller,
  ]

  tags = local.common_tags
}

# EKS Node Group
resource "aws_eks_node_group" "pilot_nodes" {
  cluster_name    = aws_eks_cluster.pilot_cluster.name
  node_group_name = "${var.project}-nodes"
  node_role_arn   = aws_iam_role.eks_node_role.arn
  subnet_ids      = aws_subnet.private_subnets[*].id

  scaling_config {
    desired_size = 3
    max_size     = 6
    min_size     = 2
  }

  update_config {
    max_unavailable = 1
  }

  instance_types = ["t3.medium"]
  capacity_type  = "ON_DEMAND"

  depends_on = [
    aws_iam_role_policy_attachment.eks_worker_node_policy,
    aws_iam_role_policy_attachment.eks_cni_policy,
    aws_iam_role_policy_attachment.eks_container_registry_policy,
  ]

  tags = local.common_tags
}

# IAM Roles and Policies
resource "aws_iam_role" "eks_cluster_role" {
  name = "${var.project}-eks-cluster-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "eks.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role" "eks_node_role" {
  name = "${var.project}-eks-node-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

# Policy Attachments
resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.eks_cluster_role.name
}

resource "aws_iam_role_policy_attachment" "eks_vpc_resource_controller" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSVPCResourceController"
  role       = aws_iam_role.eks_cluster_role.name
}

resource "aws_iam_role_policy_attachment" "eks_worker_node_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.eks_node_role.name
}

resource "aws_iam_role_policy_attachment" "eks_cni_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.eks_node_role.name
}

resource "aws_iam_role_policy_attachment" "eks_container_registry_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.eks_node_role.name
}

# External Secrets Operator IAM Role
resource "aws_iam_role" "external_secrets_role" {
  name = "${var.project}-external-secrets-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRoleWithWebIdentity"
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.eks.arn
        }
        Condition = {
          StringEquals = {
            "${replace(aws_eks_cluster.pilot_cluster.identity[0].oidc[0].issuer, "https://", "")}:sub": "system:serviceaccount:external-secrets:external-secrets"
            "${replace(aws_eks_cluster.pilot_cluster.identity[0].oidc[0].issuer, "https://", "")}:aud": "sts.amazonaws.com"
          }
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_policy" "external_secrets_policy" {
  name = "${var.project}-external-secrets-policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = "${aws_secretsmanager_secret.pilot_secrets.arn}*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "external_secrets_policy_attachment" {
  role       = aws_iam_role.external_secrets_role.name
  policy_arn = aws_iam_policy.external_secrets_policy.arn
}

# OIDC Provider
data "tls_certificate" "eks_oidc_root_ca" {
  url = aws_eks_cluster.pilot_cluster.identity[0].oidc[0].issuer
}

resource "aws_iam_openid_connect_provider" "eks" {
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.eks_oidc_root_ca.certificates[0].sha1_fingerprint]
  url             = aws_eks_cluster.pilot_cluster.identity[0].oidc[0].issuer

  tags = local.common_tags
}

# Outputs
output "cluster_name" {
  description = "EKS Cluster name"
  value       = aws_eks_cluster.pilot_cluster.name
}

output "cluster_endpoint" {
  description = "EKS Cluster endpoint"
  value       = aws_eks_cluster.pilot_cluster.endpoint
}

output "cluster_security_group_id" {
  description = "Security group ID attached to the EKS cluster"
  value       = aws_eks_cluster.pilot_cluster.vpc_config[0].cluster_security_group_id
}

output "database_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.pilot_postgres.endpoint
  sensitive   = true
}

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.pilot_vpc.id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = aws_subnet.private_subnets[*].id
}

output "secrets_manager_arn" {
  description = "Secrets Manager ARN"
  value       = aws_secretsmanager_secret.pilot_secrets.arn
}