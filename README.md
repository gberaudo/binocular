# Binocular: continuously deliver demos

## Introduction

[Binocular](https://github.com/gberaudo/binocular) is a self-hosted webhook to
automatically create demos of your commits.

During a pull request it provides an immediately running instance to reviewers
helping visualize and experiment with the changes. In addition, it fosters
communication between the technical team and the others (management, client...).

For master or a feature branch it allows quickly checking the state of the work.

## Principle

- On repository activity github posts an HTTP request to the Binocular server;
- If authorized, the Binocular server clone the repository and then start a
  build of the specified commit.

## Features

- Private repositories using deploy keys;

## Limitations

- The URL to the delivered demo is no made available on github;

# Security

- Keep in mind arbitrary code execution may be triggered on the Binouclar server.

# Procedure

- Fork and clone this repository;
- Call `make run` and follow instructions;
- Implement the build hook;
- Call `make run` to launch the Binocular server.

The Binocular server listens on port 8080.
