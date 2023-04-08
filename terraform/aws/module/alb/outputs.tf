output "alb_arn" {
  value = aws_alb.alb.arn
}

output "alb_sg_id" {
  value = aws_security_group.alb_sg.id
}

output "alb_aws_url" {
  value = aws_alb.alb.dns_name
}
