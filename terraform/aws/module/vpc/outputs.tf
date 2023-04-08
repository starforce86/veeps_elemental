output "vpc_id" {
  value = aws_vpc.main.id
}

output "nat_ip_addresses" {
  value = aws_eip.nat_eip.*.public_ip
}

output "app_subnets_cidr_block" {
  value = local.app_subnets_cidr_block
}

output "app_subnets_ids" {
  value = aws_subnet.app_subnets.*.id
}

output "public_subnets_cidr_block" {
  value = local.public_subnets_cidr_block
}

output "public_subnets_ids" {
  value = aws_subnet.public_subnets.*.id
}