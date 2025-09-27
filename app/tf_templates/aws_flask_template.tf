# EC2-based Terraform template for __TF_NAME__
provider "aws" {
  region = var.aws_region
}

resource "aws_iam_role" "instance_role" {
  name = "__TF_NAME__-instance-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ssm_attach" {
  role       = aws_iam_role.instance_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "instance_profile" {
  name = "__TF_NAME__-instance-profile"
  role = aws_iam_role.instance_role.name
}
resource "aws_instance" "app" {
  ami           = var.ami_id
  instance_type = var.instance_type
  tags = { Name = "__TF_NAME__-instance" }
  iam_instance_profile = aws_iam_instance_profile.instance_profile.name
  associate_public_ip_address = true
  user_data = <<-EOF
    #!/bin/bash
    set -e
    # Amazon Linux 2: ensure agent running
    if command -v systemctl >/dev/null 2>&1; then
      systemctl enable amazon-ssm-agent || true
      systemctl start amazon-ssm-agent || true
    else
      # Ubuntu example (install)
      snap install amazon-ssm-agent --classic || true
      systemctl enable amazon-ssm-agent || true
      systemctl start amazon-ssm-agent || true
    fi
    sudo yum update -y || true
    sudo yum install git -y
    # attempt to run container if provided
    if [ -n "${var.container_image}" ] && [ "${var.container_image}" != "" ]; then
      docker run -d -p __PORT__:__PORT__ --restart unless-stopped --name __TF_NAME__ $${var.container_image}
      exit 0
    fi
    # try to clone & run repo
    if [ -n "${var.repo_url}" ] && [ "${var.repo_url}" != "" ]; then
      cd /home/ec2-user
      git clone "${var.repo_url}" __TF_NAME__ || true
      cd __TF_NAME__
      if [ -f main.py ]; then
        nohup python3 main.py &>/dev/null &
        exit 0
      elif [ -f app.py ]; then
        nohup python3 app.py &>/dev/null &
        exit 0
      fi
    fi
    # fallback simple HTTP responder
    cat > /home/ec2-user/health.py <<PY
    from http.server import HTTPServer, SimpleHTTPRequestHandler
    class Handler(SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type','text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
    HTTPServer(('0.0.0.0', __PORT__), Handler).serve_forever()
    PY
    nohup python3 /home/ec2-user/health.py &>/dev/null &
  EOF
}

output "instance_public_ip" {
  value       = aws_instance.app.public_ip
  description = "Public IP of the EC2 instance"
}

variable "aws_region" { default = "us-east-1" }
variable "ami_id" { default = "ami-0c02fb55956c7d316" }
variable "instance_type" { default = "t3.micro" }
variable "repo_url" { default = "" }
variable "container_image" { default = "" }
variable "service_port" { default = __PORT__ }