# Binocular: continuously deliver demos

## Introduction

[Binocular](https://github.com/gberaudo/binocular) is a webhook service for
github and alike to automatically create demos of your commits.

An instance of binocular is deployed on the development server and handles a
single github repository.

Reviewers get access to a running instance where they can visualize and experiment.
Managers, clients can check the changes and quicly compare versions.

## Principle

- Github posts an HTTP request to the Binocular server;
- If authorized, the repository is cloned and a build is triggered according to customizable scripts:
- The build log and demo are made avaiable.

## Features

- Work with private repositories using deploy keys;
- No dependency on Docker.

## Limitations

- The URL to the demo and build status are not made available on github;

# Security

- The user should keep in mind arbitrary code may be executed if used without care.

# Requirements

- Python3, pyvenv


# License

- AGPLv3

# Howto

- Fork and clone this repository;
- Call `make run` and follow instructions;
- Implement the build hook;
- Call `make run` to launch the Binocular server.

The Binocular server listens on port 8080.
