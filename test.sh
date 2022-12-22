#!/bin/bash

pytest tests --no-header --doctest-modules --junitxml=junit/test-results.xml --cov=com --cov-report=xml --cov-report=html