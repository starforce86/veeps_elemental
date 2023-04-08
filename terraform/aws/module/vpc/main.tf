# vpc
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr_block
  enable_dns_hostnames = true
  enable_dns_support   = true
}



resource "aws_internet_gateway" "internet_gw" {
  vpc_id = aws_vpc.main.id
}
