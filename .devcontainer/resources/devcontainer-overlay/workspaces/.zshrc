# NetAlertX devcontainer zsh configuration
# Keep this lightweight and deterministic so shells behave consistently.

export PATH="$HOME/.local/bin:$PATH"
export EDITOR=vim
export SHELL=/bin/zsh

# Start inside the workspace if it exists
if [ -d "/workspaces/NetAlertX" ]; then
  cd /workspaces/NetAlertX
fi

# Enable basic completion and prompt helpers
autoload -Uz compinit promptinit colors
colors
compinit -u
promptinit

# Friendly prompt with virtualenv awareness
setopt PROMPT_SUBST

_venv_segment() {
  if [ -n "$VIRTUAL_ENV" ]; then
    printf '(%s) ' "${VIRTUAL_ENV:t}"
  fi
}

PROMPT='%F{green}$(_venv_segment)%f%F{cyan}%n@%m%f %F{yellow}%~%f %# '
RPROMPT='%F{magenta}$(git rev-parse --abbrev-ref HEAD 2>/dev/null)%f'

# Sensible defaults
setopt autocd
setopt correct
setopt extendedglob
HISTFILE="$HOME/.zsh_history"
HISTSIZE=5000
SAVEHIST=5000

alias ll='ls -alF'
alias la='ls -A'
alias gs='git status -sb'
alias gp='git pull --ff-only'

# Ensure pyenv/virtualenv activate hooks adjust the prompt cleanly
if [ -f "$HOME/.zshrc.local" ]; then
  source "$HOME/.zshrc.local"
fi
