forwarding_rules = {
  service_a = {
    path          = "/service-a*"
    priority      = 100
    target_port   = 8080
    health_path   = "/service-a/health"
    response_code = "200"
  },
  service_b = {
    path          = "/api/b*"
    priority      = 200
    target_port   = 8081
    health_path   = "/api/b/health"
    response_code = "200"
  },
  service_c = {
    path          = "/app/c*"
    priority      = 300
    target_port   = 8082
    health_path   = "/app/c/healthz"
    response_code = "200-299"
  }
}