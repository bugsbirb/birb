# 🐦 Birb - Discord Staff Management Bot

Imagine a bot...

Where staff management is a **breeze**.

With Birb, you can effortlessly manage your Discord staff team, track their activities, and ensure smooth communication. Say goodbye to manual processes and hello to automation, with Birb!

Join our server to get support and be amongst the first people to see new updates!

[![Birb Support Server](https://discord.com/api/guilds/1092976553752789054/embed.png?style=banner2)](https://discord.gg/MaPX4zUQuk)

Visit our [website](https://www.astrobirb.dev/) to invite the bot to your server!

## ✨ Features

### 📋 Staff Management

- **Staff Database** - Complete staff member tracking with roles and timezones
- **Message Quota System** - Automated activity tracking and reporting
- **Leave of Absence (LOA)** - Comprehensive leave management with automatic expiration
- **Staff Punishments & Infractions** - Disciplinary action tracking with escalation
- **Promotion System** - Hierarchical role management
- **Staff Feedback** - Anonymous and identified feedback collection
- **Suspensions** - Temporary staff suspension management

### 🎫 Communication Tools

- **Ticket System** - Customizable support ticket management
- **Modmail** - Direct messaging system between users and staff
- **Forums** - Automated forum post management with button controls
- **Auto Response** - Intelligent automatic message responses

### 🔧 Administrative Features

- **Custom Commands** - Server-specific command creation
- **Connection Roles** - Role assignment based on external connections
- **Daily Questions** - Automated engagement prompts
- **Suggestions** - Community suggestion system with voting
- **Staff Panel** - Centralized management interface

### 🔗 Integrations

- **Roblox Groups** - Integration with Roblox group management
- **ERM (External Role Management)** - Third-party role synchronization
- **Patreon** - Premium subscription management
- **Custom Branding** - Personalized bot deployment options

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- A MongoDB database
- A Discord bot with a token
- Basic knowledge of Python and Discord API

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/bugsbirb/birb.git
   cd birb
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**

   ```bash
   cp .env.template .env
   # Edit .env with your configuration
   ```

4. **Run the bot**

   ```bash
   python main.py
   ```

### Docker Deployment

```bash
docker build -t birb .
docker run -d --env-file .env birb
```

## ⚙️ Configuration

Copy `.env.template` to `.env`. Make sure you don't miss any important values.

## 🎮 Commands

### Staff Commands

> Available to users listed in the `STAFF` environment variable:

- `!!guilds` - List all connected guilds
- `!!leave <guild_id>` - Leave a specific guild
- `!!whitelist <guild_id>` - Add guild to whitelist
- `!!unwhitelist <guild_id>` - Remove guild from whitelist
- `!!sync` - Sync slash commands (Owner only)

### Slash Commands

- `/config` - Access bot configuration panel
- `/staff` - Staff management commands
- `/ticket` - Ticket system commands
- `/feedback` - Staff feedback system
- `/suggestions` - Suggestion management

## 🔧 Development

### Adding New Features

1. Create a new cog in the appropriate directory:
   - `Cogs/Modules/` - Core bot functionality
   - `Cogs/Events/` - Event handlers
   - `Cogs/Tasks/` - Background tasks

2. Follow the existing code structure and patterns
3. Add proper error handling and logging
4. Update documentation as needed

### Code Quality

The project uses:

- **DeepSource** for code analysis (see [.deepsource.toml](.deepsource.toml))
- **Type hints** for better code documentation
- **Error handling** with specific exception types

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

Please ensure your code follows the existing patterns and includes appropriate error handling.

## 📄 License

Birb is licensed under the [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License](LICENSE).

### License Summary

- **BY (Attribution)** - Credit must be given to the original creator
- **NC (NonCommercial)** - Only non-commercial use is permitted
- **SA (ShareAlike)** - Adaptations must be licensed under the same terms

For commercial use or licensing inquiries, please contact the project maintainers.
