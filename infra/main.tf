provider "aws" {
  region = "eu-central-1"
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
          AWS = [
            aws_iam_role.ec2_role.arn,
            data.aws_caller_identity.current.arn
          ]
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

resource "aws_iam_policy" "ec2_s3_write_policy" {
  name        = "ec2-s3-write-policy"
  description = "Allow EC2 to read and write to the devlaunch S3 bucket"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket"
        ],
        Resource = [
          aws_s3_bucket.templates_bucket.arn,
          "${aws_s3_bucket.templates_bucket.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_s3_write_policy" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = aws_iam_policy.ec2_s3_write_policy.arn
}

#resource "aws_iam_role_policy_attachment" "attach_s3_policy" {
#  role       = aws_iam_role.ec2_role.name
#  policy_arn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
#}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "devlaunch-ec2-profile"
  role = aws_iam_role.ec2_role.name
}

data "aws_vpc" "default" {
  default = true
}

resource "aws_security_group" "ec2_ssh" {
  name        = "devlaunch-ec2-ssh"
  description = "Allow SSH access"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "devlaunch-ssh"
  }
}

resource "aws_instance" "api_instance" {
  ami                    = "ami-02003f9f0fde924ea"
  instance_type          = "t2.micro"
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name
  key_name               = "devops-key-eu-central"
  vpc_security_group_ids = [aws_security_group.ec2_ssh.id]

  tags = {
    Name = "devlaunch-api"
  }
}


output "bucket_name" {
  value = aws_s3_bucket.templates_bucket.bucket
}

output "ec2_public_ip" {
  value = aws_instance.api_instance.public_ip
}
