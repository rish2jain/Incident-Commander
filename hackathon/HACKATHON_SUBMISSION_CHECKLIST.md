# Hackathon Submission Checklist

Refer to `docs/hackathon/README.md` for the consolidated plan. This checklist focuses on what remains before submitting to the AWS AI Agent Global Hackathon.

## Core Requirements

- [ ] **Demonstrable AWS deployment** – rerun CDK automation with guardrails, secrets, and validation.
- [x] **Reasoning LLM usage** – FastAPI agents call Bedrock Claude models locally (needs production hardening).
- [ ] **Autonomous capabilities** – implement consensus + resolution flows noted in `docs/gap_analysis.md`.
- [ ] **Integration with external tooling** – finish Datadog, PagerDuty, Slack secret population prior to go-live.

## Submission Materials

- [ ] `HACKATHON_SUBMISSION_PACKAGE.md` updated with truthful deployment status and metrics.
- [ ] 3-minute demo video recorded after new features are complete.
- [ ] Architecture diagram refreshed once missing capabilities land.
- [ ] DevPost form populated with verified links and statistics.

## Build & Validation Tasks

1. Close feature gaps (guardrails, model routing, 3D viz, chaos tests).
2. Run `python run_comprehensive_tests.py` and add chaos/Byzantine coverage.
3. Execute a staging deployment dry run and capture health metrics.
4. Update demo assets (`DEMO_VIDEO_SCRIPT.md`, screenshots, metrics overlay).

## Final Submission Steps

```bash
# After feature + deployment work
python deploy_to_aws.py --environment production
python validate_hackathon_deployment.py

# Prepare materials
python record_demo_video.py  # optional helper

# Submit
# 1. Upload video (YouTube, unlisted/public)
# 2. Complete DevPost form with updated data
```

Keep this checklist in sync with the primary hackathon overview document.

**🏆 YOU'RE ALMOST THERE! Just AWS credentials + demo video + DevPost submission = DONE! 🎉**
