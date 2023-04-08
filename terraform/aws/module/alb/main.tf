resource "aws_alb" "alb" {
  name               = var.alb_name
  load_balancer_type = "application"
  subnets            = var.public_subnets
  security_groups    = [aws_security_group.alb_sg.id]
}

resource "aws_security_group" "alb_sg" {
  description = "Allow HTTP 80 TCP and HTTPS 443 TCP incoming to the ALB. Allow any outgoing traffic."

  vpc_id = var.vpc_id

  ingress {
    description = "Allow incoming HTTP 80 TCP from anywhere (public Internet) to the ALB."
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = var.cidr_blocks
  }

  ingress {
    description = "Allow incoming HTTPS 443 TCP from anywhere (public Internet) to the ALB."
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = var.cidr_blocks
  }

  egress {
    description = "Allow any/all outgoing traffic from the ALB (including to the public Internet)."
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    #tfsec:ignore:AWS009
    cidr_blocks = ["0.0.0.0/0"]
  }
}