#compdef globus
_globus() {
    if type globus > /dev/null;
    then
        eval "$(env COMMANDLINE="${words[1,$CURRENT]}" globus --shell-complete ZSH)"
    fi
}
if [[ "$(basename "${(%):-%x}")" != "_globus" ]]; then
    autoload -U compinit && compinit
    compdef _globus globus
fi
