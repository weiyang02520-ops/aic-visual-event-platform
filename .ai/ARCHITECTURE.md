# Architecture

User → ChatGPT Master → GitHub .ai/task → Codex Worker → branch/tests/PR/report → GitHub → Master review.

Product flow: Video Source → FrameProvider/Pipeline → Detector/Pose Provider → Tracker → Normalized Observations → RelationEngine → Primitive Facts → Enabled Scene Plugins → Temporal Reasoners → UnifiedEvent + EvidenceRef → SQLite/REST → Frontend.

Boundaries: .ai controls automation; agent-state stores deep history/evidence. Makerverse is business backend; livestream-rs is media/archive foundation. AI does not duplicate video archive. Model providers are replaceable adapters. Plugins consume normalized facts. Robot is future landing, not current control scope.
