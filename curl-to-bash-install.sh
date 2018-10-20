#!/bin/sh

#
# Experimental sh Installer for Globus CLI
#
#   Runs as a curl-to-bash script
#
#   Written to be compatible with POSIX shells
#   - attempt to be fully Bourne shell compatible
#   - test with "posh" shell
#
# install the Globus CLI into a virtualenv, vendoring all of its dependencies
#
#
# Goals:
#
# - detect if dependencies are absent, print a sensible error and exit
#
# - euid detection for root runs
#
# - rely on pip and virtualenv
#
# - use `python -m` invocation to avoid issues with newer pips possibly
#   having broken the system pip binary
#
# - don't be too quiet, noisy output is okay, but full virtualenv/pip output is
#   probably not
#
# - should not break `globus update`
#
# - respect existing installs and do nothing (`globus update` handles updates
#   already)
#   - print a message about using `globus update`
#
# - for non-root runs, *echo* the necessary PATH export
#   - no magical writing to profile or anything like that
#
# - for root runs
#   - check that the platform is Linux
#   - install into /usr/lib/globus-cli-virtualenv
#   - put generated binary link into /usr/bin
#   - message if `/usr/lib/` is missing
#
# TODO:
# - support macOS root installs -- do we need to do anything additional, or is
#   installing into /usr/lib/ safe?


# default vars...
INSTALL_LIB="$HOME/.globus-cli-virtualenv"
INSTALL_BIN="$INSTALL_LIB/bin/globus"
IS_ROOT=0
FAILED_DEPS=""
DOING_UNINSTALL=0


print_usage () {
  echo "The Globus CLI sh-Installer Supports the following arguments " >&2
  echo "and options:" >&2
  echo >&2
  echo " --uninstall : Uninstall the Globus CLI instead of installing it" >&2
  echo >&2
}

parse_arguments () {
  while [ $# -gt 0 ]; do
    arg="$1"
    shift
    case "$arg" in
      "--uninstall")
        DOING_UNINSTALL=1
        ;;
      *)
        echo "unknown argument $arg !" >&2
        print_usage
        exit 2
        ;;
    esac
  done
}

print_header () {
  #
  # say hello
  #

  echo "****************************************"
  echo "*                                      *"
  echo "*     Globus CLI sh-Installer          *"
  echo "*                                      *"
  echo "* version     0.1-ALPHA                *"
  echo "*                                      *"
  echo "* author      sirosen                  *"
  echo "* copyright   2018                     *"
  echo "*   Globus, University of Chicago      *"
  echo "* license     Apache 2.0               *"
  echo "*                                      *"
  echo "* Beware of attack cat.                *"
  echo "* Caveat \$USER                         *"
  echo "*                                      *"
  echo "****************************************"
  echo
  echo "You are running an experimental installer, and it may not work!"
  echo "Relying on this is probably a bad idea right now."
  echo
}

check_dependencies () {
  #
  # check dependencies
  #

  for dep in python pip virtualenv; do
    if ! which "$dep" > /dev/null; then
      FAILED_DEPS="$FAILED_DEPS $dep"
    fi
  done
  echo "=== Preflight Check: Dependencies"
  if [ "$FAILED_DEPS" != "" ]; then
      echo "Check Failed!"
      echo
      echo "The following required dependencies are missing."
      echo "You need to install them before you can run this installer."
      echo
      echo "Failed Dependencies:$FAILED_DEPS"
      echo
      exit 1
  else
      echo "Check OK, all dependencies found"
  fi
}

check_user () {
  #
  # check user
  #
  echo "=== Preflight Check: User"
  if [ "`id -u`" = "0" ]; then
    IS_ROOT=1
    echo "root user detected"

    platform_name=`uname -s`
    if [ "$platform_name" != "Linux" ]; then
        echo "CHECK FAILED: root user on non-linux platforms is not supported"
        echo "detected: '$platform_name'"
        echo "wanted:   'Linux'"
        exit 1
    fi

    echo "Will now attempt to install the Globus CLI Globally"
    echo "into /usr/lib/globus-cli-virtualenv/"
    echo

    INSTALL_LIB="/usr/lib/globus-cli-virtualenv"
    INSTALL_BIN="/usr/bin/globus"
  else
    echo "non-root user detected"
    echo "Will install into ~/.globus-cli-virtualenv/"
    echo
  fi
}

check_installed () {
  #
  # Check if already installed
  #

  echo "=== Preflight Check: Already Installed"
  if [ -d "$INSTALL_LIB" ]; then
    if [ $DOING_UNINSTALL -eq 0 ]; then
      echo "CHECK FAILED: found CLI already installed"
      echo
      echo "To reinstall, you must uninstall first."
      echo
      echo
      echo "To update your CLI version, use the 'globus update' command"
      echo
      echo "This will require the same permissions which were needed to do the "
      echo "original installation."
      echo
      exit 1
    else
      echo "Check OK, installed and running with --uninstall"
    fi
  else
    if [ $DOING_UNINSTALL -eq 0 ]; then
      echo "Check OK, not already installed"
    else
      echo "CHECK FAILED: CLI not installed and running with --uninstall"
      exit 1
    fi
  fi
}


do_install () {
  # setup vars which are now safe
  VIRTUALENV_CMD="python -m virtualenv --no-site-packages -q"
  PIP_INSTALL_CMD="$INSTALL_LIB/bin/python -m pip -qq install --ignore-installed"

  #
  # Create virtualenv
  #
  echo "setting up virtualenv..."
  $VIRTUALENV_CMD "$INSTALL_LIB"
  rc=$?
  if [ $rc -ne 0 ]; then
    echo
    echo "virtualenv setup failed!"
    echo
    exit $rc
  fi
  echo "virtualenv setup successful!"


  #
  # Install CLI package
  #
  echo "running pip install..."
  $PIP_INSTALL_CMD globus-cli
  rc=$?
  if [ $rc -ne 0 ]; then
    echo
    echo "pip install failed!"
    echo
    exit $rc
  fi
  echo
  echo "pip install successful!"
  echo

  #
  # if root, create BIN symlink
  #
  if [ $IS_ROOT -ne 0 ]; then
    TRUE_BIN_LOC="$INSTALL_LIB/bin/globus"
    echo "linking $INSTALL_BIN to $TRUE_BIN_LOC"
    ln -s "$TRUE_BIN_LOC" "$INSTALL_BIN"
    rc=$?
    if [ $rc -ne 0 ]; then exit $rc; fi
    echo
  fi
}


print_post_install () {
  #
  # print PATH modification if non-root
  #
  if [ $IS_ROOT -eq 0 ]; then
    echo
    echo "=== Recommended Shell Setup"
    echo
    echo "Run the following commands or equivalent for your shell:"
    echo
    echo '  $ export PATH="$PATH:$HOME/.globus-cli-virtualenv/bin"'
    echo "  $ echo 'export PATH="\$PATH:\$HOME/.globus-cli-virtualenv/bin"' >> \"\$HOME/.bashrc\""
    echo
    echo "=== Setup Completion (optional)"
    echo
    echo "Run this to setup completion:"
    echo
    echo '  $ eval "`globus --completer`"'
    echo "  $ echo 'eval \"\`globus --completer\`\"' >> \"\$HOME/.bashrc\""
    echo
  fi


  echo
  echo "Congratulations! You've now installed the Globus CLI!"
  echo
  echo
}


do_uninstall () {
  echo "Removing virtualenv..."
  rm -r "$INSTALL_LIB"
  echo "virtualenv removed"

  if [ $IS_ROOT -ne 0 ]; then
    echo "removing binary link from /usr/bin/globus ..."
    rm "/usr/bin/globus"
    echo "binary link removed"
  fi
}


print_post_uninstall () {
  echo
  echo "You have now removed the Globus CLI."
  echo

  #
  # print removal of PATH modification if non-root
  #
  if [ $IS_ROOT -eq 0 ]; then
    echo "You may have made changes to your PATH variable when you installed "
    echo "the Globus CLI."
    echo
    echo "You should check your '\$HOME/.bashrc' and shell profile files"
    echo "for any lines which add"
    echo "   \$HOME/.globus-cli-virtualenv/bin'"
    echo "to the PATH variable and remove those lines."
    echo
  fi
}



# wrap all execution in a function so that disconnects don't result in partial
# execution during `curl ... | bash`
main () {
  parse_arguments "$@"
  print_header

  check_dependencies
  check_user
  check_installed

  if [ $DOING_UNINSTALL -eq 0 ]; then
    echo
    echo "* Preflight Checks Over, Starting Install"
    echo

    do_install
    print_post_install
  else
    echo
    echo "* Preflight Checks Over, Starting Uninstall"
    echo
    do_uninstall
    print_post_uninstall
  fi

}

main "$@"
