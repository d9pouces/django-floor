#!/usr/bin/env bash
{{ processes.django.command_line }} collectstatic --noinput
