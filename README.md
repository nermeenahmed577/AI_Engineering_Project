# AI Engineering Project

## Project Overview

This repository contains the implementation of an AI Engineering course project.

The project focuses on deploying and evaluating Large Language Models (LLMs), profiling hardware performance, and building automated evaluation pipelines.

## Milestone 1 — Local Model Inference & Hardware Profiler

**Objective:** Deploy an open-source 7B language model and measure its inference performance.

**Model:** Mistral-7B-Instruct-v0.3

**Environment:** Google Colab with GPU acceleration.

### Performance Metrics

- Time To First Token (TTFT)
- Inter-token Generation Latency
- GPU VRAM Usage

### Context Lengths

- 1,024 tokens
- 2,048 tokens
- 4,096 tokens
- 8,192 tokens

### Implementation

The profiling implementation is available in:

`Milestone_1/milestone1_hardware_profiler.ipynb`

## Milestone 2 — Automated Regression Evaluation Suite

**Objective:** Build an automated evaluation pipeline to measure the quality and correctness of model responses.

Planned components:

- 30+ Golden Test Cases
- Programmatic Assertion Validators
- LLM-as-a-Judge Scoring Rubric
- Judge Calibration
- Automated Pass/Fail Reporting
- CI/CD Integration

## Technologies Used

- Python
- PyTorch
- Hugging Face Transformers
- BitsAndBytes
- Google Colab
- GitHub

## Project Status

- [x] Milestone 1 — Hardware Profiling
- [x] Milestone 2 — Automated Evaluation Suite
