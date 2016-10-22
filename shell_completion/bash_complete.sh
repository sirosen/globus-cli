_globus_completion() {
    local IFS=$'\t'
    if type globus > /dev/null;
    then
        COMPREPLY=( $( env COMP_WORDS="${COMP_WORDS[*]}" \
                       COMP_CWORD="$COMP_CWORD" \
                       globus --shell-complete BASH ) )
    else
        COMPREPLY=( )
    fi
    return 0
}

complete -F _globus_completion -o default globus;
