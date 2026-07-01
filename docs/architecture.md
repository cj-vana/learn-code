# Architecture

Web calls only `/api/v1`. CLI is HTTP-only for learner actions. API is the only SQLite writer. API calls runner-broker. Only runner-broker mounts `/var/run/docker.sock`. `python-runner` is a build-only image for short-lived execution containers.
