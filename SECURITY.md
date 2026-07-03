# Security

Learn Code is a local, single-user tool. There is no hosted service, no
accounts, and no telemetry. The security boundary that matters is the code
execution sandbox:

- Learner code runs only in short-lived containers spawned by
  `services/runner-broker` from the `python-runner` image (no network, no
  Docker socket, workspace bind-mounted per job).
- `runner-broker` is the only service that mounts the Docker socket; the web
  and API containers never touch it.
- All services publish to localhost only.

See `docs/runner-security.md` for the full model.

## Reporting a vulnerability

If you find a sandbox escape or any other security issue, please open a
[private security advisory](https://github.com/cj-vana/learn-code/security/advisories/new)
rather than a public issue. You should hear back within a week.
