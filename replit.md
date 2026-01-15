# Dynamic Admin Bot

## Overview

This is a Telegram bot built with Python using the aiogram framework (version 3.x). The bot provides a dynamic admin panel system with role-based access control, allowing super admins to manage supervisors and configure interactive button menus. The interface is in Arabic, suggesting the target audience is Arabic-speaking users.

The bot features:
- Role-based user management (super_admin, admin, supervisor, user)
- Dynamic button/menu creation and management
- Supervisor management capabilities
- SQLite-based persistent storage

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Bot Framework
- **Framework**: aiogram 3.x (async Telegram Bot API wrapper)
- **Rationale**: aiogram provides robust async support, FSM (Finite State Machine) for conversation flows, and clean router-based handler organization
- **Storage**: MemoryStorage for FSM state management (conversation states stored in memory)

### Application Structure
```
├── bot.py              # Main bot initialization, dispatcher setup, core handlers
├── config.py           # Environment-based configuration management
├── database.py         # SQLite database class with table definitions
├── keyboards.py        # Reusable keyboard/button builders
├── admin_interface.py  # Admin panel handlers and callbacks
├── user_interface.py   # User-facing handlers (currently empty)
├── states.py           # FSM state definitions for multi-step flows
└── main.py             # Application entry point (currently empty)
```

### Database Schema (SQLite)
- **users**: Stores telegram_id, role (super_admin/admin/supervisor/user), is_active status
- **permissions**: Granular permission assignments linked to users
- **buttons**: Dynamic menu buttons with parent-child hierarchy, type, content, and creator tracking

### Role Hierarchy
1. **super_admin**: Full system access, set via SUPER_ADMIN_ID environment variable
2. **admin**: Administrative capabilities
3. **supervisor**: Limited management access
4. **user**: Default role for new users

### Handler Organization
- Uses aiogram's Router system for modular handler registration
- Callback queries follow naming convention: `category:action:param` (e.g., `manager:disable:123`)
- FSM states handle multi-step user inputs (e.g., adding supervisors)

## External Dependencies

### Required Environment Variables
- `BOT_TOKEN`: Telegram Bot API token (required)
- `SUPER_ADMIN_ID`: Telegram user ID for super admin (required, integer)
- `DATABASE_NAME`: SQLite database filename (optional, defaults to "bot.db")
- `BOT_NAME`: Display name for the bot (optional)
- `DEBUG`: Enable debug mode (optional, defaults to "true")

### Python Dependencies
- `aiogram` (version 3.x): Telegram Bot API framework
- `sqlite3`: Database storage (built-in Python module)

### External Services
- **Telegram Bot API**: Primary interface for user interaction
- No additional third-party APIs or services are currently integrated