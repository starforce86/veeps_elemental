#### Direct connection to s3 on your private network ####
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${var.aws_region}.s3"
  vpc_endpoint_type = "Gateway"

  policy = <<POLICY
{
  "Version": "2008-10-17",
  "Statement": [
    {
      "Action": "*",
      "Effect": "Allow",
      "Principal": "*",
      "Resource": "*"
    }
  ]
}
POLICY

  route_table_ids = flatten([
    aws_route_table.public.id,
    [
      for route_table in aws_route_table.app :
      route_table.id
    ],
  ])
}
