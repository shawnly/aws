import gov.nasa.freddie.freddieutils.OkHttpUtils;
import okhttp3.Response;
import okhttp3.ResponseBody;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;
import org.springframework.context.annotation.PropertySource;
import org.springframework.context.support.PropertySourcesPlaceholderConfigurer;
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

import java.io.IOException;
import java.security.interfaces.RSAPublicKey;

@Configuration
@EnableWebSecurity
@ConfigurationProperties(prefix = "actuator")
@PropertySource("classpath:config/application-actuator-default.yml")
public class WebSecurityConfigBase {
    private static final Logger logger = LoggerFactory.getLogger(WebSecurityConfigBase.class);

    @Value("${actuator.username}")
    private String actuatorUsername;

    @Value("${actuator.password}")
    private String actuatorPassword;

    @Value("${spring.security.oauth2.resourceserver.jwt.key-value:${public-key.security.oauth2.resourceserver.jwt.key-value:#{null}}}")
    private RSAPublicKey key;

    protected void configureHttpSecurity(HttpSecurity http) throws Exception {
        http.csrf(AbstractHttpConfigurer::disable)
                // Don't authenticate for these particular endpoints...
                .authorizeHttpRequests((requests) -> requests.requestMatchers(
                        new AntPathRequestMatcher("/actuator/health"),
                        new AntPathRequestMatcher("/actuator/info")).permitAll())
                // These endpoints need to be authenticated...
                .authorizeHttpRequests((requests) -> requests.requestMatchers(
                        new AntPathRequestMatcher("/actuator/**", HttpMethod.GET.toString())).authenticated());

        http.httpBasic();
    }

    @Bean
    public UserDetailsService userDetailsService() {
        UserDetails user = User.builder()
                .username(actuatorUsername)
                .password(passwordEncoder().encode(actuatorPassword))
                .roles("ACTUATOR")  // Added roles for better security
                .build();

        return new InMemoryUserDetailsManager(user);
    }

    @Bean
    @Primary
    public BCryptPasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    @Bean
    public static PropertySourcesPlaceholderConfigurer propertyPlaceholderConfigurer() {
        return new PropertySourcesPlaceholderConfigurer();
    }

    @Bean
    protected JwtDecoder jwtDecoder() {
        if (key == null) {
            return null;
        }
        return NimbusJwtDecoder.withPublicKey(this.key).build();
    }

    protected JwtDecoder createJwtDecoder(String jwksUri) {
        if (jwksUri.isEmpty()) {
            return jwtDecoder();
        }

        logger.info("Using JwksUri - {}", jwksUri);
        try (Response response = OkHttpUtils.get(jwksUri)) {
            if (!response.isSuccessful()) {
                ResponseBody responseBody = response.body();
                logger.error("Error accessing the JWKS URI {} with response code {} and body {}",
                        jwksUri, response.code(), (responseBody != null) ? responseBody.string() : "");
            }
        } catch (IOException ioException) {
            logger.warn("Could not access the JWKS URI: {}", jwksUri, ioException);
        }

        return NimbusJwtDecoder.withJwkSetUri(jwksUri).build();
    }
}