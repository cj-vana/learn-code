"""Thin HTTP-only client for the Learn Code API.

Every learner action (status, next, run, submit, playground, quiz, progress,
review) is a call to the Task 5 FastAPI backend over httpx. The CLI never opens
the progress database and never executes learner code. The only local actions
are ``validate-content`` (the repo content validator) and ``up`` (docker
compose).
"""
