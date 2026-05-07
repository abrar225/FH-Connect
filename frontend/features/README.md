# Feature-Sliced Design (FSD)

This directory follows a Feature-Sliced Design approach to ensure modularity.

## Rules
1. **No Cross-Feature Imports:** A feature cannot import directly from another feature. (e.g., `chat` cannot import from `room`).
2. **Global State Decoupling:** Use the isolated Zustand slices in `/stores` instead of a monolithic state object.
3. **Core is the Host:** The `room` feature acts as the host environment. Other features like `chat`, `intelligence`, and `whiteboard` are plugins that hook into the host UI.

## Modules
- `room`: Core LiveKit connection, dynamic grid layout, media controls.
- `chat`: Messaging, data channel communication.
- `intelligence`: AI Pulse, task popups, transcripts.
- `whiteboard`: Canvas drawing state.
