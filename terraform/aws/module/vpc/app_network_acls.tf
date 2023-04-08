resource "aws_network_acl" "app" {
  vpc_id = aws_vpc.main.id

  subnet_ids = [
    for subnet in aws_subnet.app_subnets :
    subnet.id
  ]
}

##########
## INGRESS
##########

# Allow http traffic coming in from vpc
resource "aws_network_acl_rule" "vpc_to_app_http_ingress_allow" {
  network_acl_id = aws_network_acl.app.id
  rule_number    = 100
  egress         = false
  protocol       = "tcp"
  rule_action    = "allow"
  cidr_block     = var.vpc_cidr_block
  from_port      = 80
  to_port        = 80
}

# Allow https traffic coming in from vpc
resource "aws_network_acl_rule" "vpc_to_app_https_ingress_allow" {
  network_acl_id = aws_network_acl.app.id
  rule_number    = 200
  egress         = false
  protocol       = "tcp"
  rule_action    = "allow"
  cidr_block     = var.vpc_cidr_block
  from_port      = 443
  to_port        = 443
}

# So traffic can return back to the subnet
resource "aws_network_acl_rule" "all_to_app_ephemeral_egress_allow" {
  network_acl_id = aws_network_acl.app.id
  rule_number    = 400
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

# Allow http outbound traffic
resource "aws_network_acl_rule" "app_to_all_http_egress_allow" {
  network_acl_id = aws_network_acl.app.id
  rule_number    = 100
  egress         = true
  protocol       = "tcp"
  rule_action    = "allow"
  cidr_block     = "0.0.0.0/0"
  from_port      = 80
  to_port        = 80
}

# Allow https outbound traffic
resource "aws_network_acl_rule" "app_to_all_https_egress_allow" {
  network_acl_id = aws_network_acl.app.id
  rule_number    = 200
  egress         = true
  protocol       = "tcp"
  rule_action    = "allow"
  cidr_block     = "0.0.0.0/0"
  from_port      = 443
  to_port        = 443
}

# So traffic can happen when coming into app tier
resource "aws_network_acl_rule" "app_to_all_ephemeral_egress_allow" {
  network_acl_id = aws_network_acl.app.id
  rule_number    = 300
  egress         = true
  protocol       = "tcp"
  rule_action    = "allow"
  cidr_block     = "0.0.0.0/0"
  from_port      = 1024
  to_port        = 65535
}
