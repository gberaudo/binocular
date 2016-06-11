# Binocular: continuously deliver demos

## Introduction

[Binocular](https://github.com/gberaudo/binocular) is a webhook service for
github and alike to automatically create demos of your commits.

An instance of binocular is deployed on the development server and handles a
single github repository.

Reviewers get access to a running instance where they can visualize and experiment.
Managers, clients can check the changes and quicly compare versions.

## Features

- Receive repository events posted by github;
- Clone public and private repositories using deploy keys;
- Usable with or without Docker;
- Display the list of builds per branch with their status/log and link to demo;
- Statically serve demos.

## Features to investigate

- Attach [status](https://developer.github.com/v3/repos/statuses/) to commit in github;
- Update PR thread with comments containing a link to deployed demo.

# Security

- The user should keep in mind arbitrary code may be executed if used without care.

# Requirements

- Python3, pyvenv


# License

- AGPLv3

# Howto

- Fork and clone this repository;
- Copy config.ini.example to config.ini and adapt to your project;
- Copy configurations/helloworld to configurations/your\_project and update symlink with rm config; ln -s configurations/your\_project config;
- Call `make run` and follow instructions;
- Implement the build hook;
- Call `make run` to launch the Binocular server.

The Binocular server listens on port 8080.
