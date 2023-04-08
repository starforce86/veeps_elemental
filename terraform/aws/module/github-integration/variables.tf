variable "thumbprint" {
  description = "Github Thumbprint"
  type    = string
}

variable "repos" {
  description = "Map of Github Organization, Repo, and ref (org/repo/*)"
  type    = map
}
