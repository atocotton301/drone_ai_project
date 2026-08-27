---
name: drone-ai-workflow
description: "Use when: debugging the indoor drone AI project, validating model or dataset issues, investigating Jetson/PX4/demo logic, or preparing reproducible fixes in this autonomous navigation and threat-detection workspace. Covers root-cause analysis, targeted verification, and evidence-based completion checks."
---

# Drone AI Workflow

This skill standardizes how to work inside this repository for debugging, validation, feature work, and release-quality checks. It is designed for the indoor autonomous drone AI system described in the project README, especially scenarios involving object detection, tactical analysis, SLAM, dashboard simulation, and Jetson/PX4 integration.

## Goals

- Investigate the actual root cause before changing code
- Keep changes minimal and traceable
- Validate with the smallest relevant command or test
- Produce evidence that the fix or feature works
- Keep the work aligned with the project’s mission: offline, edge-based, indoor drone autonomy under 3-OFF constraints

## Workflow

### 1. Understand the project context

Before changing code, read the relevant project context:
- The repository overview in the root README
- The specific module or script related to the issue
- The related tests, config files, and dataset structures

Decision point:
- If the issue is in model behavior, check dataset, config, and training artifacts first
- If the issue is in logic or dashboard behavior, inspect the relevant Python module and any demo code
- If the issue is in hardware or PX4/Jetson flow, review integration scripts and safety logic before patching

### 2. Reproduce the problem

Use the smallest available reproduction:
- Run the related script or test
- Re-create the bug with a focused command or input sample
- Capture the exact error, stack trace, or incorrect behavior

Quality bar:
- The failure mode is observed before the fix
- The result is specific enough to guide the root-cause investigation

### 3. Trace to the root cause

Follow the data flow to the failure point:
- Identify the function, class, or config that produces the incorrect output
- Check whether the problem is caused by a dataset issue, model mismatch, dependency problem, logic bug, or environment/setup drift
- Compare with similar working examples in the repository when available

Decision point:
- If the problem is a dependency/environment mismatch, confirm the interpreter and package setup
- If the problem is logic, inspect the control flow and relevant assumptions
- If the problem is training or inference quality, validate the input data and labels before adjusting code

### 4. Apply the minimal fix

Keep the patch narrow and aligned with the actual cause:
- Prefer one root-cause fix over broad refactoring
- Avoid unrelated cleanup during a bug fix
- Keep naming, structure, and comments consistent with the surrounding code

Quality bar:
- The patch addresses the root cause only
- No unrelated behavior is changed

### 5. Validate with evidence

After the patch, run the smallest command that checks the changed behavior:
- A targeted unit or integration test
- A representative script execution
- A quick smoke check for the affected workflow

Acceptance conditions:
- The relevant test or command passes
- The original symptom is no longer reproduced
- The result is recorded in the output or terminal evidence

### 6. Check for regression risk

Before concluding work:
- Review adjacent code paths that may be affected
- Confirm the fix does not break the command or expected project flow
- If the change touches configuration or model behavior, verify the related inputs still match expected formats

## Decision Tree

### If it is a data issue
- Inspect dataset structure, labels, and YAML config
- Confirm class names, image paths, and annotation formats
- Run the relevant validation script or dataset checker before changing logic

### If it is a model issue
- Review training config, weights, and inference path
- Check whether the model is being loaded with the expected input size, classes, or output format
- Verify the issue by reproducing with a small sample input

### If it is a logic issue
- Read the function responsible for the output
- Trace the data values through the function boundary
- Confirm assumptions against the project domain and the expected behavior

### If it is an environment issue
- Check the interpreter, installed packages, and project configuration
- Ensure the active environment matches the repo requirements
- Reproduce under the expected runtime, not a mismatched shell environment

## Completion Checklist

Use this checklist before marking an issue resolved:

- [ ] The root cause was identified and not merely guessed
- [ ] The fix is minimal and directly related to the cause
- [ ] The relevant validation command was run
- [ ] The output confirms the expected behavior
- [ ] No obviously related regression was introduced
- [ ] The result is documented clearly enough for the next person to continue

## Project-Specific Guidance

This repository is organized around multiple subsystems, so keep the scope explicit:

- `datasets/`: dataset management and label validation
- `scripts/`: data conversion, validation, and benchmarking utilities
- `configs/`: class mappings and model configuration
- `demo/`: simulation dashboard and tactical logic
- `jetson/`: edge inference and on-device execution
- `mapping/`: SLAM and spatial overlay logic
- `px4/`: hardware and flight-control integration guidance
- `tests/`: local verification scripts

When adjusting code, align with the repository’s overall objective:
- offline operation
- indoor autonomy
- edge AI inference
- safety-oriented flight logic
- tactical threat detection and disaster-response awareness

## Writing Style for AI Collaboration

When working on this project with an AI assistant or automation agent:

- Prefer concise, evidence-based language
- State what was reproduced, what was changed, and what was verified
- Keep prompts actionable and tied to the affected subsystem
- Avoid broad rewrites unless the root cause requires them
- When uncertainty remains, state the missing fact and the next check needed

## Example Trigger Prompts

- "Investigate why the dataset validation is failing in this workspace."
- "Debug the inference flow in the demo dashboard and confirm the issue with a targeted run."
- "Find the cause of the label mismatch in the custom training setup and fix it with minimal changes."
- "Review the Jetson/PX4 integration path and identify the risk in the current failsafe logic."
- "Validate the project’s Python environment and check for setup drift before changing the code."

## Related Customizations

Potential next customizations for this repository:
- A project-specific validation prompt for dataset and model checks
- A testing workflow skill for inference and dashboard smoke tests
- A Jetson deployment skill for edge runtime validation
- A safety review skill for PX4 and failsafe logic
