# Speak Runtime Contract

`speak` is a file-first speech skill.

The installed adapter should call mega-orchestrator tool `speak_generate` with:

- `text`: required source text to read aloud
- `agent_family`: optional target adapter family
- `voice_id`: optional override
- `model_id`: optional override
- `output_format`: optional format string such as `mp3_44100_128`

Expected result contract:

- `provider`: `elevenlabs-mcp`
- `gateway`: `mega-orchestrator`
- `agent_family`: resolved family
- `text_input`: sanitized text sent to TTS
- `voice_id`: effective voice id
- `model_id`: effective model id
- `output_path`: absolute path to generated audio on HAS
- `mime_type`: expected audio mime type
- `playback_hint`: short instruction for the client

The core does not autoplay. Adapters decide how to present the generated file.
