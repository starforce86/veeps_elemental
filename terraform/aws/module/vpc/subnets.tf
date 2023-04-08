locals {
  subnet_tier_cidrs         = cidrsubnets(var.vpc_cidr_block, var.subnet_tier_cidrs_newbits, var.subnet_tier_cidrs_newbits, var.subnet_tier_cidrs_newbits)
  public_subnets_cidr_block = local.subnet_tier_cidrs[0]
  app_subnets_cidr_block    = local.subnet_tier_cidrs[1]
  db_subnets_cidr_block     = local.subnet_tier_cidrs[2]
}

resource "aws_subnet" "public_subnets" {
  count = length(var.availability_zones)

  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(local.public_subnets_cidr_block, var.public_subnets_cidr_newbits, count.index)
  availability_zone = element(var.availability_zones, count.index)

  map_public_ip_on_launch = true

}

resource "aws_subnet" "app_subnets" {
  count = length(var.availability_zones)

  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(local.app_subnets_cidr_block, var.app_subnets_cidr_newbits, count.index)
  availability_zone = element(var.availability_zones, count.index)

}
