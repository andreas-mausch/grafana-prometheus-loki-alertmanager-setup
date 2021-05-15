Grafana setup with

- Loki for providing logs of running docker containers  
  http://localhost:3100
- Prometheus (with cadvisor) for docker container metrics  
  http://localhost:9090/alerts
- Alertmanager for sending emails  
  http://localhost:9093/#/alerts
- Mailhog as SMTP host  
  http://localhost:8025

Link to my Blog post: https://andreas-mausch.de/blog/2021/05/14/monitoring-grafana/

# Install Loki Docker Driver

```bash
docker plugin install grafana/loki-docker-driver:main-d9380ea --alias loki --grant-all-permissions
```

# Run

```bash
docker-compose up
```

Grafana is accessible at http://localhost:3000  
The first time login is admin/admin.

# Start example logging service

```bash
docker run -it --rm --name my-service --log-driver=loki --log-opt loki-url="http://localhost:3100/loki/api/v1/push" --log-opt loki-pipeline-stages="- multiline:
           firstline: '^\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2},\\d{3}'
       " -v "$PWD":/usr/src/myapp -w /usr/src/myapp python:3 python my-service.py
```

After starting the service, you should see logs in grafana.

Stop the service, wait a few minutes, and you should see an alert email in mailhog.

# Multiline

Check the [Grafana docs](https://grafana.com/docs/loki/latest/clients/promtail/stages/multiline/) on this topic to see allowed values.

# Check alerts

Alerts are sent:
- When the *my-service* is down for more than 1 minute
- Any message is logged with the content error, failure or exception.

http://localhost:9093/#/alerts  
http://localhost:8025

# Clean up

```bash
docker-compose rm
docker volume rm grafana-prometheus-loki-alertmanager-setup_alertmanager grafana-prometheus-loki-alertmanager-setup_grafana grafana-prometheus-loki-alertmanager-setup_loki grafana-prometheus-loki-alertmanager-setup_prometheus
```

# Source link in alert e-mails is broken for loki alerts

Right, I don't know how to solve it.
I think the link displayed is the generatorURL sent to alertmanager.

And [somebody requested](https://github.com/grafana/loki/issues/3119#issuecomment-776453889)
to support the field in order to allow customized source links.

Maybe this will be fixed soon.
