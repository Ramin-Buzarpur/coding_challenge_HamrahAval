# Cluster API Client

A reliable client module for managing group objects across multiple cluster nodes.

## Overview

This project implements a client that communicates with multiple REST API nodes and maintains consistency during create and delete operations.

The client handles:
- concurrent API requests
- transient failures
- rollback operations
- error handling