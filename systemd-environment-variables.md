# Systemd User Environment and VS Code

## Problem Summary

VS Code was picking up these environment variables even though they weren't in `.bashrc`:

```bash
ANTHROPIC_BASE_URL=https://mangpt-api.res.m/dev
ANTHROPIC_MODEL=claude-sonnet-4-5
ANTHROPIC_AUTH_TOKEN=mangpt_bb25865fe66e747d80c5870ed09fe314
```

## Root Cause

The variables were set in **systemd's user environment**, not in shell profile files.

## What is systemd?

**systemd** is the init system and service manager for modern Linux distributions. It's responsible for:

- Starting and managing system services
- Managing the boot process
- Handling system state transitions
- Managing user sessions and services

### systemd User Services

In addition to system-level services, systemd also manages **user-level services** for each logged-in user. This includes:

- User session management
- User-specific services and timers
- **User environment variables** that persist across all applications launched by the desktop environment

## How Environment Variables Work in Linux

There are several places where environment variables can be set, each with different scopes:

### 1. Shell Profile Files (Terminal Only)
- **Files**: `~/.bashrc`, `~/.bash_profile`, `~/.profile`, `~/.zshrc`
- **Scope**: Only affect terminal sessions
- **When loaded**: When you open a terminal
- **Not inherited by**: GUI applications launched from desktop environment

### 2. Systemd User Environment (Desktop Environment)
- **Command**: `systemctl --user show-environment`
- **Scope**: Affects ALL applications launched by the desktop environment
- **When loaded**: At login (when systemd user session starts)
- **Inherited by**: All GUI applications including VS Code, browsers, file managers, etc.

### 3. System-wide Environment
- **Files**: `/etc/environment`, `/etc/profile`
- **Scope**: All users and all applications
- **When loaded**: At system boot / user login

## How VS Code Uses Environment Variables

VS Code inherits its environment variables from its **parent process**, which is typically:

```
Login → systemd user session → Desktop Environment → VS Code
```

### The Inheritance Chain

1. **You log in** → systemd starts your user session
2. **systemd loads user environment** → Variables from `systemctl --user show-environment`
3. **Desktop environment starts** → Inherits systemd user environment
4. **You launch VS Code from desktop** → Inherits from desktop environment
5. **VS Code terminal** → Inherits from VS Code process

This is why:
- ✅ VS Code picks up variables from systemd user environment
- ❌ VS Code does NOT automatically pick up variables from `.bashrc`
- ✅ Terminals opened in VS Code can load `.bashrc` and add MORE variables

## The Solution

### What We Did

Removed the variables from systemd user environment:

```bash
systemctl --user unset-environment ANTHROPIC_BASE_URL
systemctl --user unset-environment ANTHROPIC_MODEL
systemctl --user unset-environment ANTHROPIC_AUTH_TOKEN
```

Or all at once:
```bash
systemctl --user unset-environment ANTHROPIC_BASE_URL ANTHROPIC_MODEL ANTHROPIC_AUTH_TOKEN
```

### Verification

Check current systemd user environment:
```bash
systemctl --user show-environment
```

### Making Changes Take Effect

After modifying systemd user environment, you need to:
- **Option 1**: Restart VS Code (and any other affected GUI applications)
- **Option 2**: Log out and log back in (restarts entire systemd user session)

## How Variables Were Set in systemd

Variables can be added to systemd user environment in several ways:

### 1. Manually (Temporary - until logout)
```bash
systemctl --user set-environment VARIABLE_NAME=value
```

### 2. Via Configuration Files (Persistent)
Variables can be set in:
- `~/.config/environment.d/*.conf`
- `/etc/systemd/user.conf.d/*.conf`
- Service files that export variables

### 3. Via Shell Scripts
Some login scripts or startup applications may call `systemctl --user set-environment`

## Best Practices

### When to Use Each Method

#### Use Shell Profile Files (`.bashrc`) When:
- ✅ You only need variables in terminal sessions
- ✅ You want different values for different shell types
- ✅ Variables are development/debugging specific

#### Use Systemd User Environment When:
- ✅ You need variables in ALL GUI applications
- ✅ Variables should persist across terminal sessions
- ✅ You're setting system-wide user preferences

#### Use System-wide Files (`/etc/environment`) When:
- ✅ Variables needed by ALL users
- ✅ System-level configuration
- ⚠️ Requires root/admin access

## Troubleshooting

### Check where a variable is set:

```bash
# Check current shell
echo $VARIABLE_NAME

# Check systemd user environment
systemctl --user show-environment | grep VARIABLE_NAME

# Check shell profile files
grep VARIABLE_NAME ~/.bashrc ~/.bash_profile ~/.profile

# Check system-wide
grep VARIABLE_NAME /etc/environment
```

### Common Issues

1. **Variable in `.bashrc` not visible in VS Code**
   - This is expected behavior
   - VS Code doesn't read `.bashrc` at startup
   - Solution: Set in systemd user environment OR configure VS Code to load shell environment

2. **Changes to systemd environment not taking effect**
   - Need to restart applications or re-login
   - systemd user environment is loaded at session start

3. **Different values in terminal vs GUI**
   - Terminal may be overriding with `.bashrc` values
   - Check both systemd environment and shell profiles

## Summary

- **systemd** manages user sessions and environment for desktop applications
- **VS Code** inherits environment from systemd user session, not from `.bashrc`
- **Shell profiles** only affect terminal sessions
- Use `systemctl --user {set,unset,show}-environment` to manage variables for GUI applications
- Restart applications or re-login after changes to systemd user environment
