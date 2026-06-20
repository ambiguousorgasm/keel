#!/usr/bin/env python3
"""Run all KEEL gate-simulator experiments and print the results tables."""
from sim.experiments import run_all

if __name__ == "__main__":
    print(run_all())
