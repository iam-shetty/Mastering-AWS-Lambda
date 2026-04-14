
terraform {
  required_version = ">= 1.4"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  alias  = "primary"
  region = "ap-south-1"
}

provider "aws" {
  alias  = "dr"
  region = "us-east-1"
}

provider "aws" {
  alias  = "neutral"
  region = "ap-southeast-2"
}