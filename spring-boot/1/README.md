Removed the @ConfigurationProperties and @PropertySource annotations 
since we're no longer using the external configuration file
Added @Value annotations to inject the actuator username and password with default values

actuator:
  username: your_username
  password: your_secure_password

java -jar your-app.jar --actuator.username=your_username --actuator.password=your_secure_password

management:
  endpoints:
    web:
      exposure:
        include: info
  endpoint:
    info:
      enabled: true
  security:
    enabled: true

spring:
  security:
    user:
      name: "${ACTUATOR_USERNAME:defaultUser}"  # Use environment variable or default
      password: "${ACTUATOR_PASSWORD:defaultPassword}" # Use environment variable or default
