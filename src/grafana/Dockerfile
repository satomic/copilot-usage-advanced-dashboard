FROM grafana/grafana-oss:11.4.0

USER root

# Install dependencies
RUN apk update && \
    apk add --no-cache libcap && \
    rm -rf /var/cache/apk/*

RUN setcap 'cap_net_bind_service=+ep' /usr/share/grafana/bin/grafana-server

# Expose the Grafana port
EXPOSE 80

# Start Grafana
CMD ["grafana-server", "--volume=grafana-storage:/var/lib/grafana"]