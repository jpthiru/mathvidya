# =============================================================================
# Mathvidya Infrastructure - Outputs
# =============================================================================

# -----------------------------------------------------------------------------
# VPC Outputs
# -----------------------------------------------------------------------------
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "IDs of public subnets"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "IDs of private subnets"
  value       = aws_subnet.private[*].id
}

# -----------------------------------------------------------------------------
# EC2 Outputs
# -----------------------------------------------------------------------------
output "ec2_instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.app.id
}

output "ec2_public_ip" {
  description = "Elastic IP address of the EC2 instance"
  value       = aws_eip.app.public_ip
}

output "ec2_public_dns" {
  description = "Public DNS name of the EC2 instance"
  value       = aws_eip.app.public_dns
}

# -----------------------------------------------------------------------------
# S3 Outputs
# -----------------------------------------------------------------------------
output "s3_media_bucket" {
  description = "Name of the S3 media bucket"
  value       = aws_s3_bucket.media.bucket
}

output "s3_media_bucket_arn" {
  description = "ARN of the S3 media bucket"
  value       = aws_s3_bucket.media.arn
}

output "s3_backups_bucket" {
  description = "Name of the S3 backups bucket"
  value       = aws_s3_bucket.backups.bucket
}

# -----------------------------------------------------------------------------
# Security Group Outputs
# -----------------------------------------------------------------------------
output "web_security_group_id" {
  description = "ID of the web security group"
  value       = aws_security_group.web.id
}

output "app_security_group_id" {
  description = "ID of the application security group"
  value       = aws_security_group.app.id
}

output "db_security_group_id" {
  description = "ID of the database security group"
  value       = aws_security_group.db.id
}

# -----------------------------------------------------------------------------
# CloudWatch Outputs
# -----------------------------------------------------------------------------
output "cloudwatch_log_group" {
  description = "Name of the CloudWatch log group"
  value       = aws_cloudwatch_log_group.app.name
}

# -----------------------------------------------------------------------------
# ALB Outputs
# -----------------------------------------------------------------------------
output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the Application Load Balancer"
  value       = aws_lb.main.zone_id
}

output "target_group_arn" {
  description = "ARN of the target group"
  value       = aws_lb_target_group.app.arn
}

# -----------------------------------------------------------------------------
# ACM Certificate Outputs
# -----------------------------------------------------------------------------
output "acm_certificate_arn" {
  description = "ARN of the ACM certificate"
  value       = aws_acm_certificate.main.arn
}

output "acm_certificate_validation_records" {
  description = "DNS records needed for ACM certificate validation - ADD THESE TO GODADDY"
  value = {
    for dvo in aws_acm_certificate.main.domain_validation_options : dvo.domain_name => {
      name  = dvo.resource_record_name
      type  = dvo.resource_record_type
      value = dvo.resource_record_value
    }
  }
}

# -----------------------------------------------------------------------------
# Connection Information
# -----------------------------------------------------------------------------
output "ssh_command" {
  description = "SSH command to connect to the instance (only from allowed IPs)"
  value       = "ssh -i ~/.ssh/mathvidya-key ec2-user@${aws_eip.app.public_ip}"
}

output "application_url" {
  description = "URL to access the application"
  value       = "https://${var.domain_name}"
}

output "godaddy_dns_records" {
  description = "DNS records to create in GoDaddy"
  value       = <<-EOT

    =====================================================
    GODADDY DNS CONFIGURATION
    =====================================================

    1. ADD CNAME RECORD FOR ALB (instead of A record):

       Type: CNAME
       Name: @
       Value: ${aws_lb.main.dns_name}
       TTL: 600

       Type: CNAME
       Name: www
       Value: ${aws_lb.main.dns_name}
       TTL: 600

       NOTE: GoDaddy may not allow CNAME for root domain (@).
       If so, use their "Forwarding" feature or consider
       moving DNS to Route 53 or CloudFlare.

       ALTERNATIVE - Use A record with ALB IP (not recommended
       as ALB IPs can change):
       - Get ALB IPs: nslookup ${aws_lb.main.dns_name}

    2. ADD CNAME RECORDS FOR SSL CERTIFICATE VALIDATION:
       (Check acm_certificate_validation_records output)

    =====================================================
  EOT
}

# -----------------------------------------------------------------------------
# Next Steps
# -----------------------------------------------------------------------------
output "next_steps" {
  description = "Next steps after deployment"
  value       = <<-EOT

    ============================================
    DEPLOYMENT SUCCESSFUL!
    ============================================

    ARCHITECTURE:
    - ALB handles HTTPS (SSL via ACM - free)
    - EC2 only accessible via SSH (from your IP) and ALB
    - No direct HTTP/HTTPS access to EC2

    STEP 1: VALIDATE SSL CERTIFICATE (REQUIRED FIRST!)
    ---------------------------------------------------
    Add these CNAME records in GoDaddy for ACM validation:
    (Run: terraform output acm_certificate_validation_records)

    STEP 2: CONFIGURE DNS IN GODADDY
    ---------------------------------
    Option A (Recommended - use ANAME/ALIAS if supported):
       Type: ANAME/ALIAS
       Name: @
       Value: ${aws_lb.main.dns_name}

    Option B (For www subdomain):
       Type: CNAME
       Name: www
       Value: ${aws_lb.main.dns_name}

    Option C (If ANAME not supported - use forwarding):
       Forward mathvidya.com to www.mathvidya.com
       Then CNAME www -> ${aws_lb.main.dns_name}

    STEP 3: SSH INTO INSTANCE
    --------------------------
    ssh -i ~/.ssh/mathvidya-key ec2-user@${aws_eip.app.public_ip}

    STEP 4: DEPLOY APPLICATION
    ---------------------------
    cd /opt/mathvidya
    git clone <your-repo-url> .
    docker-compose -f docker-compose.yml up -d

    STEP 5: VERIFY
    ---------------
    curl https://${var.domain_name}/health

    ============================================
    SECURITY NOTES:
    - EC2 SSH: Only from ${join(", ", var.ssh_allowed_cidrs)}
    - Web traffic: Only through ALB
    - SSL: Handled by ALB (ACM certificate)
    ============================================
  EOT
}
