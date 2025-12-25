# =============================================================================
# Mathvidya Infrastructure - Variables
# =============================================================================

# -----------------------------------------------------------------------------
# General Settings
# -----------------------------------------------------------------------------
variable "project_name" {
  description = "Name of the project, used for resource naming"
  type        = string
  default     = "mathvidya"
}

variable "environment" {
  description = "Environment name (prod, staging, dev)"
  type        = string
  default     = "prod"
}

variable "aws_region" {
  description = "AWS region for resources (Mumbai for India data residency)"
  type        = string
  default     = "ap-south-1"
}

variable "domain_name" {
  description = "Primary domain name for the application"
  type        = string
  default     = "mathvidya.com"
}

# -----------------------------------------------------------------------------
# Network Settings
# -----------------------------------------------------------------------------
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.11.0/24"]
}

# -----------------------------------------------------------------------------
# EC2 Settings
# -----------------------------------------------------------------------------
variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.small"
}

variable "root_volume_size" {
  description = "Size of root EBS volume in GB"
  type        = number
  default     = 30
}

variable "ssh_public_key" {
  description = "SSH public key for EC2 access"
  type        = string
  sensitive   = true
}

variable "ssh_allowed_cidrs" {
  description = "CIDR blocks allowed for SSH access"
  type        = list(string)
  default     = ["0.0.0.0/0"]  # Restrict this to your IP in production!
}

# -----------------------------------------------------------------------------
# Application Settings
# -----------------------------------------------------------------------------
variable "db_password" {
  description = "PostgreSQL database password"
  type        = string
  sensitive   = true
}

variable "secret_key" {
  description = "Application secret key for JWT tokens"
  type        = string
  sensitive   = true
}

# -----------------------------------------------------------------------------
# Monitoring Settings
# -----------------------------------------------------------------------------
variable "alarm_email" {
  description = "Email address for CloudWatch alarm notifications (optional)"
  type        = string
  default     = ""
}
