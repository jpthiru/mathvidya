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
# ALB Outputs - COMMENTED OUT (ALB disabled to save costs)
# -----------------------------------------------------------------------------
# output "alb_dns_name" {
#   description = "DNS name of the Application Load Balancer"
#   value       = aws_lb.main.dns_name
# }

# output "alb_zone_id" {
#   description = "Zone ID of the Application Load Balancer"
#   value       = aws_lb.main.zone_id
# }

# output "target_group_arn" {
#   description = "ARN of the target group"
#   value       = aws_lb_target_group.app.arn
# }

# -----------------------------------------------------------------------------
# ACM Certificate Outputs - COMMENTED OUT (not needed without ALB)
# -----------------------------------------------------------------------------
# output "acm_certificate_arn" {
#   description = "ARN of the ACM certificate"
#   value       = aws_acm_certificate.main.arn
# }

# output "acm_certificate_validation_records" {
#   description = "DNS records needed for ACM certificate validation - ADD THESE TO GODADDY"
#   value = {
#     for dvo in aws_acm_certificate.main.domain_validation_options : dvo.domain_name => {
#       name  = dvo.resource_record_name
#       type  = dvo.resource_record_type
#       value = dvo.resource_record_value
#     }
#   }
# }

# -----------------------------------------------------------------------------
# Connection Information
# -----------------------------------------------------------------------------
output "ssh_command" {
  description = "SSH command to connect to the instance (only from allowed IPs)"
  value       = "ssh -i ~/.ssh/mathvidya-key ec2-user@${aws_eip.app.public_ip}"
}

output "application_url" {
  description = "URL to access the application (HTTP - no SSL without ALB)"
  value       = "http://${aws_eip.app.public_ip}"
}

output "godaddy_dns_records" {
  description = "DNS records to create in GoDaddy for direct EC2 access"
  value       = <<-EOT

    =====================================================
    GODADDY DNS CONFIGURATION (DIRECT EC2 - NO ALB)
    =====================================================

    ADD A RECORD POINTING TO EC2 ELASTIC IP:

       Type: A
       Name: @
       Value: ${aws_eip.app.public_ip}
       TTL: 600

       Type: A
       Name: www
       Value: ${aws_eip.app.public_ip}
       TTL: 600

    NOTE: Without ALB, there is no HTTPS/SSL.
    For HTTPS, you can later:
    - Enable ALB (uncomment in main.tf)
    - Or install Let's Encrypt on EC2 directly

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
    DEPLOYMENT SUCCESSFUL! (Direct EC2 Mode)
    ============================================

    ARCHITECTURE:
    - EC2 directly accessible on HTTP (port 80)
    - No ALB (cost savings)
    - No HTTPS (add Let's Encrypt later if needed)

    STEP 1: CONFIGURE DNS IN GODADDY
    ---------------------------------
    Add A records pointing to EC2 Elastic IP:

       Type: A
       Name: @
       Value: ${aws_eip.app.public_ip}

       Type: A
       Name: www
       Value: ${aws_eip.app.public_ip}

    STEP 2: SSH INTO INSTANCE
    --------------------------
    ssh -i ~/.ssh/mathvidya-key ec2-user@${aws_eip.app.public_ip}

    STEP 3: DEPLOY APPLICATION
    ---------------------------
    cd /opt/mathvidya
    git clone <your-repo-url> .
    docker-compose -f docker-compose.prod.yml up -d

    STEP 4: VERIFY
    ---------------
    curl http://${aws_eip.app.public_ip}/health
    curl http://${var.domain_name}/health  (after DNS propagates)

    ============================================
    SECURITY NOTES:
    - EC2 SSH: Only from ${join(", ", var.ssh_allowed_cidrs)}
    - Web traffic: HTTP on port 80 (no SSL)
    - For HTTPS: Enable ALB or install Let's Encrypt
    ============================================
  EOT
}
