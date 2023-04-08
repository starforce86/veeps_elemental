resource "aws_network_acl" "public" {
  vpc_id = aws_vpc.main.id

  subnet_ids = [
    for subnet in aws_subnet.public_subnets :
    subnet.id
  ]
}

##########
## INGRESS
##########

# Allow http traffic into public subnet
resource "aws_network_acl_rule" "public_http_ingress_allow" {
  network_acl_id = aws_network_acl.public.id
  rule_number    = 100
  egress         = false
  protocol       = "tcp"
  rule_action    = "allow"
  cidr_block     = "0.0.0.0/0"
  from_port      = 80
  to_port        = 80
}

# Allow https traffic into public subnet
resource "aws_network_acl_rule" "public_https_ingress_allow" {
  network_acl_id = aws_network_acl.public.id
  rule_number    = 200
  egress         = false
  protocol       = "tcp"
  rule_action    = "allow"
  cidr_block     = "0.0.0.0/0"
  from_port      = 443
  to_port        = 443
}

# Allow return ephemeral traffic from public subnet
resource "aws_network_acl_rule" "ephemeral_to_public_ingress_allow" {
  network_acl_id = aws_network_acl.public.id
  rule_number    = 300
  egress         = false
  protocol       = "tcp"
  rule_action    = "allow"
  cidr_block     = "0.0.0.0/0"
  from_port      = 1024
  to_port        = 65535
}

##########
## EGRESS
##########

# Allow outbound http traffic from public subnet to everywhere
# Since NAT gateways are in this subnet tier, it's needed
resource "aws_network_acl_rule" "public_ipv4_http_egress_allow" {
  network_acl_id = aws_network_acl.public.id
  rule_number    = 100
  egress         = true
  protocol       = "tcp"
  rule_action    = "allow"
  cidr_block     = "0.0.0.0/0"
  from_port      = 80
  to_port        = 80
}

# Allow outbound https traffic from public subnet to everywhere
# Since NAT gateways are in this subnet tier, it's needed
resource "aws_network_acl_rule" "public_ipv4_https_egress_allow" {
  network_acl_id = aws_network_acl.public.id
  rule_number    = 200
  egress         = true
  protocol       = "tcp"
  rule_action    = "allow"
  cidr_block     = "0.0.0.0/0"
  from_port      = 443
  to_port        = 443
}

# Allow ephemeral outbound traffic from public subnet
resource "aws_network_acl_rule" "ephemeral_public_egress_allow" {
  network_acl_id = aws_network_acl.public.id
  rule_number    = 300
  egress         = true
  protocol       = "tcp"
  rule_action    = "allow"
  cidr_block     = "0.0.0.0/0"
  from_port      = 1024
  to_port        = 65535
}
