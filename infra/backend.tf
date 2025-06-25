terraform {
  backend "s3" {
    bucket = "devlaunch-templates-bucket"
    key    = "terraform.tfstate"
    region = "eu-central-1"
  }
}

