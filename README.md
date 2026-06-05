# Pages Directory

For Fantasy11 Pro, we use a session-state-driven router inside `app.py` instead of standard Streamlit files in this directory. 

## Rationale
1. **State Preservation**: The Squad Builder and Contest entry confirm screens require heavy session-state tracking (credits left, roles selected, current user profile, match IDs). Standard Streamlit sub-pages reload their states, making multi-step forms difficult to coordinate.
2. **Branding & Auth Locks**: A single main file allows us to easily lock down the entire application behind a custom themed Login/Register interface, preventing non-authenticated page access.
