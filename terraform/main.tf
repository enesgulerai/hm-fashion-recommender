terraform {
    required_providers {
        aws = {
            source = "hashicorp/aws"
            version = "~> 5.0"
        }
    }
}

provider "aws" {
    region = "eu-central-1"
}

# S3 BUCKET
resource "aws_s3_bucket" "model_repo" {
    bucket = "hm-fashion-models-production-enesguler"

    # TAGGING
    tags = {
        Environment = "Production"
        Project = "Fashion-Recommender"
        ManagedBy = "Terraform"
    }
}
