// WebSecurityConfigBase.java
package gov.nasa.freddie.freddieutils.config;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;
import org.springframework.core.env.Environment;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.oauth2.jwt.JwtDecoder;
import org.springframework.security.oauth2.jwt.NimbusJwtDecoder;
import org.springframework.security.provisioning.InMemoryUserDetailsManager;
import org.springframework.security.web.util.matcher.AntPathRequestMatcher;

import java.security.interfaces.RSAPublicKey;

@Configuration
@EnableWebSecurity
public class WebSecurityConfigBase {
    private static final Logger logger = LoggerFactory.getLogger(WebSecurityConfigBase.class);

    @Value("${actuator.username:admin}")  // Default value: admin
    private String actuatorUsername;

    @Value("${actuator.password:changeMe}")  // Default value: changeMe
    private String actuatorPassword;

    @Value("${spring.security.oauth2.resourceserver.jwt.key-value:#{null}}")
    private RSAPublicKey key;

    protected void configureHttpSecurity(HttpSecurity http) throws Exception {
        http.csrf(AbstractHttpConfigurer::disable)
                // Don't authenticate for these particular endpoints
                .authorizeHttpRequests((requests) -> requests.requestMatchers(
                        new AntPathRequestMatcher("/actuator/health"),
                        new AntPathRequestMatcher("/actuator/info")).permitAll())
                // These endpoints need to be authenticated
                .authorizeHttpRequests((requests) -> requests.requestMatchers(
                        new AntPathRequestMatcher("/actuator/**", HttpMethod.GET.toString())).authenticated());

        http.httpBasic();
    }

    @Bean
    public UserDetailsService userDetailsService() {
        UserDetails user = User.builder()
                .username(actuatorUsername)
                .password(passwordEncoder().encode(actuatorPassword))
                .roles("ACTUATOR")
                .build();

        return new InMemoryUserDetailsManager(user);
    }

    @Bean
    @Primary
    public BCryptPasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    @Bean
    protected JwtDecoder jwtDecoder() {
        if (key == null) {
            return null;
        }
        return NimbusJwtDecoder.withPublicKey(this.key).build();
    }
}

// ActuatorSecurityConfig.java
package gov.nasa.freddie.freddieutils.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.core.annotation.Order;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.context.annotation.Bean;

@Configuration
@EnableWebSecurity
@Order(1)
public class ActuatorSecurityConfig extends WebSecurityConfigBase {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        super.configureHttpSecurity(http);
        return http.build();
    }
}