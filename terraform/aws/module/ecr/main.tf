# Create an AWS ECR (Elastic Container Repository) to store the Docker container(s)
resource "aws_ecr_repository" "ecr" {
  name                 = var.ecr_repository_name
  image_tag_mutability = "MUTABLE"
  image_scanning_configuration {
    scan_on_push = true
  }
}

# Keep the last 16 images, adjust to meet your needs. 
# Keep too many, and you get false alarms in Security Hub
# Keep too few, and you won't be able to deploy an old version if needed
resource "aws_ecr_lifecycle_policy" "only_keep_last_16_images" {
  repository = aws_ecr_repository.ecr.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Only keep last 16 images in ECR."
      action = {
        type = "expire"
      }
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 16
      }
    }]
  })
}