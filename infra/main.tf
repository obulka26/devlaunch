provider "aws" {
  region = ""
}

resource "aws_s3_bucket" "templates_bucket" {
  bucket        = "devlaunch-templates-bucket"
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "public_access" {
  bucket = aws_s3_bucket.templates_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_iam_role" "ec2_role" {
  name = "devlaunch-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Principal = {
          Service = "ec2.amazonaws.com"
        },
        Effect = "Allow",
        Sid    = ""
      }
    ]
  })
}

data "aws_caller_identity" "current" {}

resource "aws_s3_bucket_policy" "ec2_only_access" {
  bucket = aws_s3_bucket.templates_bucket.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid    = "AllowEC2RoleReadOnly"
        Effect = "Allow"
        Principal = {
          AWS = [aws_iam_role.ec2_role.arn, data.aws_caller_identity.arn]
        }
        Action = [
          "s3:GetObject",
          "s3:ListBucket",
          "s3:PutObject"
        ]
        Resource = [
          "${aws_s3_bucket.templates_bucket.arn}",
          "${aws_s3_bucket.templates_bucket.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_s3_policy" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "devlaunch-ec2-profile"
  role = aws_iam_role.ec2_role.name
}

resource "aws_instance" "api_instance" {
  ami                  = ""
  instance_type        = "t2.micro"
  iam_instance_profile = aws_iam_instance_profile.ec2_profile.name
  key_name             = var.key_name
  user_data            = file("bootstrap.sh")

  tags = {
    Name = "devlaunch-api"
  }
}

variable "key_name" {
  description = "Name of the SSH key for EC2"
}

output "bucket_name" {
  value = aws_s3_bucket.templates_bucket.bucket
}

output "ec2_public_ip" {
  value = aws_instance.api_instance.public_ip
}
